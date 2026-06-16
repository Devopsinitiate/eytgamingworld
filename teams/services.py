from decimal import Decimal
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from teams.models import Team


class TeamValuationService:
    """Calculate team market value based on performance, roster, and activity."""

    BASE_VALUE = Decimal('1000.00')
    WIN_VALUE = Decimal('50.00')
    TOURNAMENT_WIN_VALUE = Decimal('500.00')
    MEMBER_VALUE = Decimal('200.00')
    STREAK_BONUS = Decimal('0.10')

    @classmethod
    def calculate(cls, team):
        """Calculate and return the market value for a team."""
        value = cls.BASE_VALUE

        win_value = Decimal(str(team.total_wins)) * cls.WIN_VALUE
        value += win_value

        tournament_value = Decimal(str(team.tournaments_won)) * cls.TOURNAMENT_WIN_VALUE
        value += tournament_value

        active_members = team.members.filter(status='active').count()
        member_value = Decimal(str(active_members)) * cls.MEMBER_VALUE
        value += member_value

        total_games = team.total_wins + team.total_losses
        if total_games > 10:
            win_rate = team.total_wins / total_games
            if win_rate >= 0.60:
                bonus = value * cls.STREAK_BONUS
                value += bonus

        return max(value, cls.BASE_VALUE)

    @classmethod
    def update_team_value(cls, team):
        """Recalculate and persist the team's market value."""
        new_value = cls.calculate(team)
        Team.objects.filter(pk=team.pk).update(
            market_value=new_value,
            updated_at=timezone.now()
        )
        return new_value
