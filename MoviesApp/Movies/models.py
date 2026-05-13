
from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class ProductionHouse(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    founded_year = models.IntegerField()
    website = models.URLField()

    def __str__(self):
        return self.name


class Movie(models.Model):
    GENRE = [
        ("ACTION", "Action"),
        ("COMEDY", "Comedy"),
        ("DRAMA", "Drama"),
        ("HORROR", "Horror"),
        ("SCIFI", "Sci-Fi"),
        ("DOCUMENTARY", "Documentary"),
        ("ANIMATION", "Animation"),
    ]

    FORMAT = [
        ("DIGITAL", "Digital"),
        ("BLUERAY", "Blu-ray"),
        ("DVD", "DVD"),
    ]

    title = models.CharField(max_length=100)
    poster = models.ImageField(upload_to='media/')
    imbd = models.CharField(max_length=100)
    year = models.IntegerField()
    productionHouse = models.ForeignKey(ProductionHouse, on_delete=models.CASCADE)
    duration = models.FloatField()
    genre = models.CharField(max_length=20, choices=GENRE)
    format = models.CharField(max_length=15,choices=FORMAT)
    price = models.DecimalField(max_digits=10, decimal_places=2)



