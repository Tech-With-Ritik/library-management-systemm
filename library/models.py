from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Author(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    isbn = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    quantity = models.IntegerField(default=1)
    available_quantity = models.IntegerField(default=1)
    cover = models.ImageField(upload_to='books/', blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.available_quantity:
            self.available_quantity = self.quantity
        super().save(*args, **kwargs)


class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    reservation_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f"{self.user} reserved {self.book}"


class IssueBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    returned = models.BooleanField(default=False)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_overdue = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.book}"

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = timezone.now().date() + timedelta(days=14)  # 14 days loan period
        super().save(*args, **kwargs)

    def calculate_fine(self):
        if self.returned:
            return 0
        days_overdue = (timezone.now().date() - self.due_date).days
        if days_overdue > 0:
            self.fine_amount = days_overdue * 0.50  # $0.50 per day
            self.is_overdue = True
            self.save()
            return self.fine_amount
        return 0
        return f"{self.user} - {self.book}"