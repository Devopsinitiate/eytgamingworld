# Team List Property Conflict Fix

**Date:** December 3, 2025  
**Issue:** AttributeError when accessing team list page  
**Status:** ✅ Fixed

## Problem

When clicking "Teams" in the dashboard, the following error occurred:

```
AttributeError: property 'member_count' of 'Team' object has no setter
```

**Error Details:**
- The `TeamListView` was using `.annotate(member_count=...)` to count members
- The `Team` model has a `@property` named `member_count`
- Django's ORM tried to set the annotated value on the property
- Properties are read-only by default (no setter), causing the error

## Root Cause

In `teams/views.py`, the `TeamListView.get_queryset()` was annotating with names that conflicted with model properties:

```python
queryset = Team.objects.filter(
    status='active',
    is_public=True
).select_related('game', 'captain').annotate(
    member_count=Count('members', filter=Q(members__status='active')),  # ❌ Conflicts with @property
    achievement_count=Count('achievements')  # ❌ Potential conflict
)
```

The Team model has:
```python
@property
def member_count(self):
    return self.members.filter(status='active').count()
```

When Django tries to populate the queryset results, it attempts to set `obj.member_count = <annotated_value>`, but since `member_count` is a property without a setter, it fails.

## Solution

Renamed the annotations to avoid conflicts with model properties:

**1. Updated `teams/views.py`:**
```python
queryset = Team.objects.filter(
    status='active',
    is_public=True
).select_related('game', 'captain').annotate(
    annotated_member_count=Count('members', filter=Q(members__status='active')),
    annotated_achievement_count=Count('achievements')
)
```

**2. Updated `templates/teams/team_list.html`:**
- Changed `{{ team.member_count }}` → `{{ team.annotated_member_count }}`
- Changed `{{ team.achievement_count }}` → `{{ team.annotated_achievement_count }}`

## Benefits

1. **Avoids Property Conflicts:** Annotations no longer conflict with model properties
2. **Better Performance:** Uses pre-calculated annotated values instead of triggering additional queries
3. **Clearer Intent:** The `annotated_` prefix makes it clear these are database annotations
4. **Maintains Compatibility:** The original properties still work elsewhere in the codebase

## Impact

**Before Fix:**
- ❌ Team list page crashed with AttributeError
- ❌ Could not access /teams/ URL
- ❌ Dashboard "Teams" link was broken

**After Fix:**
- ✅ Team list page loads successfully
- ✅ Member counts display correctly
- ✅ Achievement counts display correctly
- ✅ Better query performance (single query instead of N+1)

## Testing

To verify the fix:

1. Navigate to `/teams/` or click "Teams" in the dashboard
2. Verify the page loads without errors
3. Check that member counts show correctly (e.g., "5/10")
4. Check that achievement badges display when teams have achievements
5. Test search and filter functionality

## Related Files

- `eytgaming/teams/views.py` - Updated annotation names in TeamListView
- `eytgaming/templates/teams/team_list.html` - Updated template to use new annotation names
- `eytgaming/teams/models.py` - Team model with member_count property (unchanged)

## Best Practices

**Avoiding Annotation Conflicts:**

1. **Use Descriptive Names:** Prefix annotations with `annotated_` or `computed_` to avoid conflicts
2. **Check Model Properties:** Before adding annotations, check if the model has properties with the same name
3. **Document Annotations:** Add comments explaining what each annotation calculates
4. **Consistent Naming:** Use a consistent naming convention across the project

**Example:**
```python
# Good - Clear and avoids conflicts
.annotate(
    annotated_member_count=Count('members'),
    computed_win_rate=F('wins') / F('total_games')
)

# Bad - May conflict with properties
.annotate(
    member_count=Count('members'),  # Conflicts with @property
    win_rate=F('wins') / F('total_games')  # May conflict
)
```

## Notes

- The original `member_count` property is still available and works correctly
- Other views and templates using `team.member_count` will use the property (which is fine)
- The team list view now uses the optimized annotated value for better performance
- This pattern should be applied to other list views that use annotations
