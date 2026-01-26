from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Q, Count, Case, When, Value, IntegerField
from django.utils import timezone
from datetime import timedelta

from .models import Team, TeamMember, TeamInvite, TeamAnnouncement
from .forms import TeamCreateForm, TeamSettingsForm
from core.models import User, Game


# ============================================================================
# Permission Mixins
# ============================================================================

class TeamAccessMixin:
    """Base mixin for team access control"""
    
    def get_team(self):
        """Get team from URL slug"""
        if not hasattr(self, '_team'):
            self._team = get_object_or_404(Team, slug=self.kwargs['slug'])
        return self._team
    
    def get_user_membership(self):
        """Get user's membership in the team"""
        if not self.request.user.is_authenticated:
            return None
        
        team = self.get_team()
        
        return TeamMember.objects.filter(
            team=team,
            user=self.request.user,
            status='active'
        ).first()


class TeamMemberRequiredMixin(TeamAccessMixin):
    """Require user to be an active team member"""
    
    def dispatch(self, request, *args, **kwargs):
        """Check member permission before dispatching"""
        team = self.get_team()
        
        # Allow access if team is public or user is a member
        if not team.is_public:
            membership = self.get_user_membership()
            if not membership:
                messages.error(request, 'You must be a team member to access this page.')
                return redirect('teams:detail', slug=self.kwargs['slug'])
        
        return super().dispatch(request, *args, **kwargs)


class TeamCaptainRequiredMixin(TeamAccessMixin):
    """Require user to be the team captain"""
    
    def dispatch(self, request, *args, **kwargs):
        """Check captain permission before dispatching"""
        membership = self.get_user_membership()
        if not membership or membership.role != 'captain':
            messages.error(request, 'Only the team captain can perform this action.')
            return redirect('teams:detail', slug=self.kwargs['slug'])
        return super().dispatch(request, *args, **kwargs)


class TeamCaptainOrCoCaptainRequiredMixin(TeamAccessMixin):
    """Require user to be captain or co-captain"""
    
    def dispatch(self, request, *args, **kwargs):
        """Check captain/co-captain permission before dispatching"""
        membership = self.get_user_membership()
        if not membership or membership.role not in ['captain', 'co_captain']:
            messages.error(request, 'Only team captains and co-captains can perform this action.')
            return redirect('teams:detail', slug=self.kwargs['slug'])
        return super().dispatch(request, *args, **kwargs)


# ============================================================================
# Team List and Discovery
# ============================================================================

class TeamListView(ListView):
    """List and search teams"""
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Team.objects.filter(
            status='active',
            is_public=True
        ).select_related('game', 'captain').annotate(
            annotated_member_count=Count('members', filter=Q(members__status='active')),
            annotated_achievement_count=Count('achievements')
        )
        
        # Search by name, tag, or description (AND logic with other filters)
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(tag__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by game (AND logic)
        game = self.request.GET.get('game', '').strip()
        if game:
            queryset = queryset.filter(game__slug=game)
        
        # Filter by recruiting status (AND logic)
        recruiting = self.request.GET.get('recruiting', '').strip()
        if recruiting == 'true':
            queryset = queryset.filter(is_recruiting=True)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all games that have teams
        context['available_games'] = Game.objects.filter(
            teams__status='active',
            teams__is_public=True
        ).distinct().order_by('name')
        
        # Preserve filter parameters
        context['filter_params'] = {
            'search': self.request.GET.get('search', ''),
            'game': self.request.GET.get('game', ''),
            'recruiting': self.request.GET.get('recruiting', ''),
        }
        
        return context


# ============================================================================
# Team Detail
# ============================================================================

class TeamDetailView(DetailView):
    """Team detail page"""
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get(self, request, *args, **kwargs):
        """Override get to handle private team access control"""
        self.object = self.get_object()
        
        # Enforce private team access control (Requirement 3.1, 12.1)
        if not self.object.is_public:
            if not request.user.is_authenticated:
                messages.error(request, 'This team is private.')
                return redirect('teams:list')
            
            # Check if user is an active member
            membership = TeamMember.objects.filter(
                team=self.object,
                user=request.user,
                status='active'
            ).first()
            
            if not membership:
                messages.error(request, 'This team is private. Only members can view it.')
                return redirect('teams:list')
        
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object
        
        # Check user membership status (Requirement 3.1)
        user_membership = None
        if self.request.user.is_authenticated:
            user_membership = TeamMember.objects.filter(
                team=team,
                user=self.request.user
            ).first()
        context['user_membership'] = user_membership
        
        # Load roster with active members only (Requirement 3.2, 6.1)
        context['roster'] = team.members.filter(
            status='active'
        ).select_related('user').order_by('role', '-joined_at')
        
        # Load recent tournament history (Requirement 3.3)
        from tournaments.models import Participant
        recent_tournaments = Participant.objects.filter(
            team=team,
            status='confirmed'
        ).select_related(
            'tournament', 'tournament__game'
        ).order_by('-tournament__start_datetime')[:5]
        context['recent_tournaments'] = recent_tournaments
        
        # Load team achievements (Requirement 3.4)
        achievements = team.achievements.all().order_by('-earned_at')[:6]
        context['achievements'] = achievements
        
        # Load recent announcements (Requirement 3.5, 9.3)
        announcements = team.announcements.all().select_related('posted_by').order_by(
            '-is_pinned', '-created_at'
        )[:5]
        context['recent_announcements'] = announcements
        
        return context


# ============================================================================
# Team Creation
# ============================================================================

class TeamCreateView(LoginRequiredMixin, CreateView):
    """Create a new team"""
    model = Team
    form_class = TeamCreateForm
    template_name = 'teams/team_create.html'
    
    def form_valid(self, form):
        # Set captain
        form.instance.captain = self.request.user
        form.instance.status = 'active'
        
        # Save team
        response = super().form_valid(form)
        
        # Create captain membership
        TeamMember.objects.create(
            team=self.object,
            user=self.request.user,
            role='captain',
            status='active',
            approved_at=timezone.now()
        )
        
        messages.success(self.request, f'Team "{self.object.name}" created successfully!')
        return response
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse('teams:detail', kwargs={'slug': self.object.slug})


# ============================================================================
# Team Settings
# ============================================================================

class TeamSettingsView(LoginRequiredMixin, TeamCaptainRequiredMixin, UpdateView):
    """Team settings page (captain only) - Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 12.1"""
    model = Team
    form_class = TeamSettingsForm
    template_name = 'teams/team_settings.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        """Load current team settings (Requirement 7.1)"""
        context = super().get_context_data(**kwargs)
        context['user_membership'] = self.get_user_membership()
        
        # Get all active members for transfer captaincy dropdown
        context['active_members'] = self.object.members.filter(
            status='active'
        ).exclude(
            user=self.request.user
        ).select_related('user').order_by('role', '-joined_at')
        
        return context
    
    def form_valid(self, form):
        """Implement update functionality for team info (Requirement 7.2)"""
        # Handle logo and banner uploads (Requirement 7.3)
        # Files are automatically handled by Django's form processing
        
        # Implement toggle updates (Requirement 7.4)
        # recruiting, approval, public toggles are handled by the form
        
        messages.success(self.request, 'Team settings updated successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse('teams:settings', kwargs={'slug': self.object.slug})


# ============================================================================
# Roster Management
# ============================================================================

class TeamRosterView(LoginRequiredMixin, TeamCaptainOrCoCaptainRequiredMixin, DetailView):
    """Team roster management page"""
    model = Team
    template_name = 'teams/team_roster.html'
    context_object_name = 'team'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object
        
        # Get user's membership for permission checks in template
        context['user_membership'] = self.get_user_membership()
        
        # Get all members
        context['active_members'] = team.members.filter(
            status='active'
        ).select_related('user').order_by('role', '-joined_at')
        
        # Get pending applications
        context['pending_applications'] = team.members.filter(
            status='pending'
        ).select_related('user').order_by('-joined_at')
        
        # Get pending invites
        context['pending_invites'] = team.invites.filter(
            status='pending',
            expires_at__gt=timezone.now()
        ).select_related('invited_user', 'invited_by').order_by('-created_at')
        
        return context


# ============================================================================
# Team Invitations
# ============================================================================

class TeamInvitesView(LoginRequiredMixin, DetailView):
    """View team invitations"""
    model = Team
    template_name = 'teams/team_invites.html'
    context_object_name = 'team'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's received invites
        if self.request.user.is_authenticated:
            context['received_invites'] = TeamInvite.objects.filter(
                invited_user=self.request.user,
                status='pending',
                expires_at__gt=timezone.now()
            ).select_related('team', 'invited_by').order_by('-created_at')
        
        return context


class TeamUserSearchView(LoginRequiredMixin, View):
    """Search for users to invite (Requirement 4.1)"""
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        team_slug = request.GET.get('team', '')
        
        if not query or len(query) < 2:
            return JsonResponse({'users': []})
        
        # Get team to check existing members
        team = None
        if team_slug:
            try:
                team = Team.objects.get(slug=team_slug)
            except Team.DoesNotExist:
                pass
        
        # Search users by username or email
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(
            id=request.user.id  # Exclude current user
        )[:10]
        
        # Filter out existing team members if team is specified
        if team:
            existing_member_ids = team.members.filter(
                status__in=['active', 'pending']
            ).values_list('user_id', flat=True)
            users = users.exclude(id__in=existing_member_ids)
            
            # Filter out users with pending invites
            pending_invite_user_ids = team.invites.filter(
                status='pending',
                expires_at__gt=timezone.now()
            ).values_list('invited_user_id', flat=True)
            users = users.exclude(id__in=pending_invite_user_ids)
        
        # Format response
        user_list = [{
            'id': str(user.id),
            'username': user.username,
            'display_name': user.get_display_name(),
            'email': user.email,
        } for user in users]
        
        return JsonResponse({'users': user_list})


class TeamInviteSendView(LoginRequiredMixin, TeamCaptainOrCoCaptainRequiredMixin, View):
    """Send team invitation"""
    
    def post(self, request, slug):
        team = get_object_or_404(Team, slug=slug)
        
        # Get invited user
        user_id = request.POST.get('user_id')
        try:
            invited_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('teams:roster', slug=slug)
        
        # Check if team is full
        if team.is_full:
            messages.error(request, 'Team is full.')
            return redirect('teams:roster', slug=slug)
        
        # Check if user is already a member
        if TeamMember.objects.filter(team=team, user=invited_user, status='active').exists():
            messages.error(request, 'User is already a team member.')
            return redirect('teams:roster', slug=slug)
        
        # Check if invite already exists
        if TeamInvite.objects.filter(
            team=team,
            invited_user=invited_user,
            status='pending',
            expires_at__gt=timezone.now()
        ).exists():
            messages.error(request, 'An active invite already exists for this user.')
            return redirect('teams:roster', slug=slug)
        
        # Create invite with 7-day expiration (Requirement 4.2)
        invite = TeamInvite.objects.create(
            team=team,
            invited_by=request.user,
            invited_user=invited_user,
            message=request.POST.get('message', ''),
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Send notification to invited user (Requirement 4.3)
        from .notification_service import TeamNotificationService
        TeamNotificationService.notify_team_invite(invite, request.user)
        
        messages.success(request, f'Invitation sent to {invited_user.get_display_name()}.')
        return redirect('teams:roster', slug=slug)


class TeamInviteAcceptView(LoginRequiredMixin, View):
    """Accept team invitation (Requirement 4.4, 4.5)"""
    
    def post(self, request, invite_id):
        invite = get_object_or_404(
            TeamInvite,
            id=invite_id,
            invited_user=request.user,
            status='pending'
        )
        
        # Check if invite is expired
        if invite.expires_at < timezone.now():
            invite.status = 'expired'
            invite.save()
            messages.error(request, 'This invitation has expired.')
            return redirect('teams:list')
        
        # Check if team is full
        if invite.team.is_full:
            messages.error(request, 'Team is full.')
            return redirect('teams:detail', slug=invite.team.slug)
        
        # Check game-specific team limits (Requirement 12.5)
        # Users can only be an active member of one team per game
        existing_active_membership = TeamMember.objects.filter(
            user=request.user,
            team__game=invite.team.game,
            status='active'
        ).select_related('team').first()
        
        if existing_active_membership:
            messages.error(
                request,
                f'You are already an active member of {existing_active_membership.team.name} for {invite.team.game.name}. '
                f'You can only be on one team per game.'
            )
            return redirect('teams:detail', slug=invite.team.slug)
        
        # Create active TeamMember (Requirement 4.5)
        TeamMember.objects.create(
            team=invite.team,
            user=request.user,
            role='member',
            status='active',
            approved_at=timezone.now()
        )
        
        # Update invite status and responded_at timestamp (Requirement 4.5)
        invite.status = 'accepted'
        invite.responded_at = timezone.now()
        invite.save()
        
        # Notify team captain
        from .notification_service import TeamNotificationService
        TeamNotificationService.notify_invite_accepted(invite, invite.team)
        TeamNotificationService.notify_member_joined(invite.team, request.user)
        
        messages.success(request, f'You have joined {invite.team.name}!')
        return redirect('teams:detail', slug=invite.team.slug)


class TeamInviteDeclineView(LoginRequiredMixin, View):
    """Decline team invitation (Requirement 4.4, 4.5)"""
    
    def post(self, request, invite_id):
        invite = get_object_or_404(
            TeamInvite,
            id=invite_id,
            invited_user=request.user,
            status='pending'
        )
        
        # Mark invite as declined and update responded_at timestamp (Requirement 4.5)
        invite.status = 'declined'
        invite.responded_at = timezone.now()
        invite.save()
        
        # Notify team captain
        from .notification_service import TeamNotificationService
        TeamNotificationService.notify_invite_declined(invite, invite.team)
        
        messages.info(request, 'Invitation declined.')
        return redirect('teams:list')


class TeamInviteCancelView(LoginRequiredMixin, TeamCaptainOrCoCaptainRequiredMixin, View):
    """Cancel a pending team invitation"""
    
    def post(self, request, slug, invite_id):
        team = get_object_or_404(Team, slug=slug)
        invite = get_object_or_404(
            TeamInvite,
            id=invite_id,
            team=team,
            status='pending'
        )
        
        # Delete the invite
        invited_user_name = invite.invited_user.get_display_name()
        invite.delete()
        
        messages.success(request, f'Invitation to {invited_user_name} has been cancelled.')
        return redirect('teams:roster', slug=slug)


# ============================================================================
# Team Applications
# ============================================================================

class TeamApplyView(LoginRequiredMixin, View):
    """Apply to join a team (Requirement 5.1, 5.2, 5.3)"""
    
    def post(self, request, slug):
        team = get_object_or_404(Team, slug=slug)
        
        # Check if team is recruiting (Requirement 5.1)
        if not team.is_recruiting:
            messages.error(request, 'This team is not currently recruiting.')
            return redirect('teams:detail', slug=slug)
        
        # Check if team is full (Requirement 5.1)
        if team.is_full:
            messages.error(request, 'Team is full.')
            return redirect('teams:detail', slug=slug)
        
        # Check game-specific team limits (Requirement 12.5)
        # Users can only be an active member of one team per game
        existing_active_membership = TeamMember.objects.filter(
            user=request.user,
            team__game=team.game,
            status='active'
        ).select_related('team').first()
        
        if existing_active_membership:
            messages.error(
                request,
                f'You are already an active member of {existing_active_membership.team.name} for {team.game.name}. '
                f'You can only be on one team per game.'
            )
            return redirect('teams:detail', slug=slug)
        
        # Check if user is already a member or has pending application
        existing = TeamMember.objects.filter(
            team=team,
            user=request.user
        ).first()
        
        if existing:
            if existing.status == 'active':
                messages.error(request, 'You are already a member of this team.')
            elif existing.status == 'pending':
                messages.error(request, 'You already have a pending application.')
            return redirect('teams:detail', slug=slug)
        
        # Create pending TeamMember record (Requirement 5.2)
        application = TeamMember.objects.create(
            team=team,
            user=request.user,
            role='member',
            status='pending'
        )
        
        # Send notification to captain (Requirement 5.3)
        from .notification_service import TeamNotificationService
        TeamNotificationService.notify_new_application(application, team)
        
        messages.success(request, 'Application submitted! The team captain will review it.')
        return redirect('teams:detail', slug=slug)


class TeamApplicationsView(LoginRequiredMixin, TeamCaptainOrCoCaptainRequiredMixin, DetailView):
    """View team applications"""
    model = Team
    template_name = 'teams/team_applications.html'
    context_object_name = 'team'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get pending applications
        context['pending_applications'] = self.object.members.filter(
            status='pending'
        ).select_related('user').order_by('-joined_at')
        
        return context


class TeamApplicationApproveView(LoginRequiredMixin, TeamCaptainOrCoCaptainRequiredMixin, View):
    """Approve team application (Requirement 5.4, 5.5, 12.3)"""
    
    def post(self, request, slug, member_id):
        team = get_object_or_404(Team, slug=slug)
        
        # First check if the member exists at all
        try:
            member = TeamMember.objects.get(id=member_id, team=team)
        except TeamMember.DoesNotExist:
            messages.error(request, 'Application not found. It may have already been processed or withdrawn.')
            return redirect('teams:roster', slug=slug)
        
        # Check if application is already processed
        if member.status == 'active':
            messages.info(request, f'{member.user.get_display_name()} is already a team member.')
            return redirect('teams:roster', slug=slug)
        elif member.status != 'pending':
            messages.error(request, f'Application for {member.user.get_display_name()} has already been processed.')
            return redirect('teams:roster', slug=slug)
        
        # Check if team is full
        if team.is_full:
            messages.error(request, 'Team is full.')
            return redirect('teams:roster', slug=slug)
        
        # Check game-specific team limits (Requirement 12.5)
        # Users can only be an active member of one team per game
        existing_active_membership = TeamMember.objects.filter(
            user=member.user,
            team__game=team.game,
            status='active'
        ).select_related('team').first()
        
        if existing_active_membership:
            messages.error(
                request,
                f'{member.user.get_display_name()} is already an active member of {existing_active_membership.team.name} for {team.game.name}. '
                f'Users can only be on one team per game.'
            )
            return redirect('teams:roster', slug=slug)
        
        # Approve member - change status to active (Requirement 5.5)
        member.status = 'active'
        member.approved_at = timezone.now()
        member.save()
        
        # Send notification to applicant (Requirement 5.5)
        from .notification_service import TeamNotificationService
        TeamNotificationService.notify_application_approved(member, team)
        TeamNotificationService.notify_member_joined(team, member.user)
        
        messages.success(request, f'{member.user.get_display_name()} has been added to the team.')
        return redirect('teams:roster', slug=slug)


class TeamApplicationDeclineView(LoginRequiredMixin, TeamCaptainOrCoCaptainRequiredMixin, View):
    """Decline team application (Requirement 5.4, 5.5, 12.3)"""
    
    def post(self, request, slug, member_id):
        team = get_object_or_404(Team, slug=slug)
        
        # First check if the member exists at all
        try:
            member = TeamMember.objects.get(id=member_id, team=team)
        except TeamMember.DoesNotExist:
            messages.error(request, 'Application not found. It may have already been processed or withdrawn.')
            return redirect('teams:roster', slug=slug)
        
        # Check if application is already processed
        if member.status == 'active':
            messages.error(request, f'{member.user.get_display_name()} is already a team member and cannot be declined.')
            return redirect('teams:roster', slug=slug)
        elif member.status != 'pending':
            messages.error(request, f'Application for {member.user.get_display_name()} has already been processed.')
            return redirect('teams:roster', slug=slug)
        
        # Store user info before deletion
        user_name = member.user.get_display_name()
        applicant_user = member.user
        
        # Delete TeamMember record (Requirement 5.5)
        member.delete()
        
        # Send notification to applicant (Requirement 5.5)
        from .notification_service import TeamNotificationService
        TeamNotificationService.notify_application_declined(applicant_user, team)
        
        messages.info(request, f'Application from {user_name} has been declined.')
        return redirect('teams:roster', slug=slug)


# ============================================================================
# Team Announcements
# ============================================================================

class TeamAnnouncementsView(LoginRequiredMixin, TeamMemberRequiredMixin, DetailView):
    """Team announcements page (Requirements 9.1, 9.4)"""
    model = Team
    template_name = 'teams/team_announcements.html'
    context_object_name = 'team'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object
        
        # Get user's membership for permission checks in template
        context['user_membership'] = self.get_user_membership()
        
        # Load announcements (pinned first, then by date) - Requirement 9.1, 9.4
        from .models import TeamAnnouncement
        context['announcements'] = team.announcements.all().select_related(
            'posted_by'
        ).order_by('-is_pinned', '-created_at')
        
        # Load team activity feed (recent events)
        # This includes: member joins, tournament registrations, match results, achievements, role changes
        context['activity_feed'] = self._get_activity_feed(team)
        
        return context
    
    def _get_activity_feed(self, team):
        """Generate team activity feed from various sources"""
        activities = []
        
        # Recent member joins (last 30 days)
        recent_joins = team.members.filter(
            status='active',
            approved_at__gte=timezone.now() - timedelta(days=30)
        ).select_related('user').order_by('-approved_at')[:10]
        
        for member in recent_joins:
            activities.append({
                'type': 'member_join',
                'timestamp': member.approved_at,
                'description': f"{member.user.get_display_name()} joined the team",
                'icon': 'person_add'
            })
        
        # Recent achievements
        recent_achievements = team.achievements.all().order_by('-earned_at')[:5]
        for achievement in recent_achievements:
            activities.append({
                'type': 'achievement',
                'timestamp': achievement.earned_at,
                'description': f"Team earned: {achievement.title}",
                'icon': 'emoji_events'
            })
        
        # Recent tournament registrations
        from tournaments.models import Participant
        recent_tournaments = Participant.objects.filter(
            team=team,
            status='confirmed',
            registered_at__gte=timezone.now() - timedelta(days=30)
        ).select_related('tournament').order_by('-registered_at')[:5]
        
        for participant in recent_tournaments:
            activities.append({
                'type': 'tournament_registration',
                'timestamp': participant.registered_at,
                'description': f"Registered for {participant.tournament.name}",
                'icon': 'event'
            })
        
        # Sort all activities by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return activities[:20]  # Return top 20 most recent activities


class TeamAnnouncementPostView(LoginRequiredMixin, TeamCaptainOrCoCaptainRequiredMixin, View):
    """Post team announcement (Requirements 9.1, 9.2, 12.3)"""
    
    def post(self, request, slug):
        team = get_object_or_404(Team, slug=slug)
        
        # Get form data
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        priority = request.POST.get('priority', 'normal')
        is_pinned = request.POST.get('is_pinned') == 'on'
        
        # Validate inputs
        if not title:
            messages.error(request, 'Announcement title is required.')
            return redirect('teams:announcements', slug=slug)
        
        if not content:
            messages.error(request, 'Announcement content is required.')
            return redirect('teams:announcements', slug=slug)
        
        # Validate priority
        valid_priorities = ['normal', 'important', 'urgent']
        if priority not in valid_priorities:
            priority = 'normal'
        
        # Create TeamAnnouncement record (Requirement 9.1)
        from .models import TeamAnnouncement
        announcement = TeamAnnouncement.objects.create(
            team=team,
            posted_by=request.user,
            title=title,
            content=content,
            priority=priority,
            is_pinned=is_pinned
        )
        
        # Send notifications to all active team members (Requirement 9.2)
        from .notification_service import TeamNotificationService
        TeamNotificationService.notify_team_announcement(announcement, team, request.user)
        
        messages.success(request, 'Announcement posted successfully!')
        return redirect('teams:announcements', slug=slug)


# ============================================================================
# Team Statistics
# ============================================================================

class TeamStatsView(DetailView):
    """Team statistics dashboard (Requirements 8.1, 8.2, 8.3, 8.4)"""
    model = Team
    template_name = 'teams/team_stats.html'
    context_object_name = 'team'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object
        
        # Load team statistics (Requirement 8.1, 8.2)
        context['statistics'] = {
            'tournaments_played': team.tournaments_played,
            'tournaments_won': team.tournaments_won,
            'total_wins': team.total_wins,
            'total_losses': team.total_losses,
            'win_rate': team.win_rate,
            'current_streak': self._calculate_current_streak(team),
        }
        
        # Load match history (Requirement 8.4)
        context['recent_matches'] = self._get_recent_matches(team)
        
        # Calculate performance trends (Requirement 8.4)
        context['performance_trends'] = self._calculate_performance_trends(team)
        
        # Load individual member statistics (Requirement 8.3)
        context['member_statistics'] = self._get_member_statistics(team)
        
        return context
    
    def _calculate_current_streak(self, team):
        """Calculate current win/loss streak"""
        from tournaments.models import Match
        
        # Get recent matches where team participated (as winner or loser)
        recent_matches = Match.objects.filter(
            Q(winner__team=team) | Q(loser__team=team),
            status='completed'
        ).order_by('-completed_at')[:20]
        
        if not recent_matches:
            return {'type': 'none', 'count': 0}
        
        streak_type = None
        streak_count = 0
        
        for match in recent_matches:
            is_winner = match.winner and match.winner.team == team
            
            if streak_type is None:
                # First match sets the streak type
                streak_type = 'win' if is_winner else 'loss'
                streak_count = 1
            elif (streak_type == 'win' and is_winner) or (streak_type == 'loss' and not is_winner):
                # Streak continues
                streak_count += 1
            else:
                # Streak broken
                break
        
        return {'type': streak_type or 'none', 'count': streak_count}
    
    def _get_recent_matches(self, team):
        """Get recent match history with results"""
        from tournaments.models import Match, Participant
        
        # Get matches where team participated
        matches = Match.objects.filter(
            Q(participant1__team=team) | Q(participant2__team=team),
            status='completed'
        ).select_related(
            'tournament',
            'participant1__team',
            'participant1__user',
            'participant2__team',
            'participant2__user',
            'winner__team',
            'winner__user'
        ).order_by('-completed_at')[:10]
        
        match_list = []
        for match in matches:
            # Determine if team was participant1 or participant2
            is_p1 = match.participant1 and match.participant1.team == team
            team_score = match.score_p1 if is_p1 else match.score_p2
            opponent_score = match.score_p2 if is_p1 else match.score_p1
            
            # Get opponent info
            opponent_participant = match.participant2 if is_p1 else match.participant1
            opponent_name = opponent_participant.display_name if opponent_participant else "Unknown"
            
            # Determine result
            is_winner = match.winner and match.winner.team == team
            
            match_list.append({
                'tournament': match.tournament,
                'opponent': opponent_name,
                'team_score': team_score,
                'opponent_score': opponent_score,
                'result': 'win' if is_winner else 'loss',
                'date': match.completed_at,
                'round': match.round_number,
            })
        
        return match_list
    
    def _calculate_performance_trends(self, team):
        """Calculate win/loss trends over time"""
        from tournaments.models import Match
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        # Get matches from last 6 months, grouped by month
        six_months_ago = timezone.now() - timedelta(days=180)
        
        matches = Match.objects.filter(
            Q(participant1__team=team) | Q(participant2__team=team),
            status='completed',
            completed_at__gte=six_months_ago
        ).order_by('completed_at')
        
        # Group by month
        monthly_data = {}
        for match in matches:
            month_key = match.completed_at.strftime('%Y-%m')
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {'wins': 0, 'losses': 0}
            
            is_winner = match.winner and match.winner.team == team
            if is_winner:
                monthly_data[month_key]['wins'] += 1
            else:
                monthly_data[month_key]['losses'] += 1
        
        # Convert to list format for charting
        trend_data = []
        for month, data in sorted(monthly_data.items()):
            trend_data.append({
                'month': month,
                'wins': data['wins'],
                'losses': data['losses'],
                'total': data['wins'] + data['losses']
            })
        
        return trend_data
    
    def _get_member_statistics(self, team):
        """Get individual member statistics (Requirement 8.3)"""
        members = team.members.filter(
            status='active'
        ).select_related('user').order_by('-matches_played')
        
        member_stats = []
        for member in members:
            total_matches = member.matches_played
            win_rate = 0
            if total_matches > 0:
                win_rate = round((member.matches_won / total_matches) * 100, 2)
            
            member_stats.append({
                'user': member.user,
                'role': member.get_role_display(),
                'matches_played': member.matches_played,
                'matches_won': member.matches_won,
                'win_rate': win_rate,
                'joined_at': member.joined_at,
            })
        
        return member_stats


# ============================================================================
# Team Achievements
# ============================================================================

class TeamAchievementsView(DetailView):
    """Team achievements gallery page (Requirement 15.3)"""
    model = Team
    template_name = 'teams/team_achievements.html'
    context_object_name = 'team'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object
        
        # Load all achievements
        all_achievements = team.achievements.all().order_by('-earned_at')
        context['achievements'] = all_achievements
        
        # Categorize achievements
        tournament_types = ['first_win', 'tournament_champion', 'undefeated', 'comeback', 'dynasty', 'perfect_season', 'giant_slayer']
        performance_types = ['win_streak']
        milestone_types = ['getting_started', 'experienced', 'veterans', 'legends', 'full_roster']
        
        context['tournament_achievements'] = all_achievements.filter(achievement_type__in=tournament_types)
        context['performance_achievements'] = all_achievements.filter(achievement_type__in=performance_types)
        context['milestone_achievements'] = all_achievements.filter(achievement_type__in=milestone_types)
        
        # Count tournament achievements
        context['tournament_achievements_count'] = context['tournament_achievements'].count()
        
        # Get latest achievement
        context['latest_achievement'] = all_achievements.first() if all_achievements.exists() else None
        
        return context


# ============================================================================
# Team Actions
# ============================================================================

class TeamLeaveView(LoginRequiredMixin, View):
    """Leave a team"""
    
    def post(self, request, slug):
        # Handle cases where team doesn't exist (Requirement 4.4)
        try:
            team = Team.objects.get(slug=slug)
        except Team.DoesNotExist:
            messages.error(request, 'Team not found. It may have been deleted or the link is invalid.')
            return redirect('teams:list')
        
        # Validate team state before processing (Requirement 4.4)
        if team.status == 'disbanded':
            messages.error(request, 'Cannot leave a disbanded team.')
            return redirect('teams:list')
        
        if team.status != 'active':
            messages.error(request, 'Team is not in a valid state for leaving.')
            return redirect('teams:list')
        
        # Get user's membership and validate permissions (Requirement 4.4)
        try:
            membership = TeamMember.objects.get(
                team=team,
                user=request.user,
                status='active'
            )
        except TeamMember.DoesNotExist:
            messages.error(request, 'You are not an active member of this team.')
            return redirect('teams:detail', slug=slug)
        
        # Handle captain leaving
        if membership.role == 'captain':
            try:
                # Find co-captain or oldest member to transfer captaincy
                # Priority: co-captains first (value 0), then regular members (value 1)
                # Tie-breaking: earliest join date (joined_at ascending)
                new_captain = team.members.filter(
                    status='active'
                ).exclude(
                    user=request.user
                ).order_by(
                    Case(
                        When(role='co_captain', then=Value(0)),
                        default=Value(1),
                        output_field=IntegerField()
                    ),
                    'joined_at'
                ).first()
                
                if new_captain:
                    # Transfer captaincy with proper data consistency
                    # Update new captain's role to captain
                    new_captain.role = 'captain'
                    new_captain.save()
                    
                    # Update team's captain field
                    team.captain = new_captain.user
                    team.save()
                    
                    messages.info(request, f'Captaincy transferred to {new_captain.user.get_display_name()}.')
                else:
                    # No other active members found - disband team
                    team.status = 'disbanded'
                    team.save()
                    messages.info(request, 'Team has been disbanded as you were the last member.')
            except Exception as e:
                # Handle unexpected errors during captaincy transfer (Requirement 4.4)
                messages.error(
                    request,
                    'An error occurred while transferring captaincy. Please try again or contact support.'
                )
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Error during captaincy transfer for team {team.slug}: {str(e)}', exc_info=True)
                return redirect('teams:detail', slug=slug)
        
        # Set member to inactive and record leave timestamp
        try:
            membership.status = 'inactive'
            membership.left_at = timezone.now()
            membership.save()
        except Exception as e:
            # Handle errors during membership update (Requirement 4.4)
            messages.error(
                request,
                'An error occurred while processing your leave request. Please try again or contact support.'
            )
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error updating membership for user {request.user.id} in team {team.slug}: {str(e)}', exc_info=True)
            return redirect('teams:detail', slug=slug)
        
        # Notify team captain (only if team is still active)
        if team.status != 'disbanded':
            try:
                from .notification_service import TeamNotificationService
                TeamNotificationService.notify_member_left(team, request.user)
            except Exception as e:
                # Log notification errors but don't fail the operation (Requirement 4.4)
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to send notification for member leave in team {team.slug}: {str(e)}')
                # Continue with success message even if notification fails
        
        messages.success(request, f'You have left {team.name}.')
        return redirect('teams:list')


class TeamTransferCaptaincyView(LoginRequiredMixin, TeamCaptainRequiredMixin, View):
    """Transfer team captaincy to another member (captain only)"""
    
    def post(self, request, slug):
        team = get_object_or_404(Team, slug=slug)
        
        # Get new captain member ID
        new_captain_member_id = request.POST.get('new_captain')
        
        if not new_captain_member_id:
            messages.error(request, 'Please select a member to transfer captaincy to.')
            return redirect('teams:settings', slug=slug)
        
        # Get new captain member
        try:
            new_captain_member = TeamMember.objects.get(
                id=new_captain_member_id,
                team=team,
                status='active'
            )
        except TeamMember.DoesNotExist:
            messages.error(request, 'Invalid member selected.')
            return redirect('teams:settings', slug=slug)
        
        # Cannot transfer to self
        if new_captain_member.user == request.user:
            messages.error(request, 'You are already the captain.')
            return redirect('teams:settings', slug=slug)
        
        # Get current captain membership
        current_captain_member = TeamMember.objects.get(
            team=team,
            user=request.user,
            role='captain',
            status='active'
        )
        
        # Transfer captaincy
        new_captain_member.role = 'captain'
        new_captain_member.save()
        
        current_captain_member.role = 'member'
        current_captain_member.save()
        
        team.captain = new_captain_member.user
        team.save()
        
        # Notify new captain
        from .notification_service import TeamNotificationService
        TeamNotificationService.notify_captaincy_transfer(new_captain_member.user, team, request.user)
        
        messages.success(request, f'Captaincy transferred to {new_captain_member.user.get_display_name()}.')
        return redirect('teams:detail', slug=slug)


class TeamDisbandView(LoginRequiredMixin, TeamCaptainRequiredMixin, View):
    """Disband a team (captain only)"""
    
    def post(self, request, slug):
        team = get_object_or_404(Team, slug=slug)
        
        # Set team status to disbanded
        team.status = 'disbanded'
        team.save()
        
        # Get all active members for notifications
        active_members = list(team.members.filter(status='active').select_related('user'))
        
        # Set all members to inactive
        team.members.filter(status='active').update(
            status='inactive',
            left_at=timezone.now()
        )
        
        # Send notifications to all members
        from .notification_service import TeamNotificationService
        TeamNotificationService.notify_team_disbanded(team, request.user, active_members)
        
        messages.success(request, f'Team "{team.name}" has been disbanded.')
        return redirect('teams:list')


class TeamMemberRemoveView(LoginRequiredMixin, TeamCaptainOrCoCaptainRequiredMixin, View):
    """Remove a team member"""
    
    def post(self, request, slug, member_id):
        team = get_object_or_404(Team, slug=slug)
        member = get_object_or_404(TeamMember, id=member_id, team=team, status='active')
        
        # Cannot remove captain
        if member.role == 'captain':
            messages.error(request, 'Cannot remove the team captain.')
            return redirect('teams:roster', slug=slug)
        
        # Set member to removed
        removed_user = member.user
        member.status = 'removed'
        member.left_at = timezone.now()
        member.save()
        
        # Send notification to removed user
        from .notification_service import TeamNotificationService
        TeamNotificationService.notify_member_removed(removed_user, team, request.user)
        
        messages.success(request, f'{removed_user.get_display_name()} has been removed from the team.')
        return redirect('teams:roster', slug=slug)


class TeamMemberRoleChangeView(LoginRequiredMixin, TeamCaptainRequiredMixin, View):
    """Change a team member's role (captain only)"""
    
    def post(self, request, slug, member_id):
        team = get_object_or_404(Team, slug=slug)
        member = get_object_or_404(TeamMember, id=member_id, team=team, status='active')
        
        new_role = request.POST.get('role')
        
        # Validate role
        valid_roles = ['member', 'co_captain', 'substitute']
        if new_role not in valid_roles:
            messages.error(request, 'Invalid role.')
            return redirect('teams:roster', slug=slug)
        
        # Cannot change captain role
        if member.role == 'captain':
            messages.error(request, 'Cannot change the captain role. Use transfer captaincy instead.')
            return redirect('teams:roster', slug=slug)
        
        # Update role
        old_role_value = member.role
        old_role = member.get_role_display()
        member.role = new_role
        member.save()
        
        # Send notification to user
        from .notification_service import TeamNotificationService
        TeamNotificationService.notify_role_change(member, old_role_value, new_role, team)
        
        messages.success(
            request,
            f'{member.user.get_display_name()} role changed from {old_role} to {member.get_role_display()}.'
        )
        return redirect('teams:roster', slug=slug)


# ============================================================================
# Team Tournament History
# ============================================================================

class TeamTournamentHistoryView(DetailView):
    """Team tournament history page (Requirement 13.5)"""
    model = Team
    template_name = 'teams/team_tournament_history.html'
    context_object_name = 'team'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object
        
        # Load team's tournament participations (Requirement 13.5)
        from tournaments.models import Participant
        tournament_history = Participant.objects.filter(
            team=team,
            status='confirmed'
        ).select_related(
            'tournament', 'tournament__game'
        ).order_by('-tournament__start_datetime')
        
        context['tournament_history'] = tournament_history
        
        # Categorize tournaments by result
        context['won_tournaments'] = tournament_history.filter(final_placement=1)
        context['participated_tournaments'] = tournament_history.exclude(final_placement=1)
        
        # Get achievements earned from tournaments (Requirement 13.5)
        tournament_achievement_types = [
            'first_win', 'tournament_champion', 'undefeated', 
            'comeback', 'dynasty', 'perfect_season', 'giant_slayer'
        ]
        context['tournament_achievements'] = team.achievements.filter(
            achievement_type__in=tournament_achievement_types
        ).order_by('-earned_at')
        
        # Calculate tournament statistics
        total_tournaments = tournament_history.count()
        won_count = context['won_tournaments'].count()
        
        context['tournament_stats'] = {
            'total': total_tournaments,
            'won': won_count,
            'win_rate': round((won_count / total_tournaments * 100), 2) if total_tournaments > 0 else 0,
            'top_3_finishes': tournament_history.filter(final_placement__lte=3).count(),
        }
        
        return context
