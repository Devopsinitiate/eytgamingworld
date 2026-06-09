"""
Views for the teams app: CRUD, membership, invites, announcements, achievements.
"""
import json
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, View
from django.views.generic.edit import FormView
from django.utils import timezone
from datetime import timedelta

from core.models import User
from .models import Team, TeamMember, TeamInvite, TeamAnnouncement, TeamAchievement
from .forms import TeamCreateForm


class TeamListView(ListView):
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'
    paginate_by = 20

    def get_queryset(self):
        qs = Team.objects.filter(status='active', is_public=True)
        game = self.request.GET.get('game')
        if game:
            qs = qs.filter(game__slug=game)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs.select_related('game', 'captain')


class TeamDetailView(DetailView):
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'

    def get_queryset(self):
        return Team.objects.select_related('game', 'captain').prefetch_related(
            'members__user', 'announcements', 'achievements',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        team = self.get_object()
        ctx['members'] = team.members.filter(status='active').select_related('user')
        ctx['announcements'] = team.announcements.all()[:5]
        ctx['achievements'] = team.achievements.all()[:5]
        if self.request.user.is_authenticated:
            ctx['is_member'] = team.members.filter(user=self.request.user, status='active').exists()
        return ctx


class TeamCreateView(LoginRequiredMixin, CreateView):
    model = Team
    form_class = TeamCreateForm
    template_name = 'teams/team_form.html'

    def form_valid(self, form):
        team = form.save(commit=False)
        team.captain = self.request.user
        team.save()
        TeamMember.objects.create(
            team=team, user=self.request.user,
            role='captain', status='active',
        )
        return redirect(team.get_absolute_url())

    def get_success_url(self):
        return self.object.get_absolute_url()


class TeamSettingsView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Team
    form_class = TeamCreateForm
    template_name = 'teams/team_settings.html'

    def test_func(self):
        team = self.get_object()
        return team.members.filter(
            user=self.request.user, role__in=['captain', 'co_captain'], status='active',
        ).exists()


class TeamRosterView(LoginRequiredMixin, DetailView):
    model = Team
    template_name = 'teams/team_roster.html'
    context_object_name = 'team'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        team = self.get_object()
        ctx['members'] = team.members.select_related('user').order_by('role', '-joined_at')
        return ctx


class TeamInvitesView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Team
    template_name = 'teams/team_invites.html'
    context_object_name = 'team'

    def test_func(self):
        team = self.get_object()
        return team.members.filter(
            user=self.request.user, role__in=['captain', 'co_captain'], status='active',
        ).exists()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pending_invites'] = self.get_object().invites.filter(status='pending')
        return ctx


class TeamInviteSendView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        team = Team.objects.get(slug=self.kwargs['slug'])
        return team.members.filter(
            user=self.request.user, role__in=['captain', 'co_captain'], status='active',
        ).exists()

    def post(self, request, slug):
        team = get_object_or_404(Team, slug=slug)
        username = request.POST.get('username')
        invited_user = get_object_or_404(User, username=username)
        TeamInvite.objects.create(
            team=team,
            invited_by=request.user,
            invited_user=invited_user,
            expires_at=timezone.now() + timedelta(days=7),
        )
        return redirect('teams:invites', slug=slug)


class TeamInviteCancelView(LoginRequiredMixin, View):
    def post(self, request, slug, invite_id):
        invite = get_object_or_404(TeamInvite, id=invite_id, team__slug=slug, status='pending')
        invite.status = 'expired'
        invite.save()
        return redirect('teams:invites', slug=slug)


class TeamInviteAcceptView(LoginRequiredMixin, View):
    def post(self, request, invite_id):
        invite = get_object_or_404(TeamInvite, id=invite_id, invited_user=request.user, status='pending')
        with transaction.atomic():
            invite.status = 'accepted'
            invite.responded_at = timezone.now()
            invite.save()
            TeamMember.objects.create(
                team=invite.team, user=request.user, role='member', status='active',
                approved_at=timezone.now(),
            )
        return redirect('teams:detail', slug=invite.team.slug)


class TeamInviteDeclineView(LoginRequiredMixin, View):
    def post(self, request, invite_id):
        invite = get_object_or_404(TeamInvite, id=invite_id, invited_user=request.user, status='pending')
        invite.status = 'declined'
        invite.responded_at = timezone.now()
        invite.save()
        return redirect('teams:list')


class TeamUserSearchView(LoginRequiredMixin, View):
    def get(self, request):
        q = request.GET.get('q', '')
        users = User.objects.filter(username__icontains=q)[:10] if q else []
        data = [{'id': u.id, 'username': u.username, 'display_name': u.get_display_name()} for u in users]
        return JsonResponse(data, safe=False)


class TeamApplyView(LoginRequiredMixin, FormView):
    template_name = 'teams/team_apply.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['team'] = get_object_or_404(Team, slug=self.kwargs['slug'])
        return ctx

    def post(self, request, slug):
        team = get_object_or_404(Team, slug=slug)
        TeamMember.objects.get_or_create(team=team, user=request.user, defaults={'role': 'member'})
        return redirect('teams:detail', slug=slug)


class TeamApplicationsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Team
    template_name = 'teams/team_applications.html'
    context_object_name = 'team'

    def test_func(self):
        team = self.get_object()
        return team.members.filter(
            user=self.request.user, role__in=['captain', 'co_captain'], status='active',
        ).exists()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pending_members'] = self.get_object().members.filter(status='pending')
        return ctx


class TeamApplicationApproveView(LoginRequiredMixin, View):
    def post(self, request, slug, member_id):
        member = get_object_or_404(TeamMember, id=member_id, team__slug=slug, status='pending')
        member.status = 'active'
        member.approved_at = timezone.now()
        member.save()
        return redirect('teams:applications', slug=slug)


class TeamApplicationDeclineView(LoginRequiredMixin, View):
    def post(self, request, slug, member_id):
        member = get_object_or_404(TeamMember, id=member_id, team__slug=slug, status='pending')
        member.status = 'removed'
        member.save()
        return redirect('teams:applications', slug=slug)


class TeamAnnouncementsView(LoginRequiredMixin, DetailView):
    model = Team
    template_name = 'teams/team_announcements.html'
    context_object_name = 'team'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['announcements'] = self.get_object().announcements.select_related('posted_by').all()
        return ctx


class TeamAnnouncementPostView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        team = Team.objects.get(slug=self.kwargs['slug'])
        return team.members.filter(
            user=self.request.user, role__in=['captain', 'co_captain'], status='active',
        ).exists()

    def post(self, request, slug):
        team = get_object_or_404(Team, slug=slug)
        TeamAnnouncement.objects.create(
            team=team,
            posted_by=request.user,
            title=request.POST.get('title', ''),
            content=request.POST.get('content', ''),
            priority=request.POST.get('priority', 'normal'),
        )
        return redirect('teams:announcements', slug=slug)


class TeamStatsView(DetailView):
    model = Team
    template_name = 'teams/team_stats.html'
    context_object_name = 'team'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        team = self.get_object()
        ctx['member_stats'] = team.members.filter(status='active').select_related('user')
        return ctx


class TeamAchievementsView(DetailView):
    model = Team
    template_name = 'teams/team_achievements.html'
    context_object_name = 'team'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        achievements = self.get_object().achievements.all()
        ctx['achievements'] = achievements

        tournament_types = ['first_win', 'tournament_champion', 'undefeated', 'comeback', 'dynasty']
        performance_types = ['win_streak', 'perfect_season', 'giant_slayer']
        milestone_types = ['getting_started', 'experienced', 'veterans', 'legends', 'full_roster']

        ctx['tournament_achievements'] = achievements.filter(achievement_type__in=tournament_types)
        ctx['performance_achievements'] = achievements.filter(achievement_type__in=performance_types)
        ctx['milestone_achievements'] = achievements.filter(achievement_type__in=milestone_types)
        ctx['tournament_achievements_count'] = ctx['tournament_achievements'].count()
        ctx['latest_achievement'] = achievements.first()
        return ctx


class TeamTournamentHistoryView(DetailView):
    model = Team
    template_name = 'teams/team_tournament_history.html'
    context_object_name = 'team'


class TeamLeaveView(LoginRequiredMixin, View):
    def post(self, request, slug):
        team = get_object_or_404(Team, slug=slug)
        membership = team.members.filter(user=request.user, status='active').first()
        if membership and membership.role != 'captain':
            membership.status = 'inactive'
            membership.left_at = timezone.now()
            membership.save()
        return redirect('teams:list')


class TeamDisbandView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        team = Team.objects.get(slug=self.kwargs['slug'])
        return team.members.filter(user=self.request.user, role='captain', status='active').exists()

    def post(self, request, slug):
        team = get_object_or_404(Team, slug=slug)
        team.status = 'disbanded'
        team.save()
        return redirect('teams:list')


class TeamTransferCaptaincyView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        team = Team.objects.get(slug=self.kwargs['slug'])
        return team.members.filter(user=self.request.user, role='captain', status='active').exists()

    def post(self, request, slug):
        team = get_object_or_404(Team, slug=slug)
        new_captain_id = request.POST.get('new_captain')
        with transaction.atomic():
            current_captain = team.members.get(user=request.user, role='captain', status='active')
            current_captain.role = 'member'
            current_captain.save()
            new_captain = team.members.get(id=new_captain_id, status='active')
            new_captain.role = 'captain'
            new_captain.save()
            team.captain = new_captain.user
            team.save()
        return redirect('teams:detail', slug=slug)


class TeamMemberRemoveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        team = Team.objects.get(slug=self.kwargs['slug'])
        return team.members.filter(
            user=self.request.user, role__in=['captain', 'co_captain'], status='active',
        ).exists()

    def post(self, request, slug, member_id):
        member = get_object_or_404(TeamMember, id=member_id, team__slug=slug, status='active')
        member.status = 'removed'
        member.left_at = timezone.now()
        member.save()
        return redirect('teams:roster', slug=slug)


class TeamMemberRoleChangeView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        team = Team.objects.get(slug=self.kwargs['slug'])
        return team.members.filter(user=self.request.user, role='captain', status='active').exists()

    def post(self, request, slug, member_id):
        member = get_object_or_404(TeamMember, id=member_id, team__slug=slug, status='active')
        new_role = request.POST.get('role', 'member')
        if new_role in dict(TeamMember.ROLE_CHOICES) and new_role != 'captain':
            member.role = new_role
            member.save()
        return redirect('teams:roster', slug=slug)
