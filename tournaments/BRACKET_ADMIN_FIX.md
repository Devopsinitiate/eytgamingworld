# Bracket Admin Fix - Match Creation Error

**Date:** December 3, 2025  
**Issue:** IntegrityError when creating brackets with matches through Django admin  
**Status:** ✅ Fixed

## Problem

When attempting to create a bracket with matches through the Django admin panel, the following error occurred:

```
django.db.utils.IntegrityError: null value in column "round_number" of relation "tournament_matches" violates not-null constraint
```

**Error Details:**
- The `Match` model requires `round_number` and `match_number` to be non-null
- The `MatchInline` in the admin had these fields set as `readonly_fields`
- When creating new matches through the inline form, readonly fields are not editable
- This caused Django to attempt to save matches with `null` values for these required fields

## Root Cause

In `tournaments/admin.py`, the `MatchInline` configuration was:

```python
class MatchInline(admin.TabularInline):
    model = Match
    extra = 0
    fields = ['round_number', 'match_number', 'participant1', 'participant2', 
              'score_p1', 'score_p2', 'winner', 'status']
    readonly_fields = ['round_number', 'match_number']  # ❌ Problem here
    raw_id_fields = ['participant1', 'participant2', 'winner']
```

The `readonly_fields` setting prevented users from entering values for `round_number` and `match_number` when creating new matches.

## Solution

Removed `readonly_fields` from the `MatchInline` configuration to allow users to input these required values:

```python
class MatchInline(admin.TabularInline):
    model = Match
    extra = 0
    fields = ['round_number', 'match_number', 'participant1', 'participant2', 
              'score_p1', 'score_p2', 'winner', 'status']
    # Removed readonly_fields to allow editing round_number and match_number
    raw_id_fields = ['participant1', 'participant2', 'winner']
```

## Impact

**Before Fix:**
- ❌ Could not create brackets with matches through admin panel
- ❌ IntegrityError on save
- ❌ Matches could not be added inline when creating brackets

**After Fix:**
- ✅ Can create brackets with matches through admin panel
- ✅ Users can input round_number and match_number values
- ✅ Matches save successfully with all required fields

## Testing

To verify the fix:

1. Log into Django admin: `/admin/`
2. Navigate to Tournaments → Brackets
3. Click "Add Bracket"
4. Fill in bracket details
5. Add matches using the inline form
6. Enter values for round_number and match_number
7. Save the bracket

The bracket and matches should save successfully without errors.

## Alternative Solutions Considered

1. **Add default values to the model:**
   - Could set `round_number = models.IntegerField(default=1)`
   - Rejected: Round numbers should be explicitly set, not defaulted

2. **Override save method to auto-calculate:**
   - Could auto-calculate round_number based on bracket structure
   - Rejected: Too complex for admin use case, better handled by bracket generation logic

3. **Make fields nullable:**
   - Could change to `round_number = models.IntegerField(null=True, blank=True)`
   - Rejected: These fields are essential for bracket structure and should be required

## Related Files

- `eytgaming/tournaments/admin.py` - Fixed MatchInline configuration
- `eytgaming/tournaments/models.py` - Match model with required fields

## Notes

- The `readonly_fields` setting is useful for preventing edits to existing matches
- For new match creation, users need to be able to set these values
- Consider adding validation to ensure round_number and match_number are positive integers
- Future enhancement: Add JavaScript to auto-populate these fields based on bracket structure
