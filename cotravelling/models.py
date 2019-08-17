from django.db import models

from django.contrib.auth.models import User

from django.utils import timezone
        
class Trip(models.Model):
    source = models.CharField(max_length=30, default="")
    target = models.CharField(max_length=30, default="")
    vehicle = models.CharField(max_length=30, default="")
    datetime = models.DateTimeField(default=timezone.now)
    free_places = models.IntegerField(default=0)
    is_open = models.BooleanField(default=False)
    
    def __str__(self):
        return self.source + " " + self.target + " " + self.vehicle + " " + str(self.datetime) + " " + str(self.free_places) + " " + str(self.is_open)
    
    def time(self):
        return timezone.localtime(self.datetime).time()
        
    def date(self):
        return timezone.localdate(self.datetime)
        
class Message(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    datetime = models.DateTimeField(default=timezone.now)
    text = models.CharField(max_length=200)
    
    def __str__(self):
        return str(self.trip) + "/" + str(self.author) + ", " + str(self.datetime) + ": " + str(self.text)
        
    def author_info(self):
        return self.author.first_name + " " + self.author.last_name

class UserTrip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    is_owner = models.BooleanField(default=False)
    admitted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'trip',)
    
    def __str__(self):
        return str(self.user) + "/" + str(self.trip) + "/" + str(self.is_owner) + "/" + str(self.admitted)
