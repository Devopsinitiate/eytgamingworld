from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils import timezone
from django.conf import settings
from .models import Player, Game, Video, NewsArticle, Product


class LandingPageView(TemplateView):
    """
    Landing page view with context data for the redesigned EYTGaming homepage.
    
    Provides featured players, games, videos, news articles, and products
    for display on the landing page. Optimizes queries with select_related
    and prefetch_related for performance.
    
    Requirements: 15.2
    """
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Featured players (top 8) - optimized with select_related for game
        context['players'] = Player.objects.filter(
            is_featured=True
        ).select_related('game').order_by('display_order', '-kd_ratio')[:8]
        
        # Supported games - ordered by display_order
        context['games'] = Game.objects.filter(
            is_active=True
        ).order_by('display_order', 'name')
        
        # Featured video (first featured video)
        featured_video = Video.objects.filter(
            is_featured=True,
            is_published=True
        ).select_related('game').first()
        
        context['featured_video'] = featured_video
        
        # Highlight videos (recent published videos, excluding featured)
        highlight_videos_query = Video.objects.filter(
            is_published=True
        ).select_related('game').order_by('-published_date')
        
        # Exclude featured video if it exists
        if featured_video:
            highlight_videos_query = highlight_videos_query.exclude(id=featured_video.id)
        
        context['highlight_videos'] = highlight_videos_query[:6]
        
        # Recent news articles (top 6)
        context['news_articles'] = NewsArticle.objects.filter(
            is_published=True
        ).select_related('author').order_by('-published_date')[:6]
        
        # Featured products (top 4)
        context['featured_products'] = Product.objects.filter(
            is_featured=True,
            is_available=True
        ).order_by('display_order', 'name')[:4]
        
        # Social media URLs from settings
        context['discord_url'] = getattr(settings, 'DISCORD_URL', '#')
        context['twitter_url'] = getattr(settings, 'TWITTER_URL', '#')
        context['twitch_url'] = getattr(settings, 'TWITCH_URL', '#')
        context['youtube_url'] = getattr(settings, 'YOUTUBE_URL', '#')
        
        # Current year for copyright
        context['current_year'] = timezone.now().year
        
        return context

