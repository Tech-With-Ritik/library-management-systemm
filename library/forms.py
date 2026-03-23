from django import forms
from .models import Book, IssueBook, Reservation
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'category', 'isbn', 'description', 'quantity', 'cover']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter book title',
                'required': True
            }),
            'author': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'isbn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ISBN (e.g., 978-0-123456-78-9)',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter book description (optional)'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 1,
                'required': True
            }),
            'cover': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }


class SearchForm(forms.Form):
    query = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search books...'}))
    author = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Filter by author'}))
    category = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Filter by category'}))


class IssueBookForm(forms.ModelForm):
    class Meta:
        model = IssueBook
        fields = ['book', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['book']


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email address'
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Create a password'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Confirm your password'
            }),
        }


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password'
    }))