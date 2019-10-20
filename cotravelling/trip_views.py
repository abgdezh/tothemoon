from django.template.loader import render_to_string
from django.shortcuts import render
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse

from .models import *

from django.contrib.auth.decorators import login_required

from django.db import transaction

from datetime import datetime, timedelta, date, time

from django.utils import timezone

from django_user_agents.utils import get_user_agent

import traceback
import locale
import sys

from cotravelling.utils import user_id_to_vk_id
from cotravelling.vk import allowed
from cotravelling.tasks import send_trip_notifications, send_user_join_notification

locale.setlocale(locale.LC_TIME, locale.getlocale())

SUPERMARKETS = ['IKEA', 'Metro', 'Рио', 'Ашан Алтуфьево', 'Лента']

def format_timedelta(td):
  items = []
  if td.days >= 5:
    day_str = str(td.days) + " дней"
  elif td.days >= 2:
    day_str = str(td.days) + " дня"
  elif td.days == 1:
    day_str = str(td.days) + " день"
  else:
    day_str = ""
  hours = td.seconds // 3600
  minutes = (td.seconds - hours * 3600) // 60
  if hours in [1, 21]:
    hour_str = str(hours) + " час"
  elif hours in [2, 3, 4, 22, 23, 24]:
    hour_str = str(hours) + " часа"
  elif hours > 0:
    hour_str = str(hours) + " часов"
  else:
    hour_str = ""
  if minutes in [1, 21]:
    minutes_str = str(minutes) + " минуту"
  elif minutes in [2, 3, 4, 22, 23, 24]:
    minutes_str = str(minutes) + " минуты"
  else:
    minutes_str = str(minutes) + " минут"
  return "через " + ", ".join([i for i in [day_str, hour_str, minutes_str] if i != ""])


def build_trip(date, user=None):
    trips = Trip.objects.filter(datetime__gte=date, datetime__lt=date + timedelta(1)).order_by('datetime', 'id')
    for trip in trips:
        trip.joining = False
        trip.is_owner = False
        trip.admitted = False
        if type(user) is int:
            trip.joining = len(UserTrip.objects.filter(user_id=user, trip=trip)) == 1
            if trip.joining:
                user_trip = UserTrip.objects.get(user_id=user, trip=trip)
                trip.is_owner = user_trip.is_owner
                trip.admitted = user_trip.admitted
        elif user and user.is_authenticated:
            trip.joining = len(UserTrip.objects.filter(user=user, trip=trip)) == 1
            if trip.joining:
                user_trip = UserTrip.objects.get(user=user, trip=trip)
                trip.is_owner = user_trip.is_owner
                trip.admitted = user_trip.admitted
        trip.users = [user_trip.user.first_name + " " + user_trip.user.last_name for user_trip in UserTrip.objects.filter(trip=trip.id, admitted=True)]
        trip.deletable = len(UserTrip.objects.filter(trip=trip.id)) == 1 and trip.is_owner
    return trips


def build_context(date_from, days, user):
    trips = [build_trip(date_from + timedelta(i), user) for i in range(days)]
    context = {'trips': 
               [{'trips' : trips[i], 
                 'date' : datetime.strftime(date_from + timedelta(i), "%A, %-d %B"),
                 'short_date' : datetime.strftime(date_from + timedelta(i), "%-d %B"),
                 'iteration' : i,
                }
                 for i in range(days)],
                'date_from' : datetime.strftime(date_from, "%Y-%m-%d"),
                'auth' : type(user) is int or (user and user.is_authenticated),
                'locations' : Location.objects.all()
              }
    return context


def handle_post_request(request):
    if 'target' in request.POST:
        return add_trip(request)
    elif request.user and request.user.is_authenticated and str(request.POST).find("join") != -1:
        return join_trip(request)
    elif request.user and request.user.is_authenticated and str(request.POST).find("leave") != -1:
        return leave_trip(request)
    elif request.user and request.user.is_authenticated and str(request.POST).find("ask") != -1:
        return ask_trip(request)
#    elif request.user and request.user.is_authenticated and str(request.POST).find("accept") != -1:
#        return accept(request)
    return HttpResponseRedirect(reverse('cotravelling:findtrip'))


def findtrip(request, **kwargs):
    period = request.GET.get('schedule_trip', None)
    status = request.GET.get('status', 'in_process')
    added_trip = request.GET.get('added_trip', False)

    if status == 'accept':
        add_scheduled_user(period, request.user)
    elif status == 'cancel':
        remove_scheduled_user(request.user)
        period = None

    if request.POST:
        return handle_post_request(request)
    if 'date_from' in kwargs:
        date_from = datetime.strptime(kwargs['date_from'], '%Y-%m-%d')
    else:
        date_from = date.today()
    date_from = timezone.make_aware(datetime.combine(date_from, time()))
    
    days = 3

    is_notify_allowed = False
    if request.user.is_authenticated:
        vk_id = user_id_to_vk_id(request.user)    
        if vk_id:
            is_notify_allowed = allowed(vk_id)
        else:
            print("Could not find vk_id for user {}".format(request.user))
    context = build_context(date_from, days, request.user)
    context["user"] = request.user
    context["period"] = period
    context["is_notify_allowed"] = is_notify_allowed
    context["added_trip"] = added_trip
    return render(request, 'cotravelling/available_trips.html', context)
    
def add_scheduled_user(period, user_auth):
    start_date, end_date = get_schedule_period(period)
    print("User will get notifications from {} to {}".format(start_date, end_date))
    
    user_plan = UserPlan(user=user_auth, date_start=timezone.make_aware(start_date), date_end=timezone.make_aware(end_date))
    user_plan.save()
    
def get_schedule_period(period):
    if period == 'week':
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
    elif period == "weekend":
        current_dt = datetime.now()
        if current_dt.weekday() == 5 or current_dt.weekday() == 6:
            start_date = current_dt
            if current_dt.weekday() == 5:
                end_date = datetime.combine((start_date + timedelta(days=1)), time.max)
            else:
                end_date = datetime.combine(start_date, time.max)
        else:
            delta_sat = timedelta(days=(12 - current_dt.weekday()) % 7)
            start_date = datetime.combine((current_dt + delta_sat), time.min)
            end_date = datetime.combine((start_date + timedelta(days=1)), time.max)
    
    return start_date, end_date

def remove_scheduled_user(user):
    UserPlan.objects.filter(user=user).delete()

def load_trips(request, **kwargs):
    if request.POST:
        return handle_post_request(request)
    date_from = datetime.strptime(kwargs['datetime'], '%Y-%m-%d')
    date_from = timezone.make_aware(datetime.combine(date_from, time()))
    user = kwargs.get("user")
    diff = kwargs.get("diff") if kwargs.get("direction") == "f" else -kwargs.get("diff")
    context = build_context(date_from + timedelta(diff), 3, user)
    return JsonResponse({"page" : render_to_string('cotravelling/trips_block.html', context, request=request),
                         "date_from" : datetime.strftime(date_from + timedelta(diff), '%Y-%m-%d')
                         })


def add_trip(request):
    date = ''
    try:
        with transaction.atomic():
            trip = Trip()
            trip.source = request.POST['source']
            trip.target = request.POST['target']
            trip.vehicle = request.POST['vehicle']
            trip.datetime = timezone.make_aware(datetime.strptime(request.POST['datetime'], '%d.%m.%Y %H:%M'))
            trip.free_places = request.POST['free_places']
            trip.is_closed = 'is_closed' in request.POST
            trip.save()
            date = request.POST['date_from']
            user_trip = UserTrip(user=request.user, trip=trip, is_owner=True, admitted=True)
            user_trip.save()
        
        users = find_schedule_users(request.POST['target'], trip.datetime)
        users = [user['user'] for user in users]
        print(trip)
        trip_data = {
            'source': trip.source,
            'target': trip.target,
            'datetime': trip.datetime
        }
        if users:
            send_trip_notifications.delay(users, trip_data)

        is_notify_allowed = False
        if request.user.is_authenticated:
            vk_id = user_id_to_vk_id(request.user)    
        if vk_id:
            is_notify_allowed = allowed(vk_id)
    except Exception as e:
        print(traceback.print_tb(sys.exc_info()[2]))
    return HttpResponseRedirect('/findtrip/' + date + '?added_trip=true&notify_allowed=' + str(is_notify_allowed))

def find_schedule_users(target, trip_date):
    if target not in SUPERMARKETS:
        return []
    
    user_ids = UserPlan.objects.values('user').filter(date_start__lte=trip_date, date_end__gte=trip_date).distinct()
    return user_ids
    
    
def parse_request(request):
    query = [s.split() for s in request.POST if s != "csrfmiddlewaretoken"][0]
    return {
              "query_type": query[0],
              "trip_id": int(query[1]), 
              "date_from": query[2],
           }


def join_trip(request):
    date = ''
    try:
        query = parse_request(request)
        trip_id = query["trip_id"]
        date = query["date_from"]
        trip_participants_id = UserTrip.objects.values('user_id').filter(id=trip_id)
        user_ids = [part_id['user_id'] for part_id in trip_participants_id]
        with transaction.atomic():
            trip = Trip.objects.get(id=trip_id)
            if trip.free_places > 0 and not trip.is_closed:
                trip.free_places -= 1
                user_trip = UserTrip(user=request.user, trip=trip, is_owner=False, admitted=True)
                trip.save()
                user_trip.save()
        
        print(user_ids)
        trip_data = {
            'source': trip.source,
            'target': trip.target,
            'datetime': trip.datetime
        }
        send_user_join_notification.delay(user_ids, trip_data, str(request.user))
    except Exception as e:
        print(traceback.print_tb(sys.exc_info()[2]))
    return HttpResponseRedirect('/findtrip/' + date)
    
    
def accept(request, **kwargs):
    try:
        with transaction.atomic():
            user_trip_id = kwargs['usertrip']
            user_trip = UserTrip.objects.get(id=user_trip_id)
            trip = Trip.objects.get(id=user_trip.trip_id)
            actor_user_trip = UserTrip.objects.get(user_id=request.user.id, trip=trip)
            if trip.free_places > 0 and actor_user_trip.admitted and not user_trip.admitted:
                trip.free_places -= 1
                user_trip.admitted = True
                trip.save()
                user_trip.save()
        return HttpResponseRedirect('/chat/' + str(trip.id))
    except Exception as e:
        print(traceback.print_tb(sys.exc_info()[2]))
        return HttpResponseRedirect(reverse('cotravelling:findtrip'))
        

def reject(request, **kwargs):
    try:
        with transaction.atomic():
            user_trip_id = kwargs['usertrip']
            user_trip = UserTrip.objects.get(id=user_trip_id)
            trip = Trip.objects.get(id=user_trip.trip_id)
            actor_user_trip = UserTrip.objects.get(user_id=request.user.id, trip=trip)
            if actor_user_trip.admitted:
                if user_trip.admitted:
                    trip.free_places += 1
                    trip.save()
                user_trip.delete()
        return HttpResponseRedirect('/chat/' + str(trip.id))
    except Exception as e:
        print(traceback.print_tb(sys.exc_info()[2]))
        return HttpResponseRedirect(reverse('cotravelling:findtrip'))


def leave_trip(request):
    date = ''
    try:
        query = parse_request(request)
        trip_id = query["trip_id"]
        date = query["date_from"]
        with transaction.atomic():
            trip = Trip.objects.get(id=trip_id)
            user_trip = UserTrip.objects.get(user=request.user, trip=trip)
            joining_count = len(UserTrip.objects.filter(trip=trip))
            if user_trip.admitted and not user_trip.is_owner:
                trip.free_places += 1
                trip.save()
                user_trip.delete()
            elif not user_trip.admitted:
                user_trip.delete()
            elif user_trip.is_owner and joining_count == 1:
                user_trip.delete()
                trip.delete()
            
    except Exception as e:
        print(traceback.print_tb(sys.exc_info()[2]))
    return HttpResponseRedirect('/findtrip/' + date)


def ask_trip(request):
    date = ''
    try:
        query = parse_request(request)
        trip_id = query["trip_id"]
        date = query["date_from"]
        with transaction.atomic():
            trip = Trip.objects.get(id=trip_id)
            if trip.free_places > 0:
                user_trip = UserTrip(user=request.user, trip=trip, is_owner=False, admitted=False)
                trip.save()
                user_trip.save()
            
    except Exception as e:
        print(traceback.print_tb(sys.exc_info()[2]))
    return HttpResponseRedirect('/findtrip/' + date)


def load_messages(request, **kwargs):
    last_message_id = kwargs['last_message_id']
    trip_id = kwargs['trip_id']
    context = {"messages" : []}
    context["messages"] = Message.objects.filter(trip__id=trip_id, id__gt=last_message_id).order_by('datetime')
    if context["messages"]:
        new_last_message_id = context["messages"][len(context["messages"]) - 1].id
    else:
        new_last_message_id = last_message_id
    return JsonResponse({"page" : render_to_string('cotravelling/message.html', context, request=request),
                         "last_message_id" : last_message_id,
                         "new_last_message_id" : new_last_message_id
                         })


@login_required(login_url='/')
def chat(request, **kwargs):
    context = {"messages" : [], "footer_off" : True}
    if UserTrip.objects.filter(trip__id=kwargs['chat_id'], user=request.user, admitted=True):
        context["messages"] = Message.objects.filter(trip__id=kwargs['chat_id']).order_by('datetime')
    else:
        context["forbidden"] = True
    try:
        context["trip_info"] = Trip.objects.get(id=kwargs['chat_id'])
        remaining_time = context["trip_info"].datetime - timezone.make_aware(datetime.now())
        context["trip_info"].remaining_time = format_timedelta(remaining_time)
        context["trip_info"].is_over = remaining_time > timedelta(0)
        context["participants"] = UserTrip.objects.filter(trip__id=kwargs['chat_id'], admitted=True)
        context["requested_participants"] = UserTrip.objects.filter(trip__id=kwargs['chat_id'], admitted=False)
        if context["messages"]:
            context["last_message_id"] = context["messages"][len(context["messages"]) - 1].id
        else:
            context["last_message_id"] = 0
    except Trip.DoesNotExist:
        raise Http404("Trip does not exist")
    return render(request, 'cotravelling/tripchat.html', context)

 
def add_message(request, **kwargs):
    try:
        message_text = request.POST["content"]
        if not message_text:
            return JsonResponse({})
        trip_id = kwargs['chat_id']
        with transaction.atomic():
            message = Message()
            message.author = request.user
            message.trip = Trip.objects.get(id=trip_id)
            message.text = message_text
            message.save()
            
    except Exception as e:
        print(traceback.print_tb(sys.exc_info()[2]))
    return JsonResponse({})