from django.urls import path
from . import views, performance_views

app_name = 'core'

urlpatterns = [
    # Performance monitoring endpoint
    path('api/performance/', performance_views.PerformanceAPIView.as_view(), name='performance_data'),
    # Leaderboard - public
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    # News detail
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
    # Player directory - public
    path('players/', views.player_directory, name='player_directory'),
]
