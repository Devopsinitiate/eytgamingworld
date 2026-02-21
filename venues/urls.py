from django.urls import path
from . import views

app_name = 'venues'

urlpatterns = [
    # Venue browsing
    path('', views.VenueListView.as_view(), name='list'),
    
    # Booking management (must come before venue detail to avoid slug conflict)
    path('bookings/', views.BookingListView.as_view(), name='booking_list'),
    path('bookings/<uuid:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('bookings/<uuid:pk>/cancel/', views.BookingCancelView.as_view(), name='booking_cancel'),
    
    # Venue detail and booking (slug patterns last)
    path('<slug:slug>/', views.VenueDetailView.as_view(), name='detail'),
    path('<slug:slug>/book/', views.BookingCreateView.as_view(), name='booking_create'),
]
