"""
Dashboard Views

Performance Optimizations (Task 23.1):
- Use select_related() for foreign key relationships to reduce database queries
- Use prefetch_related() for many-to-many and reverse foreign key relationships
- Activity model has indexes on (user, created_at) and (activity_type, created_at)
- Participant queries use select_related for tournament, game, organizer, venue, and team
- Team queries use select_related for team, game, captain and prefetch_related for members
- All optimizations follow Django best practices for query optimization
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from datetime import timedelta
from PIL import Image
import io
import json
from tournaments.models import Tournament, Participant, Match
from coaching.models import CoachingSession
from notifications.models import Notification
from teams.models import TeamMember, Team, TeamInvite
from core.models import User, UserGameProfile
from dashboard.models import UserAchievement, ProfileCompleteness
from dashboard.forms import (
    ProfileEditForm, 
    AvatarUploadForm, 
    BannerUploadForm, 
    GameProfileForm,
    PrivacySettingsForm,
    AccountDeleteForm,
    UserReportForm
)
from dashboard.services import (
    StatisticsService,
    ActivityService,
    RecommendationService,
    PaymentSummaryService,
    PrivacyService,
    ProfileExportService
)
from security.models import AuditLog


@login_required
def dashboard_home(request):
    """
    Main dashboard view for authenticated users.
    
    Displays personalized dashboard with:
    - Statistics cards (tournaments, win rate, teams, notifications)
    - Recent activity feed (last 10 activities)
    - Upcoming events (7-day window)
    - Tournament recommendations (top 3)
    - Payment summary
    - Quick actions
    
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 12.1**
    """
    
    # Get user statistics using StatisticsService
    try:
        user_stats = StatisticsService.get_user_statistics(request.user.id)
    except Exception as e:
        user_stats = {
            'total_tournaments': 0,
            'total_matches': 0,
            'matches_won': 0,
            'matches_lost': 0,
            'win_rate': 0.0,
            'total_prize_won': 0,
            'top_3_finishes': 0,
            'average_placement': None,
        }
    
    # Get current teams count
    try:
        current_teams = TeamMember.objects.filter(
            user=request.user,
            status='active'
        ).count()
    except Exception as e:
        current_teams = 0
    
    # Get unread notifications count
    try:
        unread_notifications = Notification.objects.filter(
            user=request.user,
            read=False
        ).count()
    except Exception as e:
        unread_notifications = 0
    
    # Build statistics cards data
    stats = {
        'total_tournaments': user_stats['total_tournaments'],
        'win_rate': user_stats['win_rate'],
        'current_teams': current_teams,
        'unread_notifications': unread_notifications,
        'total_points': request.user.total_points,
        'level': request.user.level,
    }
    
    # Get recent activity feed (last 10 activities)
    try:
        activity_data = ActivityService.get_activity_feed(
            user_id=request.user.id,
            filters=None,
            page=1,
            page_size=10
        )
        recent_activities = activity_data['activities']
    except Exception as e:
        recent_activities = []
    
    # Get upcoming events (7-day window)
    # Optimized with select_related for foreign keys
    try:
        seven_days_from_now = timezone.now() + timedelta(days=7)
        upcoming_tournaments = Tournament.objects.filter(
            start_datetime__gte=timezone.now(),
            start_datetime__lte=seven_days_from_now,
            status__in=['registration', 'draft', 'check_in']
        ).select_related('game', 'organizer', 'venue').order_by('start_datetime')[:5]
    except Exception as e:
        upcoming_tournaments = []
    
    # Get tournament recommendations (top 3)
    try:
        recommendations = RecommendationService.get_tournament_recommendations(
            user_id=request.user.id,
            limit=3
        )
    except Exception as e:
        recommendations = []
    
    # Get payment summary
    try:
        payment_summary = PaymentSummaryService.get_payment_summary(request.user.id)
    except Exception as e:
        payment_summary = {
            'total_spent': 0,
            'recent_payments_count': 0,
            'saved_payment_methods_count': 0,
            'has_default_method': False,
            'recent_payments': [],
        }
    
    # Legacy data for backward compatibility with existing templates
    try:
        user_tournaments = Participant.objects.filter(
            user=request.user
        ).select_related('tournament', 'tournament__game').order_by('-created_at')[:5]
    except Exception as e:
        user_tournaments = []
    
    try:
        upcoming_sessions = CoachingSession.objects.filter(
            student=request.user,
            scheduled_time__gte=timezone.now(),
            status='confirmed'
        ).select_related('coach', 'game').order_by('scheduled_time')[:5]
    except Exception as e:
        upcoming_sessions = []
    
    try:
        recent_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
    except Exception as e:
        recent_notifications = []
    
    context = {
        # New dashboard data
        'stats': stats,
        'recent_activities': recent_activities,
        'upcoming_tournaments': upcoming_tournaments,
        'recommendations': recommendations,
        'payment_summary': payment_summary,
        
        # Legacy data for backward compatibility
        'user_tournaments': user_tournaments,
        'upcoming_sessions': upcoming_sessions,
        'recent_notifications': recent_notifications,
    }
    
    return render(request, 'dashboard/home.html', context)



@login_required
def dashboard_activity(request):
    """
    Activity feed view with filtering and pagination.
    
    Displays user's activity feed with optional filters:
    - activity_type: Filter by activity type
    - date_range: Filter by date range (7d, 30d, 90d, all)
    
    Implements pagination with 25 activities per page.
    
    **Validates: Requirements 8.3, 8.5**
    """
    
    # Get filter parameters from request
    activity_type = request.GET.get('activity_type', '')
    date_range = request.GET.get('date_range', 'all')
    page = request.GET.get('page', 1)
    
    # Convert page to integer
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    
    # Build filters dictionary
    filters = {}
    
    # Filter by activity type
    if activity_type:
        filters['activity_type'] = activity_type
    
    # Filter by date range
    if date_range != 'all':
        now = timezone.now()
        if date_range == '7d':
            filters['date_from'] = now - timedelta(days=7)
        elif date_range == '30d':
            filters['date_from'] = now - timedelta(days=30)
        elif date_range == '90d':
            filters['date_from'] = now - timedelta(days=90)
    
    # Get activity feed with filters and pagination
    try:
        activity_data = ActivityService.get_activity_feed(
            user_id=request.user.id,
            filters=filters,
            page=page,
            page_size=25
        )
    except Exception as e:
        activity_data = {
            'activities': [],
            'total_count': 0,
            'page': 1,
            'page_size': 25,
            'total_pages': 0,
            'has_next': False,
            'has_previous': False,
        }
    
    # Get available activity types for filter dropdown
    activity_types = ActivityService.get_activity_types()
    
    context = {
        'activities': activity_data['activities'],
        'total_count': activity_data['total_count'],
        'page': activity_data['page'],
        'page_size': activity_data['page_size'],
        'total_pages': activity_data['total_pages'],
        'has_next': activity_data['has_next'],
        'has_previous': activity_data['has_previous'],
        'activity_types': activity_types,
        'selected_activity_type': activity_type,
        'selected_date_range': date_range,
    }
    
    return render(request, 'dashboard/activity.html', context)



@login_required
def dashboard_stats(request):
    """
    Detailed statistics view with performance trends.
    
    Displays:
    - User statistics (tournaments, win rate, etc.)
    - Performance trend over last 30 days
    - Data formatted for Chart.js visualization
    
    **Validates: Requirements 3.4**
    """
    
    # Get user statistics
    try:
        user_stats = StatisticsService.get_user_statistics(request.user.id)
    except Exception as e:
        user_stats = {
            'total_tournaments': 0,
            'total_matches': 0,
            'matches_won': 0,
            'matches_lost': 0,
            'win_rate': 0.0,
            'total_prize_won': 0,
            'top_3_finishes': 0,
            'average_placement': None,
        }
    
    # Get performance trend (last 30 days)
    try:
        performance_trend = StatisticsService.get_performance_trend(
            user_id=request.user.id,
            days=30
        )
    except Exception as e:
        performance_trend = []
    
    # Format trend data for Chart.js
    # Extract dates and win rates for chart
    chart_labels = [item['date'] for item in performance_trend]
    chart_data = [item['win_rate'] for item in performance_trend]
    
    context = {
        'user_stats': user_stats,
        'performance_trend': performance_trend,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    
    return render(request, 'dashboard/stats.html', context)


@login_required
def dashboard_payment_summary(request):
    """
    Payment summary view for dashboard.
    
    Displays:
    - Total spent
    - Recent payments (last 5)
    - Saved payment methods count
    - Default payment method status
    
    Returns JSON response for AJAX requests or renders template.
    
    **Validates: Requirements 12.1, 12.2, 12.3**
    """
    
    # Get payment summary using PaymentSummaryService
    try:
        payment_summary = PaymentSummaryService.get_payment_summary(request.user.id)
    except Exception as e:
        payment_summary = {
            'total_spent': 0,
            'recent_payments_count': 0,
            'saved_payment_methods_count': 0,
            'has_default_method': False,
            'recent_payments': [],
        }
    
    # If AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(payment_summary)
    
    # Otherwise render template
    context = {
        'payment_summary': payment_summary,
    }
    
    return render(request, 'dashboard/payment_summary.html', context)


@login_required
def profile_view(request, username):
    """
    View user profile with privacy controls.
    
    Displays user profile information with respect to privacy settings:
    - Basic information (username, avatar, bio) always visible
    - Statistics visible only if viewer has permission
    - Activity feed visible only if viewer has permission
    - Achievements showcase always visible
    
    Args:
        request: HTTP request object
        username: Username of the profile to view
        
    **Validates: Requirements 2.1, 10.1, 10.2, 10.5**
    """
    # Get the profile owner
    profile_owner = get_object_or_404(User, username=username)
    
    # Check if viewer can view this profile
    can_view = PrivacyService.can_view_profile(request.user, profile_owner)
    
    if not can_view:
        # For private profiles, show limited information
        context = {
            'profile_owner': profile_owner,
            'is_own_profile': request.user.id == profile_owner.id,
            'can_view_statistics': False,
            'can_view_activity': False,
            'is_private': True,
        }
        return render(request, 'dashboard/profile_view.html', context)
    
    # Check specific permissions
    can_view_statistics = PrivacyService.can_view_statistics(request.user, profile_owner)
    can_view_activity = PrivacyService.can_view_activity(request.user, profile_owner)
    
    # Load game profiles with optimized query
    game_profiles = UserGameProfile.objects.filter(
        user=profile_owner
    ).select_related('game').order_by('-is_main_game', '-skill_rating')
    
    # Load statistics if viewer has permission
    user_stats = None
    if can_view_statistics:
        try:
            user_stats = StatisticsService.get_user_statistics(profile_owner.id)
        except Exception as e:
            user_stats = None
    
    # Load activity feed if viewer has permission
    recent_activities = []
    if can_view_activity:
        try:
            activity_data = ActivityService.get_activity_feed(
                user_id=profile_owner.id,
                filters=None,
                page=1,
                page_size=10
            )
            recent_activities = activity_data['activities']
        except Exception as e:
            recent_activities = []
    
    # Load achievements showcase (always visible)
    showcase_achievements = UserAchievement.objects.filter(
        user=profile_owner,
        in_showcase=True,
        is_completed=True
    ).select_related('achievement').order_by('showcase_order')[:6]
    
    # Build context
    context = {
        'profile_owner': profile_owner,
        'is_own_profile': request.user.id == profile_owner.id,
        'can_view_statistics': can_view_statistics,
        'can_view_activity': can_view_activity,
        'is_private': False,
        'game_profiles': game_profiles,
        'user_stats': user_stats,
        'recent_activities': recent_activities,
        'showcase_achievements': showcase_achievements,
    }
    
    return render(request, 'dashboard/profile_view.html', context)



@login_required
def profile_edit(request):
    """
    Edit user profile with avatar and banner upload handling.
    
    Handles:
    - Profile information updates
    - Avatar upload with resize to 400x400
    - Banner upload with resize to 1920x400
    - File size validation (2MB for avatar, 5MB for banner)
    - Profile completeness recalculation
    - Activity recording
    
    **Validates: Requirements 2.2, 2.3, 2.4**
    """
    user = request.user
    
    # Initialize forms with default values
    profile_form = ProfileEditForm(instance=user)
    avatar_form = AvatarUploadForm()
    banner_form = BannerUploadForm()
    
    if request.method == 'POST':
        # Determine which form was submitted
        if 'avatar' in request.FILES:
            # Avatar upload
            avatar_form = AvatarUploadForm(request.POST, request.FILES)
            if avatar_form.is_valid():
                avatar_file = avatar_form.cleaned_data['avatar']
                
                try:
                    # Open and resize image to 400x400
                    img = Image.open(avatar_file)
                    
                    # Convert RGBA to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    
                    # Resize to 400x400
                    img = img.resize((400, 400), Image.Resampling.LANCZOS)
                    
                    # Save to BytesIO
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=90)
                    output.seek(0)
                    
                    # Save to user model
                    from django.core.files.uploadedfile import InMemoryUploadedFile
                    user.avatar.save(
                        f'avatar_{user.id}.jpg',
                        InMemoryUploadedFile(
                            output,
                            'ImageField',
                            f'avatar_{user.id}.jpg',
                            'image/jpeg',
                            output.getbuffer().nbytes,
                            None
                        ),
                        save=True
                    )
                    
                    # Record activity
                    ActivityService.record_activity(
                        user_id=user.id,
                        activity_type='profile_updated',
                        data={'field': 'avatar'}
                    )
                    
                    # Recalculate profile completeness
                    ProfileCompleteness.calculate_for_user(user)
                    
                    messages.success(request, 'Avatar updated successfully!')
                    return redirect('dashboard:profile_edit')
                    
                except Exception as e:
                    messages.error(request, f'Error processing avatar: {str(e)}')
            else:
                for error in avatar_form.errors.get('avatar', []):
                    messages.error(request, error)
        
        elif 'banner' in request.FILES:
            # Banner upload
            banner_form = BannerUploadForm(request.POST, request.FILES)
            if banner_form.is_valid():
                banner_file = banner_form.cleaned_data['banner']
                
                try:
                    # Open and resize image to 1920x400
                    img = Image.open(banner_file)
                    
                    # Convert RGBA to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    
                    # Resize to 1920x400
                    img = img.resize((1920, 400), Image.Resampling.LANCZOS)
                    
                    # Save to BytesIO
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=90)
                    output.seek(0)
                    
                    # Save to user model
                    from django.core.files.uploadedfile import InMemoryUploadedFile
                    user.banner.save(
                        f'banner_{user.id}.jpg',
                        InMemoryUploadedFile(
                            output,
                            'ImageField',
                            f'banner_{user.id}.jpg',
                            'image/jpeg',
                            output.getbuffer().nbytes,
                            None
                        ),
                        save=True
                    )
                    
                    # Record activity
                    ActivityService.record_activity(
                        user_id=user.id,
                        activity_type='profile_updated',
                        data={'field': 'banner'}
                    )
                    
                    # Recalculate profile completeness
                    ProfileCompleteness.calculate_for_user(user)
                    
                    messages.success(request, 'Banner updated successfully!')
                    return redirect('dashboard:profile_edit')
                    
                except Exception as e:
                    messages.error(request, f'Error processing banner: {str(e)}')
            else:
                for error in banner_form.errors.get('banner', []):
                    messages.error(request, error)
        
        else:
            # Profile information update
            profile_form = ProfileEditForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                
                # Record activity
                ActivityService.record_activity(
                    user_id=user.id,
                    activity_type='profile_updated',
                    data={'fields': list(profile_form.changed_data)}
                )
                
                # Recalculate profile completeness
                ProfileCompleteness.calculate_for_user(user)
                
                messages.success(request, 'Profile updated successfully!')
                return redirect('dashboard:profile_edit')
            else:
                for field, errors in profile_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    
    # Get profile completeness
    try:
        completeness = ProfileCompleteness.objects.get(user=user)
    except ProfileCompleteness.DoesNotExist:
        completeness = ProfileCompleteness.calculate_for_user(user)
    
    context = {
        'profile_form': profile_form,
        'avatar_form': avatar_form,
        'banner_form': banner_form,
        'completeness': completeness,
    }
    
    return render(request, 'dashboard/profile_edit.html', context)



@login_required
def profile_export(request):
    """
    Export user profile data as JSON.
    
    Generates a comprehensive JSON export of user data including:
    - Profile information
    - Game profiles
    - Tournament history
    - Team memberships
    - Payment history (amounts only, no payment method details)
    - Activity history
    - Achievements
    
    Creates an audit log entry with timestamp and IP address.
    Returns JSON file with filename format: {username}_profile_{date}.json
    
    **Validates: Requirements 17.1, 17.3, 17.4**
    """
    user = request.user
    
    try:
        # Generate export data
        export_data = ProfileExportService.generate_export(user.id)
        
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Create audit log entry
        AuditLog.log_action(
            user=user,
            action='export',
            model_name='User',
            object_id=str(user.id),
            description=f'User data export generated from IP {ip_address}',
            severity='medium',
            details={
                'ip_address': ip_address,
                'timestamp': timezone.now().isoformat(),
                'export_sections': list(export_data.keys()),
            }
        )
        
        # Generate filename with username and date
        filename = f"{user.username}_profile_{timezone.now().strftime('%Y%m%d')}.json"
        
        # Create JSON response with download headers
        response = JsonResponse(export_data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating export: {str(e)}')
        return redirect('dashboard:home')



@login_required
def game_profile_list(request):
    """
    List user's game profiles.
    
    Displays all game profiles for the authenticated user,
    sorted by main game first, then by skill rating descending.
    
    Optimized with select_related for game foreign key.
    
    **Validates: Requirements 4.1, 4.5**
    """
    game_profiles = UserGameProfile.objects.filter(
        user=request.user
    ).select_related('game').order_by('-is_main_game', '-skill_rating')
    
    context = {
        'game_profiles': game_profiles,
    }
    
    return render(request, 'dashboard/game_profiles_list.html', context)


@login_required
def game_profile_create(request):
    """
    Create a new game profile.
    
    Handles game profile creation with validation:
    - Prevents duplicate game profiles
    - Validates skill rating range (0-5000)
    - Handles main game setting (unsets previous main if new one is set)
    - Records activity
    - Recalculates profile completeness
    
    **Validates: Requirements 4.1, 4.2**
    """
    if request.method == 'POST':
        form = GameProfileForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                game_profile = form.save(commit=False)
                game_profile.user = request.user
                
                # If this is being set as main game, unset any previous main game
                if game_profile.is_main_game:
                    UserGameProfile.objects.filter(
                        user=request.user,
                        is_main_game=True
                    ).update(is_main_game=False)
                
                game_profile.save()
                
                # Record activity
                ActivityService.record_activity(
                    user_id=request.user.id,
                    activity_type='game_profile_added',
                    data={
                        'game': game_profile.game.name,
                        'in_game_name': game_profile.in_game_name
                    }
                )
                
                # Recalculate profile completeness
                ProfileCompleteness.calculate_for_user(request.user)
                
                messages.success(request, f'Game profile for {game_profile.game.name} created successfully!')
                return redirect('dashboard:game_profile_list')
            except Exception as e:
                # Handle database integrity errors (e.g., duplicate game profile)
                messages.error(request, 'You already have a profile for this game.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = GameProfileForm(user=request.user)
    
    context = {
        'form': form,
        'action': 'Create',
    }
    
    return render(request, 'dashboard/game_profile_form.html', context)


@login_required
def game_profile_edit(request, profile_id):
    """
    Edit an existing game profile.
    
    Handles game profile updates with ownership check:
    - Ensures user owns the profile
    - Validates skill rating range
    - Handles main game setting
    - Records activity
    - Recalculates profile completeness
    
    **Validates: Requirements 4.3**
    """
    game_profile = get_object_or_404(
        UserGameProfile,
        id=profile_id,
        user=request.user  # Ownership check
    )
    
    if request.method == 'POST':
        form = GameProfileForm(request.POST, instance=game_profile, user=request.user)
        if form.is_valid():
            game_profile = form.save(commit=False)
            
            # If this is being set as main game, unset any previous main game
            if game_profile.is_main_game:
                UserGameProfile.objects.filter(
                    user=request.user,
                    is_main_game=True
                ).exclude(id=game_profile.id).update(is_main_game=False)
            
            game_profile.save()
            
            # Record activity
            ActivityService.record_activity(
                user_id=request.user.id,
                activity_type='profile_updated',
                data={
                    'field': 'game_profile',
                    'game': game_profile.game.name
                }
            )
            
            # Recalculate profile completeness
            ProfileCompleteness.calculate_for_user(request.user)
            
            messages.success(request, f'Game profile for {game_profile.game.name} updated successfully!')
            return redirect('dashboard:game_profile_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = GameProfileForm(instance=game_profile, user=request.user)
    
    context = {
        'form': form,
        'game_profile': game_profile,
        'action': 'Edit',
    }
    
    return render(request, 'dashboard/game_profile_form.html', context)


@login_required
def game_profile_delete(request, profile_id):
    """
    Delete a game profile.
    
    Handles game profile deletion with protection:
    - Ensures user owns the profile
    - Checks for tournament participations before deletion
    - Prevents deletion if user has participated in tournaments with this game
    - Records activity
    - Recalculates profile completeness
    
    **Validates: Requirements 4.4**
    """
    game_profile = get_object_or_404(
        UserGameProfile,
        id=profile_id,
        user=request.user  # Ownership check
    )
    
    if request.method == 'POST':
        # Check if user has tournament participations with this game
        has_tournament_history = Participant.objects.filter(
            user=request.user,
            tournament__game=game_profile.game
        ).exists()
        
        if has_tournament_history:
            messages.error(
                request,
                f'Cannot delete game profile for {game_profile.game.name} because you have tournament history with this game.'
            )
            return redirect('dashboard:game_profile_list')
        
        # Safe to delete
        game_name = game_profile.game.name
        game_profile.delete()
        
        # Record activity
        ActivityService.record_activity(
            user_id=request.user.id,
            activity_type='profile_updated',
            data={
                'field': 'game_profile_deleted',
                'game': game_name
            }
        )
        
        # Recalculate profile completeness
        ProfileCompleteness.calculate_for_user(request.user)
        
        messages.success(request, f'Game profile for {game_name} deleted successfully!')
        return redirect('dashboard:game_profile_list')
    
    context = {
        'game_profile': game_profile,
    }
    
    return render(request, 'dashboard/game_profile_confirm_delete.html', context)


@login_required
def game_profile_set_main(request, profile_id):
    """
    Set a game profile as the main game.
    
    Handles main game setting:
    - Ensures user owns the profile
    - Unsets any previous main game
    - Sets the selected profile as main
    - Records activity
    
    **Validates: Requirements 4.2**
    """
    game_profile = get_object_or_404(
        UserGameProfile,
        id=profile_id,
        user=request.user  # Ownership check
    )
    
    # Unset any previous main game
    UserGameProfile.objects.filter(
        user=request.user,
        is_main_game=True
    ).update(is_main_game=False)
    
    # Set this profile as main
    game_profile.is_main_game = True
    game_profile.save(update_fields=['is_main_game'])
    
    # Record activity
    ActivityService.record_activity(
        user_id=request.user.id,
        activity_type='profile_updated',
        data={
            'field': 'main_game',
            'game': game_profile.game.name
        }
    )
    
    messages.success(request, f'{game_profile.game.name} set as your main game!')
    return redirect('dashboard:game_profile_list')


@login_required
def tournament_history(request):
    """
    Display user's tournament history with filtering and pagination.
    
    Displays all tournaments the user has participated in with:
    - Filtering by game, date range, and placement
    - Pagination (20 tournaments per page)
    - Optimized queries with select_related for tournament, game, and organizer
    
    **Validates: Requirements 5.1, 5.2, 5.5**
    **Performance: Requirements 16.4**
    """
    # Base queryset - all user's tournament participations
    # Optimized with select_related to reduce database queries
    participations = Participant.objects.filter(
        user=request.user
    ).select_related(
        'tournament',
        'tournament__game',
        'tournament__organizer',
        'tournament__venue',
        'team'
    ).order_by('-tournament__start_datetime')
    
    # Get filter parameters from request
    game_id = request.GET.get('game', '')
    date_range = request.GET.get('date_range', 'all')
    placement = request.GET.get('placement', '')
    
    # Apply game filter
    if game_id:
        try:
            from core.models import Game
            game = Game.objects.get(id=game_id)
            participations = participations.filter(tournament__game=game)
        except (Game.DoesNotExist, ValueError):
            pass
    
    # Apply date range filter
    if date_range != 'all':
        now = timezone.now()
        if date_range == '7d':
            date_from = now - timedelta(days=7)
            participations = participations.filter(tournament__start_datetime__gte=date_from)
        elif date_range == '30d':
            date_from = now - timedelta(days=30)
            participations = participations.filter(tournament__start_datetime__gte=date_from)
        elif date_range == '90d':
            date_from = now - timedelta(days=90)
            participations = participations.filter(tournament__start_datetime__gte=date_from)
        elif date_range == '1y':
            date_from = now - timedelta(days=365)
            participations = participations.filter(tournament__start_datetime__gte=date_from)
    
    # Apply placement filter
    if placement:
        if placement == 'top3':
            participations = participations.filter(final_placement__lte=3, final_placement__isnull=False)
        elif placement == 'winner':
            participations = participations.filter(final_placement=1)
        elif placement.isdigit():
            participations = participations.filter(final_placement=int(placement))
    
    # Pagination (20 per page)
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    paginator = Paginator(participations, 20)
    page = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Get all games for filter dropdown
    from core.models import Game
    user_games = Game.objects.filter(
        tournaments__participants__user=request.user
    ).distinct().order_by('name')
    
    # Calculate summary statistics
    total_tournaments = participations.count()
    top_3_finishes = participations.filter(final_placement__lte=3, final_placement__isnull=False).count()
    tournament_wins = participations.filter(final_placement=1).count()
    
    context = {
        'page_obj': page_obj,
        'participations': page_obj.object_list,
        'total_tournaments': total_tournaments,
        'top_3_finishes': top_3_finishes,
        'tournament_wins': tournament_wins,
        'user_games': user_games,
        'selected_game': game_id,
        'selected_date_range': date_range,
        'selected_placement': placement,
    }
    
    return render(request, 'dashboard/tournament_history.html', context)


@login_required
def tournament_detail_history(request, tournament_id):
    """
    Display detailed match history for a specific tournament.
    
    Shows:
    - All matches the user participated in for this tournament
    - Match results with scores
    - Opponents faced
    - Timestamps for each match
    
    **Validates: Requirements 5.3**
    """
    from tournaments.models import Match
    
    # Get the tournament and verify user participated
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    # Get user's participation record
    try:
        participation = Participant.objects.select_related(
            'tournament',
            'tournament__game'
        ).get(
            tournament=tournament,
            user=request.user
        )
    except Participant.DoesNotExist:
        messages.error(request, 'You did not participate in this tournament.')
        return redirect('dashboard:tournament_history')
    
    # Get all matches where user was a participant
    matches = Match.objects.filter(
        tournament=tournament
    ).filter(
        models.Q(participant1=participation) | models.Q(participant2=participation)
    ).select_related(
        'participant1',
        'participant1__user',
        'participant1__team',
        'participant2',
        'participant2__user',
        'participant2__team',
        'winner',
        'bracket'
    ).order_by('round_number', 'match_number')
    
    # Build match details with opponent information
    match_details = []
    for match in matches:
        # Determine opponent
        if match.participant1 == participation:
            opponent = match.participant2
            user_score = match.score_p1
            opponent_score = match.score_p2
        else:
            opponent = match.participant1
            user_score = match.score_p2
            opponent_score = match.score_p1
        
        # Determine result
        if match.winner == participation:
            result = 'won'
        elif match.winner:
            result = 'lost'
        else:
            result = 'pending'
        
        match_details.append({
            'match': match,
            'opponent': opponent,
            'opponent_name': opponent.display_name if opponent else 'BYE',
            'user_score': user_score,
            'opponent_score': opponent_score,
            'result': result,
            'round': match.round_number,
            'started_at': match.started_at,
            'completed_at': match.completed_at,
        })
    
    # Calculate match statistics
    total_matches = matches.count()
    matches_won = matches.filter(winner=participation).count()
    matches_lost = matches.filter(winner__isnull=False).exclude(winner=participation).count()
    
    context = {
        'tournament': tournament,
        'participation': participation,
        'match_details': match_details,
        'total_matches': total_matches,
        'matches_won': matches_won,
        'matches_lost': matches_lost,
    }
    
    return render(request, 'dashboard/tournament_detail_history.html', context)



@login_required
def team_membership(request):
    """
    Display user's team memberships and history.
    
    Displays:
    - Active team memberships with role and statistics
    - Team history (teams user has left)
    - Team statistics calculated from tournament participations
    - Pending team invitations
    
    **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
    """
    from django.db.models import Count, Q
    
    # Get active team memberships with optimized queries
    active_memberships = TeamMember.objects.filter(
        user=request.user,
        status='active'
    ).select_related(
        'team',
        'team__game',
        'team__captain'
    ).prefetch_related(
        'team__members'
    ).order_by('-joined_at')
    
    # Get team history (left teams) with optimized queries
    team_history = TeamMember.objects.filter(
        user=request.user,
        status__in=['inactive', 'removed']
    ).select_related(
        'team',
        'team__game'
    ).order_by('-left_at')
    
    # Calculate team statistics from tournament participations
    team_stats = []
    for membership in active_memberships:
        # Get tournament participations for this team
        team_participations = Participant.objects.filter(
            team=membership.team
        ).select_related('tournament')
        
        # Calculate statistics
        total_tournaments = team_participations.count()
        tournaments_won = team_participations.filter(final_placement=1).count()
        top_3_finishes = team_participations.filter(
            final_placement__lte=3,
            final_placement__isnull=False
        ).count()
        
        # Calculate total matches for this team
        team_matches = Match.objects.filter(
            Q(participant1__team=membership.team) | Q(participant2__team=membership.team),
            status='completed'
        ).count()
        
        # Calculate wins
        team_wins = Match.objects.filter(
            Q(participant1__team=membership.team, winner__team=membership.team) |
            Q(participant2__team=membership.team, winner__team=membership.team),
            status='completed'
        ).count()
        
        # Calculate win rate
        win_rate = 0
        if team_matches > 0:
            win_rate = round((team_wins / team_matches) * 100, 2)
        
        team_stats.append({
            'membership': membership,
            'total_tournaments': total_tournaments,
            'tournaments_won': tournaments_won,
            'top_3_finishes': top_3_finishes,
            'total_matches': team_matches,
            'matches_won': team_wins,
            'win_rate': win_rate,
        })
    
    # Get pending team invitations with optimized queries
    pending_invitations = TeamInvite.objects.filter(
        invited_user=request.user,
        status='pending',
        expires_at__gt=timezone.now()
    ).select_related(
        'team',
        'team__game',
        'invited_by',
        'team__captain'
    ).order_by('-created_at')
    
    # Calculate overall team statistics
    total_active_teams = active_memberships.count()
    total_teams_left = team_history.count()
    total_pending_invites = pending_invitations.count()
    
    # Calculate contributions across all teams
    total_team_tournaments = sum(stat['total_tournaments'] for stat in team_stats)
    total_team_wins = sum(stat['tournaments_won'] for stat in team_stats)
    
    context = {
        'active_memberships': active_memberships,
        'team_history': team_history,
        'team_stats': team_stats,
        'pending_invitations': pending_invitations,
        'total_active_teams': total_active_teams,
        'total_teams_left': total_teams_left,
        'total_pending_invites': total_pending_invites,
        'total_team_tournaments': total_team_tournaments,
        'total_team_wins': total_team_wins,
    }
    
    return render(request, 'dashboard/team_membership.html', context)



@login_required
def settings_profile(request):
    """
    Profile settings view.
    
    Allows users to edit basic profile information including avatar upload.
    This is a duplicate of profile_edit but in the settings section
    for better UX organization.
    
    **Validates: Requirements 9.1**
    """
    user = request.user
    
    if request.method == 'POST':
        profile_form = ProfileEditForm(request.POST, request.FILES, instance=user)
        if profile_form.is_valid():
            profile_form.save()
            
            # Record activity
            ActivityService.record_activity(
                user_id=user.id,
                activity_type='profile_updated',
                data={'fields': list(profile_form.changed_data)}
            )
            
            # Recalculate profile completeness
            ProfileCompleteness.calculate_for_user(user)
            
            messages.success(request, 'Profile settings updated successfully!')
            return redirect('dashboard:settings_profile')
        else:
            for field, errors in profile_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        profile_form = ProfileEditForm(instance=user)
    
    context = {
        'form': profile_form,
        'profile_form': profile_form,  # Keep for backward compatibility
        'active_tab': 'profile',
    }
    
    return render(request, 'dashboard/settings/profile.html', context)


@login_required
def settings_privacy(request):
    """
    Privacy settings view.
    
    Allows users to control visibility of their profile information:
    - Online status visibility
    - Activity feed visibility
    - Statistics visibility
    
    **Validates: Requirements 9.2**
    """
    user = request.user
    
    if request.method == 'POST':
        privacy_form = PrivacySettingsForm(request.POST, user=user)
        if privacy_form.is_valid():
            # Update user privacy settings
            user.online_status_visible = privacy_form.cleaned_data.get('online_status_visible', False)
            user.activity_visible = privacy_form.cleaned_data.get('activity_visible', False)
            user.statistics_visible = privacy_form.cleaned_data.get('statistics_visible', False)
            user.save(update_fields=['online_status_visible', 'activity_visible', 'statistics_visible'])
            
            # Record activity
            ActivityService.record_activity(
                user_id=user.id,
                activity_type='profile_updated',
                data={'field': 'privacy_settings'}
            )
            
            messages.success(request, 'Privacy settings updated successfully!')
            return redirect('dashboard:settings_privacy')
        else:
            for field, errors in privacy_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        privacy_form = PrivacySettingsForm(user=user)
    
    context = {
        'privacy_form': privacy_form,
        'active_tab': 'privacy',
    }
    
    return render(request, 'dashboard/settings/privacy.html', context)


@login_required
def settings_notifications(request):
    """
    Notification preferences view.
    
    Integrates with the notifications app to manage notification preferences.
    Redirects to the notifications preferences page.
    
    **Validates: Requirements 9.3**
    """
    from notifications.models import NotificationPreference
    
    # Get or create notification preferences
    prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update preferences
        prefs.in_app_enabled = request.POST.get('in_app_enabled') == 'on'
        prefs.email_enabled = request.POST.get('email_enabled') == 'on'
        prefs.push_enabled = request.POST.get('push_enabled') == 'on'
        prefs.discord_enabled = request.POST.get('discord_enabled') == 'on'
        
        # Email preferences
        prefs.email_tournament_updates = request.POST.get('email_tournament_updates') == 'on'
        prefs.email_team_activity = request.POST.get('email_team_activity') == 'on'
        prefs.email_payment_confirmations = request.POST.get('email_payment_confirmations') == 'on'
        prefs.email_coaching_reminders = request.POST.get('email_coaching_reminders') == 'on'
        prefs.email_marketing = request.POST.get('email_marketing') == 'on'
        
        # Push preferences
        prefs.push_tournament_updates = request.POST.get('push_tournament_updates') == 'on'
        prefs.push_team_activity = request.POST.get('push_team_activity') == 'on'
        prefs.push_payment_confirmations = request.POST.get('push_payment_confirmations') == 'on'
        prefs.push_coaching_reminders = request.POST.get('push_coaching_reminders') == 'on'
        
        # Quiet hours
        prefs.quiet_hours_enabled = request.POST.get('quiet_hours_enabled') == 'on'
        quiet_hours_start = request.POST.get('quiet_hours_start')
        quiet_hours_end = request.POST.get('quiet_hours_end')
        
        if quiet_hours_start:
            from datetime import time
            try:
                hour, minute = map(int, quiet_hours_start.split(':'))
                prefs.quiet_hours_start = time(hour, minute)
            except (ValueError, AttributeError):
                pass
        
        if quiet_hours_end:
            from datetime import time
            try:
                hour, minute = map(int, quiet_hours_end.split(':'))
                prefs.quiet_hours_end = time(hour, minute)
            except (ValueError, AttributeError):
                pass
        
        # Discord webhook
        prefs.discord_webhook_url = request.POST.get('discord_webhook_url', '')
        
        prefs.save()
        
        messages.success(request, 'Notification preferences updated successfully!')
        return redirect('dashboard:settings_notifications')
    
    context = {
        'prefs': prefs,
        'active_tab': 'notifications',
    }
    
    return render(request, 'dashboard/settings/notifications.html', context)


@login_required
def settings_security(request):
    """
    Security settings view.
    
    Allows users to change their password with current password verification.
    Uses Django's built-in PasswordChangeForm.
    
    **Validates: Requirements 9.4**
    """
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            
            # Update session to prevent logout
            update_session_auth_hash(request, user)
            
            # Record activity
            ActivityService.record_activity(
                user_id=user.id,
                activity_type='profile_updated',
                data={'field': 'password'}
            )
            
            # Create audit log entry
            AuditLog.log_action(
                user=user,
                action='update',
                model_name='User',
                object_id=str(user.id),
                description='Password changed',
                severity='medium',
                details={
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'timestamp': timezone.now().isoformat(),
                }
            )
            
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('dashboard:settings_security')
        else:
            for field, errors in password_form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        password_form = PasswordChangeForm(request.user)
    
    context = {
        'password_form': password_form,
        'active_tab': 'security',
    }
    
    return render(request, 'dashboard/settings/security.html', context)


@login_required
def settings_connected_accounts(request):
    """
    Connected accounts settings view.
    
    Displays Steam, Discord, and Twitch connections.
    Shows connection status and allows users to view their connected accounts.
    
    Note: Actual connection/disconnection functionality is handled by
    the respective authentication backends (allauth, etc.)
    
    **Validates: Requirements 9.5**
    """
    user = request.user
    
    # Build connected accounts data
    connected_accounts = {
        'steam': {
            'name': 'Steam',
            'connected': bool(user.steam_id),
            'identifier': user.steam_id if user.steam_id else None,
            'icon': 'fab fa-steam',
        },
        'discord': {
            'name': 'Discord',
            'connected': bool(user.discord_username),
            'identifier': user.discord_username if user.discord_username else None,
            'icon': 'fab fa-discord',
        },
        'twitch': {
            'name': 'Twitch',
            'connected': bool(user.twitch_username),
            'identifier': user.twitch_username if user.twitch_username else None,
            'icon': 'fab fa-twitch',
        },
    }
    
    context = {
        'connected_accounts': connected_accounts,
        'active_tab': 'accounts',
    }
    
    return render(request, 'dashboard/settings/connected_accounts.html', context)


@login_required
def account_delete(request):
    """
    Account deletion view.
    
    Handles account deletion with:
    - Confirmation dialog explaining consequences
    - Password re-entry for security verification
    - Data anonymization (replaces personal info with placeholders)
    - Tournament participation records retained without personal identifiers
    - Confirmation email sent before deletion
    - Immediate logout after deletion
    - Audit log entry created
    
    **Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5**
    """
    user = request.user
    
    if request.method == 'POST':
        delete_form = AccountDeleteForm(request.POST, user=user)
        if delete_form.is_valid():
            # Get client IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # Create audit log entry before deletion
            AuditLog.log_action(
                user=user,
                action='delete',
                model_name='User',
                object_id=str(user.id),
                description=f'Account deletion requested from IP {ip_address}',
                severity='high',
                details={
                    'ip_address': ip_address,
                    'timestamp': timezone.now().isoformat(),
                    'username': user.username,
                    'email': user.email,
                }
            )
            
            # Send confirmation email
            from django.core.mail import send_mail
            from django.conf import settings
            
            try:
                send_mail(
                    subject='Account Deletion Confirmation',
                    message=f'Your account {user.username} has been deleted. If you did not request this, please contact support immediately.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception as e:
                # Log error but continue with deletion
                pass
            
            # Anonymize user data
            user.first_name = '[DELETED]'
            user.last_name = '[DELETED]'
            user.display_name = '[DELETED USER]'
            user.email = f'deleted_{user.id}@deleted.local'
            user.bio = ''
            user.phone_number = ''
            user.discord_username = ''
            user.steam_id = ''
            user.twitch_username = ''
            user.is_active = False
            
            # Clear avatar and banner
            if user.avatar:
                user.avatar.delete(save=False)
            if user.banner:
                user.banner.delete(save=False)
            
            user.save()
            
            # Tournament participation records are retained but personal identifiers removed
            # The Participant model links to User, so the anonymized user data will be shown
            
            # Logout user immediately
            from django.contrib.auth import logout
            logout(request)
            
            messages.success(request, 'Your account has been deleted. We\'re sorry to see you go.')
            return redirect('home')
        else:
            for field, errors in delete_form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        delete_form = AccountDeleteForm(user=user)
    
    context = {
        'delete_form': delete_form,
        'active_tab': 'delete',
    }
    
    return render(request, 'dashboard/settings/delete_account.html', context)



@login_required
def user_report(request, username):
    """
    User report view.
    
    Allows users to report other users for inappropriate behavior.
    
    Handles:
    - Accept username parameter
    - Use UserReportForm with category and description
    - Validate reporter != reported_user
    - Create UserReport record with status='pending'
    - Send notification to admin users
    - Redirect with success message
    
    **Validates: Requirements 10.3**
    """
    # Get the reported user
    reported_user = get_object_or_404(User, username=username)
    
    # Validate reporter != reported_user
    if request.user == reported_user:
        messages.error(request, 'You cannot report yourself.')
        return redirect('dashboard:profile_view', username=username)
    
    if request.method == 'POST':
        report_form = UserReportForm(request.POST)
        if report_form.is_valid():
            # Create UserReport record with status='pending'
            report = report_form.save(commit=False)
            report.reporter = request.user
            report.reported_user = reported_user
            report.status = 'pending'
            report.save()
            
            # Send notification to admin users
            try:
                from notifications.services import NotificationService
                admin_users = User.objects.filter(is_staff=True, is_active=True)
                
                for admin in admin_users:
                    NotificationService.create_notification(
                        user=admin,
                        notification_type='moderation',
                        title='New User Report',
                        message=f'{request.user.get_display_name()} reported {reported_user.get_display_name()} for {report.get_category_display()}',
                        link=f'/admin/dashboard/userreport/{report.id}/change/',
                        priority='high'
                    )
            except Exception as e:
                # Log error but don't fail the report submission
                pass
            
            messages.success(request, 'Your report has been submitted. Our moderation team will review it shortly.')
            return redirect('dashboard:profile_view', username=username)
        else:
            for field, errors in report_form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        report_form = UserReportForm()
    
    context = {
        'report_form': report_form,
        'reported_user': reported_user,
    }
    
    return render(request, 'dashboard/user_report.html', context)
