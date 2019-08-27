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


def build_order(date, user=None):
    orders = Order.objects.filter(datetime__gte=date, datetime__lt=date + timedelta(1)).order_by('datetime', 'id')
    for order in orders:
        order.joining = False
        order.is_owner = False
        order.admitted = False
        if type(user) is int:
            order.joining = len(UserOrder.objects.filter(user_id=user, order=order)) == 1
            if order.joining:
                user_order = UserOrder.objects.get(user_id=user, order=order)
                order.is_owner = user_order.is_owner
                order.admitted = user_order.admitted
        elif user and user.is_authenticated:
            order.joining = len(UserOrder.objects.filter(user=user, order=order)) == 1
            if order.joining:
                user_order = UserOrder.objects.get(user=user, order=order)
                order.is_owner = user_order.is_owner
                order.admitted = user_order.admitted
        order.users = [user_order.user.first_name + " " + user_order.user.last_name for user_order in UserOrder.objects.filter(order=order.id, admitted=True)]
    return orders


def build_context(date_from, days, user):
    orders = [build_order(date_from + timedelta(i), user) for i in range(days)]
    context = {'orders': 
               [{'orders' : orders[i], 
                 'date' : datetime.strftime(date_from + timedelta(i), "%A, %-d %B"),
                }
                 for i in range(days)],
                'until_date' : datetime.strftime(date_from + timedelta(days), "%Y-%m-%d"),
                'auth' : type(user) is int or (user and user.is_authenticated)
              }
    return context


def handle_post_request(request):
    if 'target' in request.POST:
        return add_order(request)
    elif request.user and request.user.is_authenticated and str(request.POST).find("join") != -1:
        return join_order(request)
    elif request.user and request.user.is_authenticated and str(request.POST).find("leave") != -1:
        return leave_order(request)
    elif request.user and request.user.is_authenticated and str(request.POST).find("ask") != -1:
        return ask_order(request)
#    elif request.user and request.user.is_authenticated and str(request.POST).find("accept") != -1:
#        return accept(request)
    return HttpResponseRedirect(reverse('cotravelling:findorder'))


def findorder(request):
    if request.POST:
        return handle_post_request(request)
    date_from = date.today()
    date_from = timezone.make_aware(datetime.combine(date_from, time()))
    
    user_agent = get_user_agent(request)
    if user_agent.is_mobile:
        days = 3
    else:
        days = 3

    context = build_context(date_from, days, request.user)
    context["user"] = request.user
    return render(request, 'cotravelling/findorder.html', context)
    

def load_orders(request, **kwargs):
    if request.POST:
        return handle_post_request(request)
    date_from = datetime.strptime(kwargs['datetime'], '%Y-%m-%d')
    date_from = timezone.make_aware(datetime.combine(date_from, time()))
    user = kwargs.get("user")
    days = 7
    context = build_context(date_from, days, user)
    print("context")
    return JsonResponse({"page" : render_to_string('cotravelling/order.html', context, request=request),
                         "date" : kwargs['datetime'],
                         "new_date" : datetime.strftime(date_from + timedelta(days), '%Y-%m-%d')
                         })


def add_order(request):
    try:
        with transaction.atomic():
            order = Order()
            order.source = request.POST['source']
            order.target = request.POST['target']
            order.datetime = timezone.make_aware(datetime.strptime(request.POST['datetime'], '%d.%m.%Y %H:%M'))
            order.is_closed = 'is_closed' in request.POST
            order.save()
            user_order = UserOrder(user=request.user, order=order, is_owner=True, admitted=True)
            user_order.save()
    except Exception as e:
        print(e)
    return HttpResponseRedirect(reverse('cotravelling:findorder'))
    

def join_order(request):
    try:
        order_id = [int(s.replace("join", "")) for s in request.POST if s.startswith("join")][0]
        with transaction.atomic():
            order = Order.objects.get(id=order_id)
            if not order.is_closed:
                user_order = UserOrder(user=request.user, order=order, is_owner=False, admitted=True)
                order.save()
                user_order.save()
            
    except Exception as e:
        pass
    return HttpResponseRedirect(reverse('cotravelling:findorder'))
    
    
def accept(request, **kwargs):
    try:
        with transaction.atomic():
            user_order_id = kwargs['userorder']
            user_order = UserOrder.objects.get(id=user_order_id)
            order = Order.objects.get(id=user_order.order_id)
            actor_user_order = UserOrder.objects.get(user_id=request.user.id, order=order)
            if actor_user_order.admitted:
                user_order.admitted = True
                order.save()
                user_order.save()
        return HttpResponseRedirect('/orders_chat/' + str(order.id))
    except Exception as e:
        print(e)
        return HttpResponseRedirect(reverse('cotravelling:findorder'))
        

def reject(request, **kwargs):
    try:
        with transaction.atomic():
            user_order_id = kwargs['userorder']
            user_order = UserOrder.objects.get(id=user_order_id)
            order = Order.objects.get(id=user_order.order_id)
            actor_user_order = UserOrder.objects.get(user_id=request.user.id, order=order)
            if actor_user_order.admitted:
                order.save()
                user_order.delete()
        return HttpResponseRedirect('/orders_chat/' + str(order.id))
    except Exception as e:
        print(e)
        return HttpResponseRedirect(reverse('cotravelling:findorder'))


def leave_order(request):
    try:
        order_id = [int(s.replace("leave", "")) for s in request.POST if s.startswith("leave")][0]
        with transaction.atomic():
            order = Order.objects.get(id=order_id)
            user_order = UserOrder.objects.get(user=request.user, order=order)
            order.save()
            user_order.delete()
    except Exception as e:
        pass
    return HttpResponseRedirect(reverse('cotravelling:findorder'))


def ask_order(request):
    try:
        order_id = [int(s.replace("ask", "")) for s in request.POST if s.startswith("ask")][0]
        with transaction.atomic():
            order = Order.objects.get(id=order_id)
            user_order = UserOrder(user=request.user, order=order, is_owner=False, admitted=False)
            order.save()
            user_order.save()
            
    except Exception as e:
        pass
    return HttpResponseRedirect(reverse('cotravelling:findorder'))


def load_orders_messages(request, **kwargs):
    last_message_id = kwargs['last_message_id']
    order_id = kwargs['order_id']
    context = {"messages" : []}
    context["messages"] = OrdersMessage.objects.filter(order__id=order_id, id__gt=last_message_id).order_by('datetime')
    if context["messages"]:
        new_last_message_id = context["messages"][len(context["messages"]) - 1].id
    else:
        new_last_message_id = last_message_id
    return JsonResponse({"page" : render_to_string('cotravelling/orders_message.html', context, request=request),
                         "last_message_id" : last_message_id,
                         "new_last_message_id" : new_last_message_id
                         })


@login_required(login_url='/')
def orders_chat(request, **kwargs):
    context = {"messages" : []}
    if UserOrder.objects.filter(order__id=kwargs['chat_id'], user=request.user, admitted=True):
        context["messages"] = OrdersMessage.objects.filter(order__id=kwargs['chat_id']).order_by('datetime')
    else:
        context["forbidden"] = True
    try:
        context["order_info"] = Order.objects.get(id=kwargs['chat_id'])
        remaining_time = context["order_info"].datetime - timezone.make_aware(datetime.now())
        context["order_info"].remaining_time = format_timedelta(remaining_time)
        context["order_info"].is_over = remaining_time > timedelta(0)
        context["participants"] = UserOrder.objects.filter(order__id=kwargs['chat_id'], admitted=True)
        context["requested_participants"] = UserOrder.objects.filter(order__id=kwargs['chat_id'], admitted=False)
        if context["messages"]:
            context["last_message_id"] = context["messages"][len(context["messages"]) - 1].id
        else:
            context["last_message_id"] = 0
    except Order.DoesNotExist:
        raise Http404("Order does not exist")
    return render(request, 'cotravelling/orderchat.html', context)

 
def add_orders_message(request, **kwargs):
    try:
        message_text = request.POST["content"]
        if not message_text:
            return JsonResponse({})
        order_id = kwargs['chat_id']
        with transaction.atomic():
            message = OrdersMessage()
            message.author = request.user
            message.order = Order.objects.get(id=order_id)
            message.text = message_text
            message.save()
            
    except Exception as e:
        print(e)
    return JsonResponse({})

