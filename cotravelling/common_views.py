from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth import logout as django_logout


def about(request):
    return render(request, 'cotravelling/about.html', {})


def logout(request):
    django_logout(request)
    print(request)
    return HttpResponseRedirect(reverse('cotravelling:findtrip'))
