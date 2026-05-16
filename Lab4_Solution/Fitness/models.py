from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Trainer(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    yearsExperience = models.IntegerField()
    website = models.URLField()

    def __str__(self):
        return self.name

class Training(models.Model):
    CATEGORY = [
        ("cardio","cardio"),
        ("strength", "strength"),
        ("yoga", "yoga"),
        ("HIIT", "HIIT"),
        ("pilates", "pilates"),
        ("crossfit", "crossfit"),
        ("stretching", "stretching"),
    ]

    LEVEL = [
        ("beginer","beginer"),
        ("intermediate", "intermediate"),
        ("advanced", "advanced"),
    ]

    name =  models.CharField(max_length=100)
    image =  models.ImageField(upload_to='images/')
    trainer =  models.ForeignKey(Trainer, on_delete=models.CASCADE)
    category =  models.CharField(choices=CATEGORY, max_length=20)
    level =  models.CharField(choices=LEVEL, max_length=20)
    duration = models.IntegerField()
    capacity = models.IntegerField()
    price = models.FloatField()
