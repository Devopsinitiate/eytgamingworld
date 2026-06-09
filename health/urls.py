from django.urls import path
from . import views
from . import metrics

urlpatterns = [
    path('', views.health_check, name='health'),
    path('db/', views.health_db, name='health-db'),
    path('cache/', views.health_cache, name='health-cache'),
    path('redis/', views.health_redis, name='health-redis'),
    path('ready/', views.health_ready, name='health-ready'),
    path('live/', views.health_live, name='health-live'),
    path('metrics/', metrics.prometheus_metrics, name='prometheus-metrics'),
]
