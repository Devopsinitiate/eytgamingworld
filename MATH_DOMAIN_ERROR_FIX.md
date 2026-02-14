# Math Domain Error Fix for Bracket Generation

## Issue
When clicking "Generate Bracket", users encountered a `ValueError: math domain error` caused by attempting to calculate `math.log2(0)` when there were no checked-in participants.

## Root Cause
The error occurred in the `next_power_of_two` method when:
1. No participants were checked in (`participant_count = 0`)
2. `math.log2(0)` was called, which is mathematically undefined
3. This caused a `ValueError: math domain error`

## Complete Fix Applied

### 1. Fixed `next_power_of_two` Method
**Before:**
```python
def next_power_of_two(self, n: int) -> int:
    return 2 ** math.ceil(math.log2(n))  # Fails when n = 0
```

**After:**
```python
def next_power_of_two(self, n: int) -> int:
    if n <= 0:
        return 2  # Minimum bracket size
    if n == 1:
        return 2  # Single participant needs at least 2 slots
    return 2 ** math.ceil(math.log2(n))
```

### 2. Added Validation to All Bracket Generation Methods

#### Single Elimination
```python
def generate_single_elimination(self):
    if self.participant_count < 1:
        raise ValueError("Cannot generate bracket with no participants")
    # ... rest of method
```

#### Double Elimination
```python
def generate_double_elimination(self):
    if self.participant_count < 2:
        raise ValueError("Double elimination requires at least 2 participants")
    # ... rest of method
```

#### Swiss System
```python
def generate_swiss_rounds(self):
    if self.participant_count < 2:
        raise ValueError("Swiss system requires at least 2 participants")
    # ... rest of method
```

#### Round Robin
```python
def generate_round_robin(self):
    if self.participant_count < 2:
        raise ValueError("Round robin requires at least 2 participants")
    # ... rest of method
```

### 3. Enhanced Tournament Model Validation
```python
def create_bracket(self):
    participants = list(self.participants.filter(checked_in=True, status='confirmed'))
    
    # Validate we have participants
    if not participants:
        raise ValueError("Cannot generate bracket: No checked-in participants found")
    
    generator = BracketGenerator(self, participants)
    
    try:
        # Generate bracket based on format
        if self.format == 'single_elim':
            return generator.generate_single_elimination()
        # ... other formats
    except ValueError as e:
        raise ValueError(f"Bracket generation failed: {str(e)}")
```

### 4. Improved View Error Handling
```python
def generate_bracket(request, slug):
    try:
        tournament.brackets.all().delete()
        tournament.create_bracket()
        messages.success(request, 'Bracket generated successfully!')
        return redirect('tournaments:bracket', slug=slug)
        
    except ValueError as e:
        messages.error(request, f'Cannot generate bracket: {str(e)}')
        return redirect('tournaments:detail', slug=slug)
        
    except Exception as e:
        logger.error(f'Bracket generation failed for tournament {slug}: {str(e)}')
        messages.error(request, 'An error occurred while generating the bracket. Please try again.')
        return redirect('tournaments:detail', slug=slug)
```

## User Experience Improvements

### Error Messages
Users now see helpful error messages instead of server errors:
- ✅ "Cannot generate bracket: No checked-in participants found"
- ✅ "Cannot generate bracket: Double elimination requires at least 2 participants"
- ✅ "Cannot generate bracket: Swiss system requires at least 2 participants"
- ✅ "Cannot generate bracket: Round robin requires at least 2 participants"

### Graceful Handling
- ✅ No more 500 Internal Server Error
- ✅ User stays on tournament detail page with error message
- ✅ Clear feedback about what went wrong
- ✅ Guidance on how to fix the issue

## Validation Rules

| Tournament Format | Minimum Participants | Error Message |
|------------------|---------------------|---------------|
| Single Elimination | 1 | "Cannot generate bracket with no participants" |
| Double Elimination | 2 | "Double elimination requires at least 2 participants" |
| Swiss System | 2 | "Swiss system requires at least 2 participants" |
| Round Robin | 2 | "Round robin requires at least 2 participants" |

## Files Modified

1. **tournaments/services/bracket_generator.py**
   - Fixed `next_power_of_two` method with proper validation
   - Added participant count validation to all generation methods
   - Improved error messages

2. **tournaments/models.py**
   - Enhanced `create_bracket` method with validation
   - Added proper error handling and re-raising

3. **tournaments/views.py**
   - Added comprehensive error handling in `generate_bracket` view
   - User-friendly error messages
   - Proper logging for debugging

## Testing Scenarios

✅ **No Participants**: Clear error message, no crash
✅ **Single Participant**: Works for single elimination, proper error for other formats
✅ **Multiple Participants**: All formats work correctly
✅ **Edge Cases**: Proper handling of unusual participant counts

The bracket generation system now handles all edge cases gracefully and provides clear feedback to users.