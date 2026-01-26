from django.urls import path
from django.views.generic import TemplateView

app_name = 'venues'

urlpatterns = [
    # Temporary placeholder views - to be implemented
    path('', TemplateView.as_view(template_name='coming_soon.html'), name='list'),
    path('<uuid:pk>/', TemplateView.as_view(template_name='coming_soon.html'), name='detail'),
]
