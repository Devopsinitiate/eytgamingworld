from django.urls import path
from django.views.generic import TemplateView

app_name = 'accounts'

urlpatterns = [
    # Temporary placeholder views - to be implemented
    path('profile/', TemplateView.as_view(template_name='coming_soon.html'), name='profile'),
    path('settings/', TemplateView.as_view(template_name='coming_soon.html'), name='settings'),
]
