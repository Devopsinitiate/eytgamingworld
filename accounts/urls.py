from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Temporary placeholder views - to be implemented
    path('profile/', TemplateView.as_view(template_name='coming_soon.html'), name='profile'),
    path('settings/', TemplateView.as_view(template_name='coming_soon.html'), name='settings'),
    # Become an Organizer
    path('become-organizer/', views.become_organizer, name='become_organizer'),
]
