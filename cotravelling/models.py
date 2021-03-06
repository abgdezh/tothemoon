from django.db import models

from django.contrib.auth.models import User

from django.utils import timezone
        
class Trip(models.Model):
    source = models.CharField(max_length=30, default='')
    target = models.CharField(max_length=30, default='')
    vehicle = models.CharField(max_length=30, default='')
    datetime = models.DateTimeField(default=timezone.now)
    free_places = models.IntegerField(default=0)
    is_closed = models.BooleanField(default=False)
    
    def __str__(self):
        date = self.date()
        time = self.time()
        return f'Из {self.source} в {self.target}, {date}, {time}, {self.free_places} мест,' +\
               (' с подтверждением' if self.is_closed else ' без подтверждения')
    
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
        return f'Поездка: [{self.trip}], создатель: {self.author.first_name} {self.author.last_name}, {self.datetime}: {self.text}'
        
    def author_info(self):
        return self.author.first_name + ' ' + self.author.last_name


class UserTrip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    is_owner = models.BooleanField(default=False)
    admitted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'trip',)
    
    def __str__(self):
        return f'Поездка: [{self.trip}], пользователь: {self.user.first_name} {self.user.last_name}, владелец: {self.is_owner}, допущен: {self.admitted}'


class Order(models.Model):
    source = models.CharField(max_length=30, default='')
    target = models.CharField(max_length=30, default='')
    datetime = models.DateTimeField(default=timezone.now)
    datetime_end = models.DateTimeField(default=timezone.now)
    is_closed = models.BooleanField(default=False)
    #min_cost = models.IntegerField(default=0)
    
    def __str__(self):
        return self.source + ' ' + self.target + ' ' + self.vehicle + ' ' + str(self.datetime) + ' ' + str(self.free_places) + ' ' + str(self.is_closed)
    
    def time(self):
        return timezone.localtime(self.datetime).time()
        
    def date(self):
        return timezone.localdate(self.datetime)


class OrdersMessage(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    datetime = models.DateTimeField(default=timezone.now)
    text = models.CharField(max_length=200)
    
    def __str__(self):
        return str(self.order) + '/' + str(self.author) + ', ' + str(self.datetime) + ': ' + str(self.text)
        
    def author_info(self):
        return self.author.first_name + ' ' + self.author.last_name


class UserOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    is_owner = models.BooleanField(default=False)
    admitted = models.BooleanField(default=False)
    #cost = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'order',)
    
    def __str__(self):
        return str(self.user) + '/' + str(self.order) + '/' + str(self.is_owner) + '/' + str(self.admitted)


class Location(models.Model):
    name = models.CharField(max_length=30, default='')
    
    def __str__(self):
        return self.name

class OrderCompanies(models.Model):
    name = models.CharField(max_length=50, default='')
    website = models.TextField(default='')
    logo_img = models.FileField(default='')

    def __str__(self):
        return self.name

class Promocode(models.Model):
    name = models.CharField(max_length=200, default='Промокод')
    code = models.CharField(max_length=10, default='')
    desc = models.TextField(default='')
    expiration_date = models.DateTimeField(blank=True, null=True)
    company = models.ForeignKey(OrderCompanies, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Sale(models.Model):
    name = models.CharField(max_length=200, default='Акция')
    desc = models.TextField(default='')
    price = models.CharField(max_length=30, default='')
    link = models.TextField(default='')
    expiration_date = models.DateTimeField(blank=True, null=True)
    company = models.ForeignKey(OrderCompanies, on_delete=models.CASCADE)
    sale_image = models.FileField(default='')

    def __str__(self):
        return self.name
    
class UserPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_start = models.DateTimeField(default=timezone.now)
    date_end = models.DateTimeField()

    def __str__(self):
        return str(self.user) + str(self.date_start) + str(self.date_end)