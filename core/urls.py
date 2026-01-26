from django.urls import path
from . import views, performance_views

app_name = 'core'

urlpatterns = [
    # Performance monitoring endpoint
    path('api/performance/', performance_views.PerformanceAPIView.as_view(), name='performance_data'),
    # Add other core URLs here as needed
]
