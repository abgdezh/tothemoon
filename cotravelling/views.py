from django.shortcuts import get_object_or_404, render
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse

from .models import *

from django.contrib.auth.decorators import login_required

from django.contrib.auth import logout as django_logout

from django.db import transaction

from datetime import datetime, timedelta, date, time

from django.utils import timezone

from django_user_agents.utils import get_user_agent

import locale

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
    
def findtrip(request):
    if request.POST:
        if 'target' in request.POST:
            return add_trip(request)
        elif request.user.is_authenticated and str(request.POST).find("join") != -1:
            return join_trip(request)
        elif request.user.is_authenticated and str(request.POST).find("leave") != -1:
            return leave_trip(request)
    
    if request.GET and 'from' in request.GET:
        date_from = datetime.strptime(request.GET['from'], '%Y-%m-%d')
    else:
        date_from = date.today()
    date_from = timezone.make_aware(datetime.combine(date_from, time()))
    
    user_agent = get_user_agent(request)
    if user_agent.is_mobile:
        days = 7
    else:
        days = 3

    trips = [Trip.objects.filter(datetime__gte=date_from + timedelta(i), 
                                 datetime__lt=date_from + timedelta(i + 1)).order_by('datetime', 'id') 
                                 for i in range(days)]

    context = {'trips': 
               [{'trips' : [], 
                 'date' : datetime.strftime(date_from + timedelta(i), "%a. %d.%m.")}
                 for i in range(days)],
                'auth': request.user.is_authenticated,
                'link_prev_date': datetime.strftime(date_from - timedelta(days), '%Y-%m-%d'),
                'link_next_date': datetime.strftime(date_from + timedelta(days), '%Y-%m-%d'),
              }
    for i in range(days):
        for trip in trips[i]:
            joining = False
            is_owner = False
            if request.user.is_authenticated:
                joining = len(UserTrip.objects.filter(user=request.user, trip=trip)) == 1
                if joining:
                    user_trip = UserTrip.objects.get(user=request.user, trip=trip)
                    is_owner = user_trip.is_owner
            context['trips'][i]['trips'].append({'trip_info' : trip,
                                                 'users' : [user_trip.user.first_name + " " + user_trip.user.last_name for user_trip in UserTrip.objects.filter(trip=trip.id)],
                                                 'joining' : joining,
                                                 'is_owner' : is_owner
                                                })
    return render(request, 'cotravelling/findtrip.html', context)
    
def add_trip(request):
    try:
        with transaction.atomic():
            trip = Trip()
            trip.source = request.POST['source']
            trip.target = request.POST['target']
            trip.vehicle = request.POST['vehicle']
            trip.datetime = datetime.strptime(request.POST['datetime'], '%d.%m.%Y %H:%M')
            trip.free_places = request.POST['free_places']
            trip.save()
            user_trip = UserTrip(user=request.user, trip=trip, is_owner=True)
            user_trip.save()
    except Exception as e:
        print(e)
    return HttpResponseRedirect(request.get_full_path())
    
def join_trip(request):
    trip_id = [int(s.replace("join", "")) for s in request.POST if s.startswith("join")][0]
    try:
        with transaction.atomic():
            trip = Trip.objects.get(id=trip_id)
            if trip.free_places > 0:
                trip.free_places -=1
                user_trip = UserTrip(user=request.user, trip=trip, is_owner=False)
                trip.save()
                user_trip.save()
            
    except Exception as e:
        pass
    return HttpResponseRedirect(request.get_full_path())
    
def leave_trip(request):
    trip_id = [int(s.replace("leave", "")) for s in request.POST if s.startswith("leave")][0]
    try:
        with transaction.atomic():
            trip = Trip.objects.get(id=trip_id)
            user_trip = UserTrip.objects.get(user=request.user, trip=trip)
            trip.free_places += 1
            trip.save()
            user_trip.delete()
    except Exception as e:
        pass
    return HttpResponseRedirect(request.get_full_path())
    
def logout(request):
    django_logout(request)
    print(request)
    return HttpResponseRedirect(reverse('cotravelling:findtrip'))

@login_required(login_url='/')
def chat(request, **kwargs):
    if request.POST:
        return(add_message(request, **kwargs))
    context = {"messages" : []}
    if UserTrip.objects.filter(trip__id=kwargs['chat_id'], user=request.user):
        context["messages"] = Message.objects.filter(trip__id=kwargs['chat_id']).order_by('datetime')
    else:
        context["forbidden"] = True
    try:
        context["trip_info"] = Trip.objects.get(id=kwargs['chat_id'])
        remaining_time = context["trip_info"].datetime - timezone.make_aware(datetime.now())
        context["trip_info"].remaining_time = format_timedelta(remaining_time)
        context["trip_info"].is_over = remaining_time > timedelta(0)
        context["participants"] = UserTrip.objects.filter(trip__id=kwargs['chat_id'])
    except Trip.DoesNotExist:
        raise Http404("Trip does not exist")
    return render(request, 'cotravelling/tripchat.html', context)
    
def add_message(request, **kwargs):
    message_text = request.POST["text"]
    trip_id = kwargs['chat_id']
    try:
        with transaction.atomic():
            message = Message()
            message.author = request.user
            message.trip = Trip.objects.get(id=trip_id)
            message.text = message_text
            message.save()
            
    except Exception as e:
        print(e)
    return HttpResponseRedirect(reverse('cotravelling:chat', kwargs=kwargs))
    
def about(request):
    return render(request, 'cotravelling/about.html', {})
