from django.contrib import admin

from .models import Book, Author, Category, IssueBook


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):

    list_display = ('title','author','category','quantity')

    search_fields = ('title','isbn')


admin.site.register(Author)
admin.site.register(Category)
admin.site.register(IssueBook)