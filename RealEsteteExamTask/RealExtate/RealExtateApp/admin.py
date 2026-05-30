from datetime import datetime, date
from os.path import exists

from django.contrib import admin
from django.db.models import F

from .models import *
# Register your models here.

class AgentProofInline(admin.TabularInline):
    model = AgentProof

class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'surname', )

    def has_add_permission(self, request):
        return request.user.is_superuser

class CharacteristicAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')

    def has_add_permission(self, request):
        return request.user.is_superuser

class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'price' , 'description' , 'size')
    inlines = [AgentProofInline]
    exclude = ['price']

    def has_add_permission(self, request):
        return Agent.objects.filter(user=request.user).exists()

    def save_model(self, request, obj, form, change):
        if not change:
            if Agent.objects.filter(user=request.user).exists():
                agent = Agent.objects.filter(user=request.user).first()
                super().save_model(request, obj, form, change)
                AgentProof.objects.create(agent=agent, property=obj)
                return

        else:
            old_obj = Property.objects.get(pk=obj.pk)
            super().save_model(request, obj, form, change)
            if old_obj.is_sold==False and obj.is_sold==True:
                for prop in AgentProof.objects.filter(property=obj):
                    prop.agent.number_properties_sold += 1
                    prop.agent.save()
            return



    def has_delete_permission(self, request, obj = None):
        if obj and obj.characteristics == "":
            return True
        return False

    def has_view_permission(self, request, obj = None):
        return Agent.objects.filter(user=request.user).exists() or request.user.is_superuser

    def has_change_permission(self, request, obj = None):
        agent = Agent.objects.filter(user=request.user).first()
        if obj and agent:
            return AgentProof.objects.filter(agent__user=request.user, property=obj).exists()
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs.filter(date=date.today()).distinct()

        return qs


admin.site.register(Agent, AgentAdmin)
admin.site.register(Characteristic, CharacteristicAdmin)
admin.site.register(Property, PropertyAdmin)

