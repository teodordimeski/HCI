from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .forms import MovieForm
from .models import Movie

def index(request):
    all_movies = Movie.objects.all()
    context = {"movies": all_movies, "pageTitle": "Movies Application"}
    return render(request, 'index.html', context)

def details(request, id):
    try:
        movie = Movie.objects.get(id=id)
    except Movie.DoesNotExist:
        return index(request)
    data = {"movie": movie}
    return render(request, 'details.html', data)

def add(request):
    if request.method == "POST":
        form = MovieForm(request.POST, request.FILES)
        if form.is_valid():
            movie = form.save()
            return redirect('index')
    form = MovieForm()
    return render(request, 'addMovies.html', {"form": form})