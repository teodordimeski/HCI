from django.shortcuts import render, redirect
from .models import Cake, Baker
from .forms import CakeForm
# Create your views here.

def index(request):
    all_cakes = Cake.objects.all()
    context = {"cakes": all_cakes, "pageTitle": "Cake Application"}
    return render(request, 'index.html', context)


def add(request):
    if request.method == "POST":
        form = CakeForm(request.POST, request.FILES)
        if form.is_valid():
            cake = form.save(commit=False)
            baker = Baker.objects.filter(user=request.user).first()
            if baker:
                cake.baker = baker
                cake.save()
                return redirect('index')
            else:
                # If user has no baker profile, show error or redirect to create one
                form.add_error(None, "You must have a baker profile to add cakes.")

    form = CakeForm()
    return render(request, 'add.html', {"form":form})