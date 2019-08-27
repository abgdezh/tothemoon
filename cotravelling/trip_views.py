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

locale.setlocale(locale.LC_TIME, locale.getlocale())

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
    return trips


def build_context(date_from, days, user):
    trips = [build_trip(date_from + timedelta(i), user) for i in range(days)]
    context = {'trips': 
               [{'trips' : trips[i], 
                 'date' : datetime.strftime(date_from + timedelta(i), "%A, %-d %B"),
                }
                 for i in range(days)],
                'until_date' : datetime.strftime(date_from + timedelta(days), "%Y-%m-%d"),
                'auth' : type(user) is int or (user and user.is_authenticated)
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


def findtrip(request):
    if request.POST:
        return handle_post_request(request)
    date_from = date.today()
    date_from = timezone.make_aware(datetime.combine(date_from, time()))
    
    user_agent = get_user_agent(request)
    if user_agent.is_mobile:
        days = 1
    else:
        days = 1

    context = build_context(date_from, days, request.user)
    context["user"] = request.user
    return render(request, 'cotravelling/findtrip.html', context)
    

def load_trips(request, **kwargs):
    if request.POST:
        return handle_post_request(request)
    date_from = datetime.strptime(kwargs['datetime'], '%Y-%m-%d')
    date_from = timezone.make_aware(datetime.combine(date_from, time()))
    user = kwargs.get("user")
    days = 7
    context = build_context(date_from, days, user)
    print("context")
    return JsonResponse({"page" : render_to_string('cotravelling/trip.html', context, request=request),
                         "date" : kwargs['datetime'],
                         "new_date" : datetime.strftime(date_from + timedelta(days), '%Y-%m-%d')
                         })


def add_trip(request):
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
            user_trip = UserTrip(user=request.user, trip=trip, is_owner=True, admitted=True)
            user_trip.save()
    except Exception as e:
        print(e)
    return HttpResponseRedirect(reverse('cotravelling:findtrip'))
    

def join_trip(request):
    try:
        trip_id = [int(s.replace("join", "")) for s in request.POST if s.startswith("join")][0]
        with transaction.atomic():
            trip = Trip.objects.get(id=trip_id)
            if trip.free_places > 0 and not trip.is_closed:
                trip.free_places -=1
                user_trip = UserTrip(user=request.user, trip=trip, is_owner=False, admitted=True)
                trip.save()
                user_trip.save()
            
    except Exception as e:
        pass
    return HttpResponseRedirect(reverse('cotravelling:findtrip'))
    
    
def accept(request, **kwargs):
    try:
        with transaction.atomic():
            user_trip_id = kwargs['usertrip']
            user_trip = UserTrip.objects.get(id=user_trip_id)
            trip = Trip.objects.get(id=user_trip.trip_id)
            actor_user_trip = UserTrip.objects.get(user_id=request.user.id, trip=trip)
            if trip.free_places > 0 and actor_user_trip.admitted:
                trip.free_places -= 1
                user_trip.admitted = True
                trip.save()
                user_trip.save()
        return HttpResponseRedirect('/chat/' + str(trip.id))
    except Exception as e:
        print(e)
        return HttpResponseRedirect(reverse('cotravelling:findtrip'))
        

def reject(request, **kwargs):
    try:
        with transaction.atomic():
            user_trip_id = kwargs['usertrip']
            user_trip = UserTrip.objects.get(id=user_trip_id)
            trip = Trip.objects.get(id=user_trip.trip_id)
            actor_user_trip = UserTrip.objects.get(user_id=request.user.id, trip=trip)
            if actor_user_trip.admitted:
                trip.free_places += 1
                trip.save()
                user_trip.delete()
        return HttpResponseRedirect('/chat/' + str(trip.id))
    except Exception as e:
        print(e)
        return HttpResponseRedirect(reverse('cotravelling:findtrip'))


def leave_trip(request):
    try:
        trip_id = [int(s.replace("leave", "")) for s in request.POST if s.startswith("leave")][0]
        with transaction.atomic():
            trip = Trip.objects.get(id=trip_id)
            user_trip = UserTrip.objects.get(user=request.user, trip=trip)
            trip.free_places += 1
            trip.save()
            user_trip.delete()
    except Exception as e:
        pass
    return HttpResponseRedirect(reverse('cotravelling:findtrip'))


def ask_trip(request):
    try:
        trip_id = [int(s.replace("ask", "")) for s in request.POST if s.startswith("ask")][0]
        with transaction.atomic():
            trip = Trip.objects.get(id=trip_id)
            if trip.free_places > 0:
                user_trip = UserTrip(user=request.user, trip=trip, is_owner=False, admitted=False)
                trip.save()
                user_trip.save()
            
    except Exception as e:
        pass
    return HttpResponseRedirect(reverse('cotravelling:findtrip'))


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
    context = {"messages" : []}
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
        print(e)
    return JsonResponse({})

