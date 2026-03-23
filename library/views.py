from django.shortcuts import render, redirect, get_object_or_404
from .models import Book, IssueBook, Reservation
from .forms import BookForm, SearchForm, IssueBookForm, ReservationForm, UserRegistrationForm, UserLoginForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile



def home(request):
    books = Book.objects.all()[:6]  # Show only 6 books on home page
    return render(request, 'home.html', {'books': books})


@login_required
def dashboard(request):
    total_books = Book.objects.count()
    issued_books = IssueBook.objects.filter(user=request.user, returned=False)
    overdue_books = issued_books.filter(due_date__lt=timezone.now().date())
    reservations = Reservation.objects.filter(user=request.user, is_active=True)

    # Calculate total fines
    total_fines = sum(issue.calculate_fine() for issue in issued_books)

    context = {
        'total_books': total_books,
        'issued_books': issued_books,
        'overdue_books': overdue_books,
        'reservations': reservations,
        'total_fines': total_fines,
    }
    return render(request, 'dashboard.html', context)


@login_required
def book_list(request):
    books = Book.objects.all()
    search_form = SearchForm(request.GET)

    if search_form.is_valid():
        query = search_form.cleaned_data.get('query')
        author = search_form.cleaned_data.get('author')
        category = search_form.cleaned_data.get('category')

        if query:
            books = books.filter(
                Q(title__icontains=query) |
                Q(isbn__icontains=query) |
                Q(description__icontains=query)
            )
        if author:
            books = books.filter(author__name__icontains=author)
        if category:
            books = books.filter(category__name__icontains=category)

    # Pagination
    paginator = Paginator(books, 12)  # 12 books per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_form': search_form,
    }
    return render(request, 'book_list.html', context)


def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    # Check if user has this book issued
    user_issue = None
    if request.user.is_authenticated:
        user_issue = IssueBook.objects.filter(user=request.user, book=book, returned=False).first()
    
    # Get related books by same author
    related_books = Book.objects.filter(author=book.author).exclude(id=book.id)[:4]
    
    # Calculate availability percentage
    availability_percentage = 0
    if book.quantity > 0:
        availability_percentage = (book.available_quantity / book.quantity) * 100
    
    context = {
        'book': book,
        'user_issue': user_issue,
        'related_books': related_books,
        'availability_percentage': availability_percentage,
    }
    return render(request, 'book_detail.html', context)


@login_required
def add_book(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to add books.')
        return redirect('book_list')

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(f"Book ID: {book.id}, Title: {book.title}, ISBN: {book.isbn}")
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            book.qr_code.save(f'qr_{book.id}.png', ContentFile(buffer.getvalue()), save=False)
            book.save()

            messages.success(request, f'Book "{book.title}" added successfully!')
            return redirect('book_list')
    else:
        form = BookForm()

    # Get statistics for the template
    from .models import Author, Category
    context = {
        'form': form,
        'total_books': Book.objects.count(),
        'total_authors': Author.objects.count(),
        'total_categories': Category.objects.count(),
        'authors': Author.objects.all(),
        'categories': Category.objects.all(),
    }
    return render(request, 'add_book.html', context)


@login_required
def edit_book(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit books.')
        return redirect('book_list')
    
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            book = form.save()
            # Regenerate QR code if title or ISBN changed
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(f"Book ID: {book.id}, Title: {book.title}, ISBN: {book.isbn}")
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            book.qr_code.save(f'qr_{book.id}.png', ContentFile(buffer.getvalue()), save=False)
            book.save()

            messages.success(request, f'Book "{book.title}" updated successfully!')
            return redirect('book_list')
    else:
        form = BookForm(instance=book)

    # Get statistics for the template
    from .models import Author, Category
    context = {
        'form': form,
        'book': book,
        'total_books': Book.objects.count(),
        'total_authors': Author.objects.count(),
        'total_categories': Category.objects.count(),
        'authors': Author.objects.all(),
        'categories': Category.objects.all(),
        'is_edit': True,
    }
    return render(request, 'add_book.html', context)


@login_required
def issue_book(request, pk):
    book = get_object_or_404(Book, id=pk)
    if book.available_quantity > 0:
        issue = IssueBook.objects.create(
            user=request.user,
            book=book,
            due_date=timezone.now().date() + timezone.timedelta(days=14)
        )
        book.available_quantity -= 1
        book.save()
        messages.success(request, f'Book "{book.title}" issued successfully!')
        # Send email
        send_mail(
            'Book Issued',
            f'You have issued "{book.title}". Due date: {issue.due_date}',
            settings.EMAIL_HOST_USER,
            [request.user.email],
            fail_silently=True,
        )
    else:
        messages.error(request, 'Book is not available!')
    return redirect('dashboard')


@login_required
def return_book(request, pk):
    issue = get_object_or_404(IssueBook, id=pk, user=request.user)
    if not issue.returned:
        issue.returned = True
        issue.return_date = timezone.now().date()
        fine = issue.calculate_fine()
        issue.book.available_quantity += 1
        issue.book.save()
        issue.save()
        messages.success(request, f'Book returned successfully! Fine: ${fine}')
        # Send email
        send_mail(
            'Book Returned',
            f'You have returned "{issue.book.title}". Fine: ${fine}',
            settings.EMAIL_HOST_USER,
            [request.user.email],
            fail_silently=True,
        )
        # Check reservations
        reservations = Reservation.objects.filter(book=issue.book, is_active=True).order_by('reservation_date')
        if reservations.exists():
            reservation = reservations.first()
            send_mail(
                'Reserved Book Available',
                f'The book "{issue.book.title}" you reserved is now available.',
                settings.EMAIL_HOST_USER,
                [reservation.user.email],
                fail_silently=True,
            )
            reservation.is_active = False
            reservation.save()
    else:
        messages.error(request, 'Book already returned!')
    return redirect('dashboard')


@login_required
def reserve_book(request, pk):
    book = get_object_or_404(Book, id=pk)
    if book.available_quantity == 0:
        reservation, created = Reservation.objects.get_or_create(
            user=request.user,
            book=book,
            defaults={'is_active': True}
        )
        if created:
            messages.success(request, f'Book "{book.title}" reserved successfully!')
        else:
            messages.info(request, 'You have already reserved this book.')
    else:
        messages.info(request, 'Book is available, no need to reserve.')
    return redirect('book_list')


from django.contrib.auth import logout
from django.contrib.auth.views import LoginView


class CustomLoginView(LoginView):
    template_name = 'login.html'
    form_class = UserLoginForm
    success_url = '/dashboard/'  # Redirect to dashboard after successful login
    
    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().username}!')
        return super().form_valid(form)


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, 'Access denied!')
        return redirect('dashboard')

    # Analytics data
    total_books = Book.objects.count()
    total_users = User.objects.count()
    total_issues = IssueBook.objects.count()
    active_issues = IssueBook.objects.filter(returned=False).count()
    overdue_issues = IssueBook.objects.filter(returned=False, due_date__lt=timezone.now().date()).count()
    total_reservations = Reservation.objects.filter(is_active=True).count()

    # Recent activities
    recent_issues = IssueBook.objects.order_by('-issue_date')[:10]
    recent_returns = IssueBook.objects.filter(returned=True).order_by('-return_date')[:10]

    context = {
        'total_books': total_books,
        'total_users': total_users,
        'total_issues': total_issues,
        'active_issues': active_issues,
        'overdue_issues': overdue_issues,
        'total_reservations': total_reservations,
        'recent_issues': recent_issues,
        'recent_returns': recent_returns,
    }
    return render(request, 'admin_dashboard.html', context)