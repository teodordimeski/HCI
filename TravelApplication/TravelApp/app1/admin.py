import random

from django.contrib import admin
from .models import TouristGuide, Trip
# Register your models here.


class TouristGuideAdmin(admin.ModelAdmin):
    list_display = ('name' , 'surname')

    def has_add_permission(self, request):
        return  request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if obj and request.user.is_superuser:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if obj and request.user.is_superuser:
            return True
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            guide_ids = [g.pk for g in qs if g.trip_set.count() < 3]
            return qs.filter(pk__in=guide_ids)
        return qs.none()

    def delete_model(self, request, obj):
        otherGuides = list(TouristGuide.objects.exclude(pk=obj.pk))
        if otherGuides:
            for trip in obj.trip_set.all():
                trip.touristGuide = random.choice(otherGuides)
                trip.save()

        else:
            obj.trip_set.all().delete()

        super().delete_model(request, obj)


class TripAdmin(admin.ModelAdmin):
    list_display = ('place' , 'price' , 'duration' , 'touristGuide')

    def has_add_permission(self, request):
        b = TouristGuide.objects.filter(user=request.user).exists()
        numTrips = Trip.objects.filter(touristGuide__user=request.user).count()
        return b and numTrips < 5

    def has_change_permission(self, request, obj=None):
        if obj and obj.touristGuide.user == request.user:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if obj and obj.touristGuide.user == request.user:
            return True
        return False

    def has_view_permission(self, request, obj=None):
        return TouristGuide.objects.filter(user=request.user).exists()

    def save_model(self, request, obj, form, change):
        guide = TouristGuide.objects.get(user=request.user)
        totalPrice = sum(t.price for t in Trip.objects.filter(touristGuide=guide))
        if totalPrice + obj.price > 50000:
            raise ValueError("Total price of trips for this guide cannot exceed 50000.")

        obj.touristGuide = guide
        super().save_model(request, obj, form, change)


admin.site.register(TouristGuide, TouristGuideAdmin)
admin.site.register(Trip, TripAdmin)