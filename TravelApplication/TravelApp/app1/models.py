from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class TouristGuide(models.Model):

    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} {self.surname}"


class Trip(models.Model):

    place = models.CharField(max_length=50 , unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField()
    image = models.ImageField(upload_to='tripImages')
    touristGuide = models.ForeignKey(TouristGuide, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.place}"