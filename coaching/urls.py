from django.urls import path
from . import views

app_name = 'coaching'

urlpatterns = [
    # Coach listing & profiles
    path('', views.CoachListView.as_view(), name='coach_list'),
    path('coach/<uuid:pk>/', views.CoachDetailView.as_view(), name='coach_detail'),
    path('become-coach/', views.CoachProfileCreateView.as_view(), name='become_coach'),
    path('coach/<uuid:pk>/edit/', views.CoachProfileUpdateView.as_view(), name='coach_edit'),
    
    # Booking
    path('coach/<uuid:coach_pk>/book/', views.book_session, name='book_session'),
    path('session/<uuid:pk>/payment/', views.session_payment, name='session_payment'),
    path('session/<uuid:pk>/confirm-payment/', views.confirm_payment, name='confirm_payment'),
    
    # Session management
    path('sessions/', views.SessionListView.as_view(), name='session_list'),
    path('session/<uuid:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('session/<uuid:pk>/cancel/', views.cancel_session, name='cancel_session'),
    path('session/<uuid:pk>/start/', views.start_session, name='start_session'),
    path('session/<uuid:pk>/complete/', views.complete_session, name='complete_session'),
    
    # Reviews
    path('session/<uuid:pk>/review/', views.review_session, name='review_session'),
    
    # Packages
    path('packages/', views.PackageListView.as_view(), name='package_list'),
    path('package/<uuid:pk>/purchase/', views.purchase_package, name='purchase_package'),
    
    # API endpoints
    path('api/coach/<uuid:coach_pk>/slots/', views.get_available_slots, name='available_slots'),
]