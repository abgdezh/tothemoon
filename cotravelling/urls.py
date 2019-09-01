#!/usr/bin/python

from django.urls import path
from django.conf.urls import url
from django.contrib.auth.views import LogoutView, LoginView

from . import trip_views, common_views, order_views


app_name = 'cotravelling'
urlpatterns = [
    path('findtrip/', trip_views.findtrip, name='findtrip'),
    path('findtrip/<str:date_from>', trip_views.findtrip, name='findtrip'),
    path('load_trips/<str:datetime>/<int:user>/<str:direction>/<int:diff>', trip_views.load_trips, name='findtrip'),
    path('load_trips/<str:datetime>/undefined/<str:direction>/<int:diff>', trip_views.load_trips, name='findtrip'),
    path('accept/<int:usertrip>', trip_views.accept, name='accept'),
    path('reject/<int:usertrip>', trip_views.reject, name='reject'),
    
    path('chat/<int:chat_id>', trip_views.chat, name='chat'),
    path('load_messages/<int:trip_id>/<int:last_message_id>', trip_views.load_messages, name='chat'),
    path('add_message/<int:chat_id>', trip_views.add_message, name='chat'),
    
    path('findorder/', order_views.findorder, name='findorder'),
    path('load_orders/<str:datetime>/<int:user>', order_views.load_orders, name='findorder'),
    path('load_orders/<str:datetime>/undefined', order_views.load_orders, name='findorder'),
    path('orders_accept/<int:userorder>', order_views.accept, name='accept'),
    path('orders_reject/<int:userorder>', order_views.reject, name='reject'),
    
    path('orders_chat/<int:chat_id>', order_views.orders_chat, name='chat'),
    path('load_orders_messages/<int:order_id>/<int:last_message_id>', order_views.load_orders_messages, name='chat'),
    path('add_orders_message/<int:chat_id>', order_views.add_orders_message, name='chat'),
    
    path('logout/', common_views.logout, name='logout'),
    path('', common_views.about, name='about'),
]
