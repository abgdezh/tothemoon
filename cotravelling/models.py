from django.db import models

from django.contrib.auth.models import User

from django.utils import timezone
        
class Trip(models.Model):
    target = models.CharField(max_length=200)
    date = models.DateField(default=timezone.now)
    time = models.TimeField(default=timezone.now)
    free_places = models.IntegerField(default=0)
    
    def __str__(self):
        return self.target + " " + str(self.date) + " " + str(self.free_places)


class UserTrip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    is_owner = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'trip',)
    
    def __str__(self):
        return str(self.user) + " " + str(self.trip)
