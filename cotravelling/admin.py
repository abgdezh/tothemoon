from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(Trip)
admin.site.register(UserTrip)
admin.site.register(Message)
admin.site.register(Location)
admin.site.register(OrderCompanies)
admin.site.register(Promocode)
admin.site.register(Sale)
