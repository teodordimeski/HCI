from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Event(models.Model):

    name = models.CharField(max_length=100)
    date = models.DateTimeField(default=None)
    posterImage = models.ImageField(upload_to='images/')
    user = models.ForeignKey(User,on_delete=models.CASCADE, blank=True, null=True)
    onOpenSky = models.BooleanField(default=None)
    bands = models.CharField(max_length=200, null=True, blank=True,default=None)

    def __str__(self):
        return f"{self.name} - {self.date}"



class Band(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    year = models.IntegerField()
    num_Attendences = models.IntegerField()

    def __str__(self):
        return self.name



class EventBand(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    band = models.ForeignKey(Band, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.event} - {self.band}"
