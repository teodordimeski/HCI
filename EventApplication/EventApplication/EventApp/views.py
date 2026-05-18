from django.db.models import Model
from django.shortcuts import render, redirect

from .forms import EventForm
from .models import Event, Band, EventBand

# Create your views here.
def index(request):
    events = Event.objects.filter(user=request.user)
    context = {'events': events}
    return render(request,'index.html', context)

def add(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            event.save()
            band_names = event.bands.split(',')
            for band in band_names:
                band_obj = Band.objects.filter(name=band).first()
                if band_obj:
                    EventBand.objects.create(event=event, band=band_obj)
            return redirect('index')
    form = EventForm()
    return render(request, 'add.html', {"form": form})