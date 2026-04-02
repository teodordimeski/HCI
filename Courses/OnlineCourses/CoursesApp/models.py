from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Category(models.Model):

    name = models.CharField(max_length=100)
    description = models.TextField()
    isPopular = models.BooleanField()

    def __str__(self):
        return f"{self.name}"


class Lecturer(models.Model):
    EXPERIENCE = [
        ("B", "Beginer"),
        ("I", "Intermediate"),
        ("E", "Expert")
    ]

    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    biography = models.TextField()
    experience = models.CharField(max_length=1, choices=EXPERIENCE)

    def __str__(self):
        return f"{self.name} {self.surname}"


class Course(models.Model):

    name = models.CharField(max_length=100)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    photo = models.ImageField(upload_to="course_photos/", null=True, blank=True)
    price = models.FloatField()
    freeSeats = models.IntegerField()

    def __str__(self):
        return f"{self.name} - {self.lecturer} {self.user}"


