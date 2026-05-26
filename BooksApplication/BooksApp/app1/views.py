from django.shortcuts import render, redirect
from .models import Author, Book, BookAuthor
from .forms import BookForm
# Create your views here.

def index(request):
    all_books = Book.objects.all()
    context = {"books": all_books, "pageTitle": "Book Application"}
    return render(request, 'index.html', context)


def add(request):
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            author = Author.objects.filter(user=request.user).first()
            if author:
                book = form.save()
                BookAuthor.objects.get_or_create(book=book, author=author)
                return redirect('index')
            else:
                # If user has no baker profile, show error or redirect to create one
                form.add_error(None, "You must have a author profile to add book.")

    form = BookForm()
    return render(request, 'add.html', {"form":form})