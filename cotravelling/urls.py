#!/usr/bin/python

from django.urls import path
from django.conf.urls import url
from django.contrib.auth.views import LogoutView, LoginView

from . import views


app_name = 'cotravelling'
urlpatterns = [
    path('findtrip/', views.findtrip, name='findtrip'),
    path('logout/', views.logout, name='logout'),
    path('chat/<int:chat_id>', views.chat, name='chat'),
    path('load_trips/<str:datetime>/<int:user>', views.load_trips, name='findtrip'),
    path('load_trips/<str:datetime>/undefined', views.load_trips, name='findtrip'),
    path('accept/<int:usertrip>', views.accept, name='accept'),
    path('reject/<int:usertrip>', views.reject, name='reject'),
    path('load_messages/<int:trip_id>/<int:last_message_id>', views.load_messages, name='chat'),
    path('add_message/<int:chat_id>', views.add_message, name='chat'),
    path('', views.about, name='about'),
]
