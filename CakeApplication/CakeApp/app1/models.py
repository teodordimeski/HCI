from tkinter.constants import CASCADE

from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Baker(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} {self.surname}"

class Cake(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.FloatField()
    weight = models.FloatField()
    description = models.TextField()
    image = models.ImageField(upload_to='cakeimages')
    baker = models.ForeignKey(Baker, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

