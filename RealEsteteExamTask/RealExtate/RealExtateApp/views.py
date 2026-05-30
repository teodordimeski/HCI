from django.shortcuts import render, redirect
from .models import *
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from .forms import PropertyForm
# Create your views here.


def index(request):
    all_propeeties = Property.objects.filter(is_sold=False,size__gt=100)

    context = {"properties": all_propeeties,}
    return render(request, 'index.html', context)


def add(request):
    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property = form.save(commit=False)
            agent = Agent.objects.filter(user=request.user).first()
            if agent:
                for c in property.characteristics.split(","):
                    characteristic = Characteristic.objects.filter(name=c).first()
                    property.price += characteristic.price
                property.save()
                if property.is_sold:
                    agent.number_properties_sold+=1
                    agent.save()
                AgentProof.objects.create(agent=agent, property=property)
                return redirect('index')
            else:
                # If user has no baker profile, show error or redirect to create one
                form.add_error(None, "You must have a agent profile to add estates.")

    form = PropertyForm()
    return render(request, 'add.html', {"form":form})



def edit(request, pk):
    prop = get_object_or_404(Property, pk=pk)

    # (опционално) permission: само агент задолжен за овој оглас може да едитира
    agent = Agent.objects.filter(user=request.user).first()

    if not agent:
        return HttpResponseForbidden("Only agents can edit properties.")
    if not AgentProof.objects.filter(agent=agent, property=prop).exists():
        return HttpResponseForbidden("You are not responsible for this property.")

    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES, instance=prop)
        if form.is_valid():
            edited = form.save(commit=False)
            # ако ти треба логиката за price да се пресметува од карактеристики:
            edited.price = 0
            for c in edited.characteristics.split(","):
                characteristic = Characteristic.objects.filter(name=c).first()
                edited.price += characteristic.price

            # логика за sold -> инкремент (како во admin)
            old_is_sold = prop.is_sold
            edited.save()

            if not old_is_sold and edited.is_sold:
                for ap in AgentProof.objects.filter(property=edited).select_related("agent"):
                    ap.agent.number_properties_sold += 1
                    ap.agent.save()

            return redirect("index")
    else:
        form = PropertyForm(instance=prop)

    return render(request, "edit.html", {"form": form, "property": prop})