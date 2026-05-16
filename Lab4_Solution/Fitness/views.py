from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from .forms import TrainingForm
from .models import Training
# Create your views here.

def index(request):
    all_trainings = Training.objects.all()
    context = {"trainings": all_trainings, "pageTitle": "Training Application"}
    return render(request, 'index.html', context)

def add(request):
    if request.method == "POST":
        form = TrainingForm(request.POST, request.FILES)
        if form.is_valid():
            training = form.save(commit=False)
            training.save()
            return redirect('index')
    form = TrainingForm()
    return render(request, 'addTraining.html', {"form":form})