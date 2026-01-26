# Testing the Tournament System

## Quick Test Guide

Your tournament system is now ready to test through ngrok!

## Prerequisites

✅ Django server running: `python manage.py runserver`  
✅ ngrok running: `ngrok http 8000`  
✅ ngrok URL: `https://2c3e7ebf57f1.ngrok-free.app`

## Test Scenarios

### 1. Basic Page Load

**URL**: `https://2c3e7ebf57f1.ngrok-free.app/tournaments/`

**Expected**:
- Page loads without errors
- Tournament cards displayed in grid
- Search bar visible
- Filter dropdowns visible
- Pagination controls (if >12 tournaments)

### 2. Search Functionality

**Steps**:
1. Enter text in search box (e.g., "Championship")
2. Click "Filter" button or press Enter

**Expected**:
- Only tournaments with search term in name/description shown
- Results update immediately
- No page errors

**Property Validated**: Search Result Relevance (Property 8)

### 3. Status Filter

**Steps**:
1. Select "Registration Open" from status dropdown
2. Form auto-submits

**Expected**:
- Only tournaments with "Registration Open" status shown
- Green status badge visible on all cards
- Other statuses not shown

**Property Validated**: Status Filter Consistency (Property 1)

### 4. Game Filter

**Steps**:
1. Select a game from game dropdown
2. Form auto-submits

**Expected**:
- Only tournaments for selected game shown
- Game name visible on all cards
- Other games not shown

**Property Validated**: Game Filter Consistency (Property 1)

### 5. Combined Filters

**Steps**:
1. Enter search term: "Tournament"
2. Select status: "In Progress"
3. Select game: (any game)
4. Click "Filter"

**Expected**:
- Results match ALL filters (AND logic)
- Only tournaments matching all criteria shown
- Filter values preserved in form

**Property Validated**: Combined Filters Consistency (Property 1)

### 6. Tournament Card Information

**For each tournament card, verify**:
- ✅ Tournament name displayed
- ✅ Game name displayed
- ✅ Status badge displayed (colored)
- ✅ Participant count (e.g., "8/16")
- ✅ Start date displayed
- ✅ Prize pool displayed (if > 0)
- ✅ Description preview (truncated)

**Property Validated**: Card Information Completeness (Property 2)

### 7. Pagination

**Steps** (if you have >12 tournaments):
1. Apply a filter (e.g., status = "Registration")
2. Click "Next" page
3. Verify URL includes filter parameters
4. Click "Previous" page

**Expected**:
- Filters preserved across pages
- Page numbers update correctly
- Results consistent with filters

### 8. Responsive Layout

**Desktop** (>1024px):
- 3 columns of tournament cards
- Filters in single row
- Full card details visible

**Tablet** (768-1024px):
- 2 columns of tournament cards
- Filters may wrap
- Card details visible

**Mobile** (<768px):
- 1 column of tournament cards
- Filters stack vertically
- Touch-friendly buttons

**Property Validated**: Responsive Layout Adaptation (Property 9)

### 9. Featured Tournaments

**Expected**:
- Featured section at top (if any featured tournaments)
- Up to 3 featured tournaments shown
- Larger/prominent display
- Separate from main list

### 10. Empty State

**Steps**:
1. Apply filters that return no results
2. Or view page with no tournaments

**Expected**:
- "No Tournaments Found" message
- Helpful text suggesting filter adjustment
- No errors or broken layout

## Mobile Testing

### On Your Phone

1. Open browser on phone
2. Go to: `https://2c3e7ebf57f1.ngrok-free.app/tournaments/`
3. Test:
   - Single column layout
   - Touch targets (buttons, filters)
   - Search input
   - Filter dropdowns
   - Card tapping (should navigate)
   - Scrolling
   - Pagination

## Performance Testing

### Check ngrok Web Interface

1. Open: `http://localhost:4040`
2. View requests to `/tournaments/`
3. Check response times
4. Verify no errors

### Expected Performance
- Page load: <2 seconds
- Filter application: <1 second
- No 500 errors
- No database query issues

## Property Test Verification

Run the automated tests:

```bash
python manage.py test tournaments.test_properties --verbosity=2
```

**Expected Output**:
```
Ran 7 tests in ~10-15s
OK
```

All tests should PASS ✅

## Common Issues & Solutions

### Issue: "Invalid HTTP_HOST header"
**Solution**: 
- Verify ngrok URL in ALLOWED_HOSTS
- Restart Django server

### Issue: CSRF Token Error
**Solution**:
- Clear browser cookies
- Use HTTPS (not HTTP)
- Verify CSRF_TRUSTED_ORIGINS includes ngrok

### Issue: No Tournaments Showing
**Solution**:
- Create test tournaments in Django admin
- Check database connection
- Verify Tournament.is_public = True

### Issue: Filters Not Working
**Solution**:
- Check browser console for JavaScript errors
- Verify form submission
- Check view queryset filtering

## Creating Test Data

### Via Django Admin

1. Go to: `https://2c3e7ebf57f1.ngrok-free.app/admin/`
2. Login with superuser credentials
3. Navigate to Tournaments
4. Create test tournaments with:
   - Different statuses
   - Different games
   - Different formats
   - Various participant counts
   - Different prize pools

### Via Django Shell

```bash
python manage.py shell
```

```python
from tournaments.models import Tournament
from core.models import Game, User
from django.utils import timezone
from datetime import timedelta

# Create test game
game = Game.objects.create(
    name="Test Game",
    slug="test-game",
    genre="fps"
)

# Create organizer
organizer = User.objects.create(
    email="organizer@test.com",
    username="organizer"
)

# Create tournament
now = timezone.now()
tournament = Tournament.objects.create(
    name="Test Tournament",
    slug="test-tournament",
    description="This is a test tournament",
    game=game,
    format="single_elim",
    status="registration",
    organizer=organizer,
    max_participants=16,
    min_participants=4,
    registration_start=now,
    registration_end=now + timedelta(days=7),
    check_in_start=now + timedelta(days=7, hours=1),
    start_datetime=now + timedelta(days=7, hours=2),
    prize_pool=1000.00,
    is_public=True
)
```

## Success Criteria

✅ All 7 property tests pass  
✅ Page loads without errors  
✅ Search returns correct results  
✅ Filters work independently  
✅ Filters work in combination  
✅ Pagination preserves filters  
✅ Responsive layout works on all devices  
✅ Tournament cards show all required info  
✅ No console errors  
✅ No database errors  

## Next Steps After Testing

Once testing is complete:
1. Document any issues found
2. Verify all requirements met
3. Proceed to Task 2 (Tournament Detail Template)
4. Continue with remaining tasks

## Support

- See `NGROK_SETUP.md` for ngrok help
- See `TASK_1_COMPLETE_SUMMARY.md` for implementation details
- See `.kiro/specs/tournament-system/` for full specifications

---

**Happy Testing! 🎮🏆**
