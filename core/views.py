from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.utils import timezone
from django.conf import settings
from django.db.models import Count, Q
from django.core.paginator import Paginator
from .models import Player, Game, Video, NewsArticle, Product, User, UserGameProfile
from tournaments.models import Tournament
from coaching.models import CoachProfile
from venues.models import Venue


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
        
        # Supported games - ordered by display_order, annotate public tournament count
        context['games'] = Game.objects.filter(
            is_active=True
        ).annotate(
            tournament_count=Count('tournaments', filter=Q(tournaments__is_public=True), distinct=True)
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
        
        # Featured products (top 8 — slideshow needs more items than visible slots)
        context['featured_products'] = Product.objects.filter(
            is_featured=True,
            is_available=True
        ).order_by('display_order', 'name')[:8]

        # Live / upcoming tournaments
        context['home_tournaments'] = Tournament.objects.filter(
            is_public=True,
            status__in=['registration', 'check_in', 'in_progress']
        ).select_related('game').order_by('start_datetime')[:6]

        # Top coaches
        context['home_coaches'] = CoachProfile.objects.filter(
            status='active',
            accepting_students=True,
        ).select_related('user').prefetch_related('user__game_profiles__game').order_by(
            '-average_rating', '-total_sessions'
        )[:6]

        # Featured venues
        context['home_venues'] = Venue.objects.filter(
            is_active=True,
            is_verified=True,
        ).order_by('name')[:6]
        
        # Social media URLs from settings
        context['discord_url'] = getattr(settings, 'DISCORD_URL', '#')
        context['twitter_url'] = getattr(settings, 'TWITTER_URL', '#')
        context['twitch_url'] = getattr(settings, 'TWITCH_URL', '#')
        context['youtube_url'] = getattr(settings, 'YOUTUBE_URL', '#')
        
        # Current year for copyright
        context['current_year'] = timezone.now().year
        
        return context



def leaderboard(request):
    """Public leaderboard page — tournaments, top players, prize winners"""
    from django.db.models import Sum, Count, Q
    from tournaments.models import Tournament, Participant

    # Active & upcoming tournaments
    active_tournaments = Tournament.objects.filter(
        is_public=True,
        status__in=['registration', 'check_in', 'in_progress']
    ).select_related('game', 'organizer').order_by('start_datetime')[:8]

    # Recently completed tournaments
    completed_tournaments = Tournament.objects.filter(
        is_public=True,
        status='completed'
    ).select_related('game', 'organizer').order_by('-actual_end', '-start_datetime')[:6]

    # Top individual players by wins across all tournaments
    top_players = Participant.objects.filter(
        user__isnull=False,
        status='confirmed',
        tournament__is_public=True,
    ).values(
        'user__id', 'user__username', 'user__display_name', 'user__avatar'
    ).annotate(
        total_wins=Sum('matches_won'),
        total_losses=Sum('matches_lost'),
        tournaments_played=Count('tournament', distinct=True),
        total_prize=Sum('prize_won'),
    ).filter(total_wins__gt=0).order_by('-total_wins', '-tournaments_played')[:20]

    # Top teams by wins
    top_teams = Participant.objects.filter(
        team__isnull=False,
        status='confirmed',
        tournament__is_public=True,
    ).values(
        'team__id', 'team__name', 'team__tag', 'team__logo'
    ).annotate(
        total_wins=Sum('matches_won'),
        total_losses=Sum('matches_lost'),
        tournaments_played=Count('tournament', distinct=True),
        total_prize=Sum('prize_won'),
    ).filter(total_wins__gt=0).order_by('-total_wins', '-tournaments_played')[:20]

    # Prize winners (participants with prize > 0)
    prize_winners = Participant.objects.filter(
        prize_won__gt=0,
        tournament__is_public=True,
    ).select_related(
        'user', 'team', 'tournament', 'tournament__game'
    ).order_by('-prize_won')[:10]

    # Featured tournaments
    featured = Tournament.objects.filter(
        is_public=True,
        is_featured=True,
        status__in=['registration', 'check_in', 'in_progress', 'completed']
    ).select_related('game').order_by('-start_datetime')[:3]

    # Games with tournaments
    games = Game.objects.filter(
        tournaments__is_public=True
    ).distinct().order_by('name')

    return render(request, 'leaderboard.html', {
        'active_tournaments': active_tournaments,
        'completed_tournaments': completed_tournaments,
        'top_players': top_players,
        'top_teams': top_teams,
        'prize_winners': prize_winners,
        'featured': featured,
        'games': games,
    })


def news_detail(request, slug):
    """News article detail page"""
    article = get_object_or_404(NewsArticle, slug=slug, is_published=True)
    # Related articles — same category, excluding current
    related = NewsArticle.objects.filter(
        is_published=True,
        category=article.category
    ).exclude(pk=article.pk).order_by('-published_date')[:3]
    return render(request, 'news/detail.html', {
        'article': article,
        'related': related,
    })


def player_directory(request):
    """
    Public player directory — browse all registered users.
    Supports search by username/display name and filter by game/skill level.
    No login required.
    """
    from django.core.paginator import Paginator

    qs = User.objects.filter(
        is_active=True,
        private_profile=False,
    ).exclude(
        username=''
    ).prefetch_related('game_profiles__game').order_by('-total_points', 'username')

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(username__icontains=q) |
            Q(display_name__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        ).distinct()

    # Filter by game slug
    game_slug = request.GET.get('game', '').strip()
    if game_slug:
        qs = qs.filter(game_profiles__game__slug=game_slug).distinct()

    # Filter by skill level
    skill = request.GET.get('skill', '').strip()
    if skill:
        qs = qs.filter(skill_level=skill)

    # Pagination — 24 per page
    paginator = Paginator(qs, 24)
    page = request.GET.get('page', 1)
    players_page = paginator.get_page(page)

    games = Game.objects.filter(is_active=True).order_by('name')

    skill_choices = User.SKILL_LEVEL_CHOICES

    return render(request, 'players/directory.html', {
        'players_page': players_page,
        'games': games,
        'skill_choices': skill_choices,
        'q': q,
        'game_slug': game_slug,
        'skill': skill,
        'total_count': paginator.count,
    })
