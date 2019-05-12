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

import locale

locale.setlocale(locale.LC_TIME, locale.getlocale())

def index(request):
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

    trips = [Trip.objects.filter(datetime__gte=date_from + timedelta(i), 
                                 datetime__lt=date_from + timedelta(i + 1)).order_by('datetime', 'id') 
                                 for i in range(3)]

    username = None
    if request.user.is_authenticated:
        username = request.user.first_name + " " + request.user.last_name + " " + request.user.username

    context = {'trips': 
               [{'trips' : [], 
                 'date' : datetime.strftime(date_from + timedelta(i), "%a. %d.%m.")}
                 for i in range(3)],
                'auth': username,
                'link_prev_date': datetime.strftime(date_from - timedelta(3), '%Y-%m-%d'),
                'link_next_date': datetime.strftime(date_from + timedelta(3), '%Y-%m-%d'),
              }
    for i in range(3):
        for trip in trips[i]:
            joining = False
            if request.user.is_authenticated:
                joining = len(UserTrip.objects.filter(user=request.user, trip=trip)) == 1 
            context['trips'][i]['trips'].append({'trip_info' : trip,
                                                 'users' : [user_trip.user.first_name + " " + user_trip.user.last_name for user_trip in UserTrip.objects.filter(trip=trip.id)],
                                                 'joining' : joining,
                                                })
    return render(request, 'cotravelling/index.html', context)
    
def add_trip(request):
    try:
        with transaction.atomic():
            trip = Trip()
            trip.target = request.POST['target']
            trip.datetime = datetime.strptime(request.POST['datetime'], '%d.%m.%Y %H:%M')
            trip.free_places = request.POST['free_places']
            trip.save()
            user_trip = UserTrip(user=request.user, trip=trip)
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
                user_trip = UserTrip(user=request.user, trip=trip)
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
    
def login(request):
    return render(request, 'cotravelling/login.html', {})
    
def logout(request):
    django_logout(request)
    return HttpResponseRedirect(reverse('cotravelling:index'))

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
        context["participants"] = [user_trip.user for user_trip in UserTrip.objects.filter(trip__id=kwargs['chat_id'])] 
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
