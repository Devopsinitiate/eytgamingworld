# Team Leave Bug Fix Design Document

## Overview

This document outlines the design for fixing the critical bug in the team leave functionality. The current implementation uses incorrect Django ORM syntax (`Q(role='co_captain').desc()`) which causes an AttributeError when a team captain attempts to leave. The fix involves replacing the invalid Q object ordering with proper Django Case/When expressions to implement the captaincy transfer priority logic.

## Architecture

### Current Problem
The existing code attempts to use `.desc()` method on a Q object, which doesn't exist in Django ORM:

```python
new_captain = team.members.filter(
    status='active'
).exclude(
    user=request.user
).order_by(
    Q(role='co_captain').desc(),  # ❌ This is invalid
    'joined_at'
).first()
```

### Solution Architecture
Replace the invalid Q object ordering with Django's Case/When expressions for conditional ordering:

```python
from django.db.models import Case, When, Value, IntegerField

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
```

## Components and Interfaces

### 1. TeamLeaveView (teams/views.py)

**Current Implementation Issues:**
- Uses invalid `Q(role='co_captain').desc()` syntax
- Causes AttributeError when executed
- Prevents captain leave functionality

**Fixed Implementation:**
- Use Django Case/When for conditional ordering
- Maintain the same priority logic (co-captain first, then by join date)
- Ensure proper error handling

**Method Signature:**
```python
def post(self, request, slug):
    # Implementation details below
```

### 2. Captaincy Transfer Logic

**Priority Order:**
1. **Co-Captain**: Highest priority (Case When role='co_captain' then 0)
2. **Regular Members**: Lower priority (default value 1)
3. **Join Date**: Secondary sort for tie-breaking ('joined_at' ascending)

**Implementation Strategy:**
```python
# Priority ordering using Case/When
Case(
    When(role='co_captain', then=Value(0)),  # Co-captains get priority 0
    default=Value(1),                        # Others get priority 1
    output_field=IntegerField()
),
'joined_at'  # Oldest member wins ties
```

### 3. Error Handling Flow

**Success Path:**
1. Find suitable new captain using corrected query
2. Transfer captaincy (update member role and team captain)
3. Set leaving member to inactive
4. Display success message with new captain name
5. Redirect to teams list

**Edge Cases:**
1. **No other members**: Disband team, set status to disbanded
2. **Query returns None**: Handle gracefully, disband team
3. **Database errors**: Display error message, don't complete leave

## Data Models

### Existing Models (No Changes Required)

**Team Model:**
- `captain` (FK to User) - Updated when captaincy transfers
- `status` (CharField) - Set to 'disbanded' when no members remain

**TeamMember Model:**
- `role` (CharField) - Updated for new captain ('captain')
- `status` (CharField) - Set to 'inactive' for leaving member
- `left_at` (DateTimeField) - Set to current timestamp
- `joined_at` (DateTimeField) - Used for tie-breaking in captain selection

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Query Execution Success
*For any* team with active members, the captaincy transfer query should execute without raising AttributeError
**Validates: Requirements 3.2, 3.5**

### Property 2: Co-Captain Priority
*For any* team with both co-captains and regular members, when a captain leaves, a co-captain should be selected as the new captain
**Validates: Requirements 1.3, 2.1**

### Property 3: Co-Captain Tie-Breaking
*For any* team with multiple co-captains, when a captain leaves, the co-captain who joined earliest should be selected
**Validates: Requirements 2.2**

### Property 4: Regular Member Selection
*For any* team with only regular members (no co-captains), when a captain leaves, the member who joined earliest should be selected
**Validates: Requirements 1.4, 2.3**

### Property 5: Data Consistency After Transfer
*For any* successful captaincy transfer, the new captain's role should be 'captain' and the team's captain field should reference the new captain's user
**Validates: Requirements 2.5, 5.2, 5.3**

### Property 6: Leaving Member Status Update
*For any* captain leave operation, the leaving member's status should be set to inactive and left_at timestamp should be recorded
**Validates: Requirements 5.1, 5.5**

### Property 7: Team Disbanding Data Consistency
*For any* team where the captain is the only active member, when the captain leaves, the team status should be set to disbanded
**Validates: Requirements 5.4**

### Property 8: Captaincy Transfer Correctness
*For any* team configuration, the selected new captain should be the member with the highest priority according to the rules (co-captain role first, then earliest join date)
**Validates: Requirements 1.2, 3.3**

## Error Handling

### Database Query Errors
- **Invalid Syntax**: Fixed by using proper Case/When expressions
- **Empty Results**: Handle gracefully by disbanding team
- **Multiple Results**: Prevented by using `.first()` method

### Business Logic Errors
- **Captain Not Found**: Validate membership before processing
- **Invalid Team State**: Check team status before allowing leave
- **Permission Errors**: Verify user is actually the captain

### User Experience Errors
- **Clear Error Messages**: Display specific error reasons
- **Graceful Degradation**: Allow user to retry or contact support
- **Consistent State**: Ensure UI reflects actual database state

## Testing Strategy

### Unit Tests
- Test captain leave with co-captain present
- Test captain leave with only regular members
- Test captain leave as last member (disbanding)
- Test error handling for invalid team states
- Test permission validation

### Property-Based Tests
We will use Hypothesis (Python property-based testing library) for property tests, configured to run a minimum of 100 iterations.

**Property Test Implementation:**
- Generate random team configurations (various member roles and join dates)
- Test captaincy transfer logic across all valid scenarios
- Verify query execution never raises AttributeError
- Validate priority ordering works correctly
- Ensure data consistency after operations

**Test Configuration:**
```python
from hypothesis import given, strategies as st
import pytest

@given(
    team_members=st.lists(
        st.tuples(
            st.sampled_from(['co_captain', 'member', 'substitute']),
            st.datetimes()
        ),
        min_size=1,
        max_size=10
    )
)
def test_captaincy_transfer_priority(team_members):
    # Property test implementation
```

### Integration Tests
- Test complete leave flow from HTTP request to database update
- Test notification system integration
- Test redirect behavior after successful leave
- Test UI state updates after captaincy transfer

## Implementation Details

### 1. Import Requirements
```python
from django.db.models import Case, When, Value, IntegerField
from django.utils import timezone
```

### 2. Fixed Query Implementation
```python
# Find co-captain or oldest member to transfer captaincy
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
```

### 3. Complete Method Implementation
```python
def post(self, request, slug):
    team = get_object_or_404(Team, slug=slug)
    
    # Get user's membership
    try:
        membership = TeamMember.objects.get(
            team=team,
            user=request.user,
            status='active'
        )
    except TeamMember.DoesNotExist:
        messages.error(request, 'You are not a member of this team.')
        return redirect('teams:detail', slug=slug)
    
    # Handle captain leaving
    if membership.role == 'captain':
        # Find co-captain or oldest member to transfer captaincy
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
            # Transfer captaincy
            new_captain.role = 'captain'
            new_captain.save()
            
            team.captain = new_captain.user
            team.save()
            
            messages.info(request, f'Captaincy transferred to {new_captain.user.get_display_name()}.')
        else:
            # No other members, disband team
            team.status = 'disbanded'
            team.save()
            messages.info(request, 'Team has been disbanded as you were the last member.')
    
    # Set member to inactive
    membership.status = 'inactive'
    membership.left_at = timezone.now()
    membership.save()
    
    # Notify team captain (if team still exists)
    if team.status != 'disbanded':
        from .notification_service import TeamNotificationService
        TeamNotificationService.notify_member_left(team, request.user)
    
    messages.success(request, f'You have left {team.name}.')
    return redirect('teams:list')
```

## Design Rationale

### Why Case/When Instead of Alternatives?

**Option 1: Multiple Queries**
```python
# Could do separate queries
co_captain = team.members.filter(status='active', role='co_captain').exclude(user=request.user).order_by('joined_at').first()
if not co_captain:
    regular_member = team.members.filter(status='active').exclude(user=request.user).order_by('joined_at').first()
```
**Rejected**: Multiple database queries, more complex logic, potential race conditions

**Option 2: Python Sorting**
```python
# Could sort in Python
members = list(team.members.filter(status='active').exclude(user=request.user))
members.sort(key=lambda m: (0 if m.role == 'co_captain' else 1, m.joined_at))
```
**Rejected**: Loads all members into memory, less efficient, not database-optimized

**Option 3: Case/When (Chosen)**
```python
# Single query with database-level sorting
Case(When(role='co_captain', then=Value(0)), default=Value(1), output_field=IntegerField())
```
**Selected**: Single database query, efficient, clear intent, database-optimized sorting

### Priority Logic Explanation

The Case/When expression assigns priority values:
- **Co-captains get 0**: Lowest number = highest priority
- **Others get 1**: Higher number = lower priority
- **joined_at ascending**: Oldest members first for tie-breaking

This ensures co-captains are always selected first, and among members of the same role, the oldest (by join date) is selected.

## Security Considerations

### Permission Validation
- Verify user is actually a team member before processing
- Confirm user has captain role before allowing captaincy transfer
- Validate team exists and is in valid state

### Data Integrity
- Use database transactions for multi-step operations
- Validate all updates before committing
- Handle concurrent modifications gracefully

### Input Validation
- Sanitize team slug parameter
- Validate user authentication
- Check for malicious input patterns

## Performance Considerations

### Database Optimization
- Single query instead of multiple queries
- Use database-level sorting instead of Python sorting
- Proper indexing on frequently queried fields (status, role, joined_at)

### Caching Strategy
- No caching needed for this operation (infrequent, requires fresh data)
- Clear any team-related caches after successful operation

## Monitoring and Logging

### Success Metrics
- Track successful captain leave operations
- Monitor captaincy transfer success rate
- Log team disbanding events

### Error Tracking
- Log any remaining AttributeErrors (should be zero after fix)
- Monitor for new edge cases or error patterns
- Track user experience issues

### Performance Monitoring
- Monitor query execution time
- Track database load from leave operations
- Alert on unusual error rates

## Rollback Plan

### Deployment Strategy
1. Deploy fix to staging environment
2. Run comprehensive tests including edge cases
3. Deploy to production during low-traffic period
4. Monitor error rates and user feedback

### Rollback Triggers
- Increase in leave operation errors
- User reports of failed captain transfers
- Database performance degradation
- Any new AttributeErrors

### Rollback Process
1. Revert to previous code version
2. Investigate root cause of issues
3. Apply additional fixes if needed
4. Re-deploy with enhanced testing

## Summary

This design fixes the critical team leave bug by replacing invalid Django ORM syntax with proper Case/When expressions. The solution maintains the existing priority logic (co-captain first, then by join date) while ensuring the query executes without errors. The fix is minimal, focused, and maintains backward compatibility with existing team data and user expectations.

The key improvement is using database-level conditional ordering instead of invalid Q object methods, which provides better performance and eliminates the AttributeError that was preventing captain leave operations from completing successfully.