# Team Captain Registration Fix - Complete

## Issue Summary

Team captains were unable to register for team-based tournaments. When attempting to register, the system was incorrectly showing the message "You should join a team" instead of allowing the team captain to register their team for the tournament.

## Root Cause Analysis

The issue was in the `can_user_register` method in the `Tournament` model (`tournaments/models.py`). The method was only checking for individual user registration:

```python
# OLD CODE - PROBLEMATIC
if Participant.objects.filter(tournament=self, user=user).exists():
    return False, "You are already registered for this tournament"
```

For team-based tournaments, participant records are created with:
- `user=None` (no individual user)  
- `team=team_id` (the team that's registered)

The method wasn't checking if the user's team was already registered for team-based tournaments, and it wasn't validating that the user had eligible teams to register.

## Solution Implemented

Updated the `can_user_register` method to properly handle team-based tournaments:

```python
# NEW CODE - FIXED
def can_user_register(self, user):
    """Check if user can register for tournament with detailed error messages"""
    from django.utils import timezone
    
    # Check if already registered first
    if self.is_team_based:
        # For team-based tournaments, check if any of user's teams are registered
        try:
            from teams.models import Team, TeamMember
            user_teams = Team.objects.filter(
                members__user=user,
                members__status='active',
                members__role__in=['captain', 'co_captain'],
                status='active',
                game=self.game
            ).distinct()
            
            if Participant.objects.filter(tournament=self, team__in=user_teams).exists():
                return False, "Your team is already registered for this tournament"
            
            # Check if user has eligible teams to register
            if not user_teams.exists():
                return False, "You must be a captain or co-captain of an active team for this game to register"
                
        except ImportError:
            return False, "Team system not available"
    else:
        # For individual tournaments, check user registration
        if Participant.objects.filter(tournament=self, user=user).exists():
            return False, "You are already registered for this tournament"
    
    # ... rest of the method continues with other validation checks
```

## Key Changes

1. **Team-based Tournament Detection**: Added check for `self.is_team_based` to handle team tournaments differently
2. **Team Eligibility Check**: Validates that the user is a captain or co-captain of an active team for the tournament's game
3. **Team Registration Check**: Checks if any of the user's eligible teams are already registered
4. **Proper Error Messages**: Provides clear feedback about why registration is not available

## Validation

The fix has been tested and verified to work correctly:

✅ **Team captains can register**: Captains and co-captains can now register their teams for tournaments  
✅ **Duplicate prevention**: System properly prevents teams from registering multiple times  
✅ **Non-captain blocking**: Regular team members cannot register teams (only captains/co-captains can)  
✅ **Game matching**: Only teams for the correct game can register  
✅ **Individual tournaments**: Individual tournament registration continues to work as before  

## User Flow (Fixed)

1. Team captain navigates to team-based tournament
2. Clicks "Register Now" 
3. System checks if user is captain/co-captain of eligible team
4. If eligible, shows registration form with team selection
5. Captain selects team and submits registration
6. System creates participant record with `team=selected_team, user=None`
7. Registration completes successfully

## Files Modified

- `tournaments/models.py` - Updated `can_user_register` method

## Testing

Created comprehensive tests to verify the fix:
- `test_team_captain_registration_fix.py` - Detailed test suite
- `test_team_captain_fix_simple.py` - Simple validation test

Both tests pass, confirming the fix works correctly.

## Impact

This fix resolves the core issue preventing team captains from registering for team-based tournaments. Team tournament registration now works as intended, allowing captains and co-captains to register their teams while maintaining proper validation and duplicate prevention.