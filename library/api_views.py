from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import send_mail
from django.conf import settings
from .models import Book, IssueBook, Reservation, Author, Category
from .serializers import (
    BookSerializer, IssueBookSerializer, ReservationSerializer,
    AuthorSerializer, CategorySerializer, UserSerializer
)
from django.contrib.auth.models import User
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import timedelta


class CustomTokenObtainPairView(TokenObtainPairView):
    pass


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['title', 'author__name', 'category__name', 'isbn']
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        book = serializer.save()
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"Book ID: {book.id}, Title: {book.title}, ISBN: {book.isbn}")
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        book.qr_code.save(f'qr_{book.id}.png', ContentFile(buffer.getvalue()), save=False)
        book.save()

    @action(detail=True, methods=['post'])
    def issue(self, request, pk=None):
        book = self.get_object()
        if book.available_quantity > 0:
            issue = IssueBook.objects.create(
                user=request.user,
                book=book,
                due_date=timezone.now().date() + timedelta(days=14)
            )
            book.available_quantity -= 1
            book.save()
            # Send email notification
            self.send_issue_notification(request.user, book)
            return Response({'status': 'Book issued successfully'})
        return Response({'error': 'Book not available'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reserve(self, request, pk=None):
        book = self.get_object()
        if book.available_quantity == 0:
            reservation, created = Reservation.objects.get_or_create(
                user=request.user,
                book=book,
                defaults={'is_active': True}
            )
            if created:
                return Response({'status': 'Book reserved successfully'})
            return Response({'error': 'Book already reserved by you'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Book is available, no need to reserve'}, status=status.HTTP_400_BAD_REQUEST)

    def send_issue_notification(self, user, book):
        subject = 'Book Issued Successfully'
        message = f'Dear {user.username},\n\nYou have successfully issued "{book.title}".\nDue date: {timezone.now().date() + timedelta(days=14)}\n\nRegards,\nLibrary Management System'
        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])


class IssueBookViewSet(viewsets.ModelViewSet):
    queryset = IssueBook.objects.all()
    serializer_class = IssueBookSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IssueBook.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        issue = self.get_object()
        if not issue.returned:
            issue.returned = True
            issue.return_date = timezone.now().date()
            issue.calculate_fine()
            issue.book.available_quantity += 1
            issue.book.save()
            issue.save()
            # Send email notification
            self.send_return_notification(request.user, issue.book, issue.fine_amount)
            # Check for reservations
            self.check_reservations(issue.book)
            return Response({'status': 'Book returned successfully', 'fine': str(issue.fine_amount)})
        return Response({'error': 'Book already returned'}, status=status.HTTP_400_BAD_REQUEST)

    def send_return_notification(self, user, book, fine):
        subject = 'Book Returned Successfully'
        message = f'Dear {user.username},\n\nYou have successfully returned "{book.title}".\nFine amount: ${fine}\n\nRegards,\nLibrary Management System'
        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])

    def check_reservations(self, book):
        reservations = Reservation.objects.filter(book=book, is_active=True).order_by('reservation_date')
        if reservations.exists():
            reservation = reservations.first()
            # Send notification to reserved user
            subject = 'Reserved Book Available'
            message = f'Dear {reservation.user.username},\n\nThe book "{book.title}" you reserved is now available.\n\nRegards,\nLibrary Management System'
            send_mail(subject, message, settings.EMAIL_HOST_USER, [reservation.user.email])
            reservation.is_active = False
            reservation.save()


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer