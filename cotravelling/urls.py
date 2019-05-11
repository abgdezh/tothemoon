#!/usr/bin/python

from django.urls import path
from django.conf.urls import url
from django.contrib.auth.views import LogoutView, LoginView

from . import views


app_name = 'cotravelling'
urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
]
