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
    path('', views.about, name='about'),
]
