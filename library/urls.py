from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views
from .views_profile import profile_view
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'books', api_views.BookViewSet)
router.register(r'issues', api_views.IssueBookViewSet)
router.register(r'reservations', api_views.ReservationViewSet)
router.register(r'authors', api_views.AuthorViewSet)
router.register(r'categories', api_views.CategoryViewSet)
router.register(r'users', api_views.UserViewSet)

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('books/', views.book_list, name='book_list'),
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    path('add-book/', views.add_book, name='add_book'),
    path('edit-book/<int:pk>/', views.edit_book, name='edit_book'),
    path('issue/<int:pk>/', views.issue_book, name='issue_book'),
    path('return/<int:pk>/', views.return_book, name='return_book'),
    path('reserve/<int:pk>/', views.reserve_book, name='reserve_book'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('accounts/profile/', profile_view, name='profile'),

    # API URLs
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]