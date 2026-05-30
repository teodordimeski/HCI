from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Agent(models.Model):
    name = models.CharField(max_length=30)
    surname = models.CharField(max_length=30)
    phone = models.CharField(max_length=30)
    linkedin = models.URLField(null=True, blank=True)
    number_properties_sold = models.IntegerField()
    email = models.EmailField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} {self.surname}"


class Property(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    size = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    image = models.ImageField(upload_to='estateiImages/')
    is_reserved = models.BooleanField(default=False)
    is_sold = models.BooleanField(default=False)
    price = models.IntegerField(default=0)
    characteristics = models.TextField(default="",null=True, blank=True)

    def __str__(self):
        return f"Name: {self.name} Size:{self.size} Description:{self.description}"


class AgentProof(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)

    def __str__(self):
        return f"Agent: {self.agent.name} Property: {self.property.name}"


class Characteristic(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()

    def __str__(self):
        return f"Name: {self.name} Price: {self.price}"

