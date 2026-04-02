from django.contrib import admin
from .models import *

# Register your models here.

class AdminCourse(admin.ModelAdmin):

    exclude = ("user",)

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

class LecturerAdmin(admin.ModelAdmin):

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False


class CategoryAdmin(admin.ModelAdmin):

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False


admin.site.register(Lecturer,LecturerAdmin)
admin.site.register(Category,CategoryAdmin)
admin.site.register(Course,AdminCourse)
