from django.contrib import admin
from .models import Author, Customer, Book, BookAuthor
# Register your models here.

class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'surname', 'email')

    def has_add_permission(self, request):
        return request.user.is_superuser and not Author.objects.filter(user=request.user).exists()



class BookAdmin(admin.ModelAdmin):
    list_display = ('title' , 'price')


    def has_add_permission(self, request):
        return Author.objects.filter(user=request.user).exists()

    def save_model(self, request, obj, form, change):
        author = Author.objects.filter(user=request.user).first()
        super().save_model(request, obj, form, change)
        BookAuthor.objects.get_or_create(book=obj, author=author)

    def get_search_fields(self, request):
        if request.user.is_superuser:
            return ('description',)
        return ()

    def has_change_permission(self, request, obj = None):
        if obj:
            author = Author.objects.filter(user=request.user).first()
            if author:
                return BookAuthor.objects.filter(book=obj, author=author).exists()
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        author = Author.objects.filter(user=request.user).first()
        if not author:
            return qs

        return (
            qs.filter(bookauthor__author=author)
            .exclude(description__isnull=True)
            .exclude(description__exact='')
            .distinct()
        )



admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Customer)
admin.site.register(BookAuthor)