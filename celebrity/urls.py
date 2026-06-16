from django.urls import path
from . import views

app_name = 'celebrity'

urlpatterns = [
    path('', views.CelebrityHomeView.as_view(), name='home'),
    path('teams/', views.CelebrityTeamsView.as_view(), name='teams'),
    path('sponsors/', views.CelebritySponsorsView.as_view(), name='sponsors'),
    path('analytics/', views.CelebrityAnalyticsView.as_view(), name='analytics'),
    path('verification/', views.CelebrityVerificationView.as_view(), name='verification'),
]
