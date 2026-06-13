from django.contrib import admin
from django.core.exceptions import ValidationError
import random

from .models import Cake, Baker


class CakeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'weight', 'baker')
    list_filter = ('baker',)
    search_fields = ('name', 'description')

    def has_view_permission(self, request, obj=None):
        return  Baker.objects.filter(user=request.user).exists()

    def has_change_permission(self, request, obj=None):
        # Само пекарот кој ја додал тортата може да ја менува
        if obj:
            return obj.baker.user == request.user

        return False

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        # Корисникот мора да е пекар
        if  Baker.objects.filter(user=request.user).exists():
             baker = Baker.objects.filter(user=request.user).first()
             if  Cake.objects.filter(baker=baker).count()>= 10:
                 return False
             return True
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            baker = Baker.objects.get(user=request.user)
            total_price = sum(c.price for c in Cake.objects.filter(baker=baker))
            if total_price + obj.price > 10000:
                raise ValidationError("Вкупната цена ги надминува 10 000.")
            obj.baker = baker

        super().save_model(request, obj, form, change)


class BakerAdmin(admin.ModelAdmin):
    list_display = ('name', 'surname', 'phone', 'email')

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        # Superuser гледа само пекари со ПОМАЛКУ од 5 торти
        # (пристап до листата е секогаш дозволен; филтрирањето е во get_queryset)
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            # Прикажи само пекари со помалку од 5 торти
            baker_ids = [b.pk for b in qs if b.cake_set.count() < 5]
            return qs.filter(pk__in=baker_ids)
        return qs.none()

    def delete_model(self, request, obj):
        """При бришење на пекар, неговите торти се распределуваат по случаен избор."""
        other_bakers = list(Baker.objects.exclude(pk=obj.pk))
        if other_bakers:
            for cake in obj.cake_set.all():
                cake.baker = random.choice(other_bakers)
                cake.save()
        else:
            # Ако нема други пекари, тортите се бришат
            obj.cake_set.all().delete()

        super().delete_model(request, obj)



admin.site.register(Cake, CakeAdmin)
admin.site.register(Baker, BakerAdmin)