from django.shortcuts import get_object_or_404, render
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse

from .models import *

from django.contrib.auth.decorators import login_required

from django.contrib.auth import logout as django_logout

from django.db import transaction

from datetime import datetime, timedelta

def index(request):
    if request.POST:
        if 'target' in request.POST:
            return add_trip(request)
        elif request.user.is_authenticated and str(request.POST).find("join") != -1:
            return join_trip(request)
        elif request.user.is_authenticated and str(request.POST).find("leave") != -1:
            return leave_trip(request)
    if request.GET and 'from' in request.GET:
        date_from = request.GET['from']
    else:
        date_from = datetime.today()
    trips = [Trip.objects.filter(date__range=(timezone.now() - timezone.timedelta(1), timezone.now()))]
    username = None
    if request.user.is_authenticated:
        username = request.user.first_name + " " + request.user.last_name + " " + request.user.username
    trips = Trip.objects.order_by('-date')
    context = {'trips': [], 'auth': username}
    for trip in trips:
        joining = False
        if request.user.is_authenticated:
            joining = len(UserTrip.objects.filter(user=request.user, trip=trip)) == 1 
        context['trips'].append({'trip_info' : trip,
                                 'users' : [user_trip.user for user_trip in UserTrip.objects.filter(trip=trip.id)],
                                 'joining' : joining,
                                })
    return render(request, 'cotravelling/index.html', context)
    
def add_trip(request):
    try:
        with transaction.atomic():
            trip = Trip()
            trip.target = request.POST['target']
            trip.date = request.POST['date']
            trip.free_places = request.POST['free_places']
            trip.save()
            user_trip = UserTrip(user=request.user, trip=trip)
            user_trip.save()
    except Exception as e:
        pass
    return HttpResponseRedirect(reverse('cotravelling:index'))
    
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
    return HttpResponseRedirect(reverse('cotravelling:index'))
    
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
    return HttpResponseRedirect(reverse('cotravelling:index'))
    
def login(request):
    return render(request, 'cotravelling/login.html', {})
    
def logout(request):
    django_logout(request)
    return HttpResponseRedirect(reverse('cotravelling:index'))
