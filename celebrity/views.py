from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import TemplateView, ListView

from datetime import timedelta

from core.models import User
from teams.models import Team, TeamTransfer, TeamAchievement
from teams.services import TeamValuationService


class CelebrityRequiredMixin(UserPassesTestMixin):
    """Mixin ensuring the user is a verified personality."""

    def test_func(self):
        return (
            self.request.user.is_authenticated and
            hasattr(self.request.user, 'is_verified_personality') and
            self.request.user.is_verified_personality
        )


class CelebrityHomeView(LoginRequiredMixin, CelebrityRequiredMixin, TemplateView):
    """Celebrity dashboard home — hero, portfolio summary, revenue, activity."""

    template_name = 'celebrity/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        owned_teams = Team.objects.filter(
            Q(owner=user) | Q(captain=user)
        ).distinct().select_related('game').prefetch_related('achievements')

        ctx['owned_teams'] = owned_teams
        ctx['team_count'] = owned_teams.count()

        total_value = sum(t.market_value for t in owned_teams)
        ctx['portfolio_value'] = total_value

        total_wins = sum(t.total_wins for t in owned_teams)
        total_games = total_wins + sum(t.total_losses for t in owned_teams)
        ctx['total_wins'] = total_wins
        ctx['overall_win_rate'] = round((total_wins / total_games * 100), 1) if total_games > 0 else 0

        recent = []
        for t in owned_teams:
            for a in t.achievements.all()[:3]:
                recent.append({'team': t, 'achievement': a, 'date': a.earned_at})
        recent.sort(key=lambda x: x['date'], reverse=True)
        ctx['recent_achievements'] = recent[:10]

        pending_transfers = TeamTransfer.objects.filter(
            Q(from_user=user) | Q(to_user=user),
            status='pending',
        ).select_related('team')
        ctx['pending_transfers'] = pending_transfers

        return ctx


class CelebrityTeamsView(LoginRequiredMixin, CelebrityRequiredMixin, TemplateView):
    """Celebrity team portfolio — manage all owned teams."""

    template_name = 'celebrity/teams.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        owned_teams = Team.objects.filter(
            Q(owner=user) | Q(captain=user)
        ).distinct().select_related('game').prefetch_related('members__user')

        for team in owned_teams:
            team.valuation_tier_display = team.valuation_tier

        ctx['owned_teams'] = owned_teams
        ctx['remaining_slots'] = user.max_team_slots - owned_teams.count()
        ctx['max_slots'] = user.max_team_slots

        return ctx


class CelebritySponsorsView(LoginRequiredMixin, CelebrityRequiredMixin, TemplateView):
    """Sponsorship management — offers, active deals, budgets, tracking."""

    template_name = 'celebrity/sponsors.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        ctx['sponsorship_email'] = user.sponsorship_email

        active_deals = []
        pending_offers = []
        past_deals = []

        try:
            from sponsorships.models import SponsorshipDeal
            all_deals = SponsorshipDeal.objects.filter(celebrity=user).select_related('sponsor')
            for d in all_deals:
                if d.status == 'active':
                    active_deals.append(d)
                elif d.status == 'pending':
                    pending_offers.append(d)
                else:
                    past_deals.append(d)
        except ImportError:
            pass

        ctx['active_deals'] = active_deals
        ctx['pending_offers'] = pending_offers
        ctx['past_deals'] = past_deals
        ctx['active_deals_count'] = len(active_deals)
        ctx['total_earnings'] = sum(d.budget for d in active_deals if hasattr(d, 'budget'))

        return ctx


class CelebrityAnalyticsView(LoginRequiredMixin, CelebrityRequiredMixin, TemplateView):
    """Analytics dashboard — tournament stats, team performance."""

    template_name = 'celebrity/analytics.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        owned_teams = Team.objects.filter(
            Q(owner=user) | Q(captain=user)
        ).distinct().select_related('game')

        ctx['owned_teams'] = owned_teams
        ctx['team_count'] = owned_teams.count()

        if owned_teams:
            total_wins = sum(t.total_wins for t in owned_teams)
            total_losses = sum(t.total_losses for t in owned_teams)
            total_games = total_wins + total_losses
            ctx['total_wins'] = total_wins
            ctx['total_losses'] = total_losses
            ctx['overall_win_rate'] = round((total_wins / total_games * 100), 1) if total_games > 0 else 0
            ctx['total_tournaments'] = sum(t.tournaments_played for t in owned_teams)
            ctx['total_titles'] = sum(t.tournaments_won for t in owned_teams)
            ctx['total_portfolio_value'] = round(sum(t.market_value for t in owned_teams), 2)

            import json
            labels = [t.name for t in owned_teams]
            win_data = [t.total_wins for t in owned_teams]
            value_data = [float(t.market_value) for t in owned_teams]
            ctx['chart_labels'] = json.dumps(labels)
            ctx['chart_win_data'] = json.dumps(win_data)
            ctx['chart_value_data'] = json.dumps(value_data)
        else:
            ctx['total_wins'] = 0
            ctx['total_losses'] = 0
            ctx['overall_win_rate'] = 0
            ctx['total_tournaments'] = 0
            ctx['total_titles'] = 0
            ctx['total_portfolio_value'] = 0
            ctx['chart_labels'] = '[]'
            ctx['chart_win_data'] = '[]'
            ctx['chart_value_data'] = '[]'

        return ctx


class CelebrityVerificationView(LoginRequiredMixin, TemplateView):
    """Verification status and application form."""

    template_name = 'celebrity/verification.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        from core.models import PersonalityVerification
        existing = PersonalityVerification.objects.filter(user=user).order_by('-submitted_at').first()

        ctx['verification'] = existing
        ctx['is_verified'] = user.is_verified_personality
        ctx['account_tier'] = user.account_tier
        ctx['celebrity_bio'] = user.celebrity_bio
        ctx['sponsorship_email'] = user.sponsorship_email

        return ctx

    def post(self, request, *args, **kwargs):
        user = request.user

        from core.models import PersonalityVerification

        additional_info = request.POST.get('additional_info', '')
        celebrity_bio = request.POST.get('celebrity_bio', '')
        sponsorship_email = request.POST.get('sponsorship_email', '')

        if celebrity_bio:
            user.celebrity_bio = celebrity_bio
        if sponsorship_email:
            user.sponsorship_email = sponsorship_email
        user.save(update_fields=['celebrity_bio', 'sponsorship_email'])

        if not user.is_verified_personality and not PersonalityVerification.objects.filter(user=user, status='pending').exists():
            PersonalityVerification.objects.create(
                user=user,
                additional_info=additional_info,
                social_links={},
                follower_counts={},
            )
            messages.success(request, 'Your verification application has been submitted.')
        else:
            messages.success(request, 'Your profile settings have been updated.')

        return redirect('celebrity:verification')
