from django.shortcuts import render, redirect
from .models import Trip, TouristGuide
from .forms import TripForm
# Create your views here.


def index(request):
    all_trips = Trip.objects.all()
    context = {"trips": all_trips, "pageTitle": "Trip Application"}
    return render(request, 'index.html', context)


def add(request):
    if request.method == "POST":
        form = TripForm(request.POST, request.FILES)
        if form.is_valid():
            trip = form.save(commit=False)
            guide = TouristGuide.objects.filter(user=request.user).first()
            if guide:
                trip.touristGuide = guide
                trip.save()
                return redirect('index')
            else:
                form.add_error(None, "You must have a baker profile to add cakes.")

    form = TripForm()
    return render(request, 'add.html', {"form":form})