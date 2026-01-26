# Design Document: Tournament System

## Overview

The Tournament System is a comprehensive competitive gaming platform built on Django that enables users to discover, register for, and participate in esports tournaments. The system leverages existing Django models (Tournament, Participant, Match, Bracket) and provides a modern, responsive frontend using Tailwind CSS and HTMX for dynamic interactions.

The architecture follows Django's MVT (Model-View-Template) pattern with class-based views for CRUD operations and function-based views for specific actions. The system integrates with the existing EYTGaming platform's authentication, payment, and notification systems.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Tournament  │  │  Tournament  │  │   Bracket    │      │
│  │     List     │  │    Detail    │  │     View     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Tournament  │  │  Participant │  │    Match     │      │
│  │    Views     │  │  Management  │  │  Management  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Bracket    │  │  Registration│                        │
│  │  Generator   │  │   Service    │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                        Data Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Tournament  │  │  Participant │  │    Match     │      │
│  │    Model     │  │    Model     │  │    Model     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Bracket    │  │    Dispute   │                        │
│  │    Model     │  │    Model     │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Request → URL Router → View → Model → Database
                              ↓
                          Template → Response
```

## Components and Interfaces

### 1. Tournament List Component

**Purpose**: Display all available tournaments with filtering and search capabilities

**Template**: `templates/tournaments/tournament_list.html`

**View**: `TournamentListView` (ListView)

**Key Features**:
- Grid layout (responsive: 1/2/3 columns)
- Search by tournament name/description
- Filter by game, status, format
- Pagination (12 per page)
- Tournament cards showing:
  - Name, description
  - Game logo and name
  - Status badge
  - Format badge
  - Participant count
  - Start date
  - Prize pool
  - Registration button

**Interface**:
```python
class TournamentListView(ListView):
    model = Tournament
    template_name = 'tournaments/tournament_list.html'
    context_object_name = 'tournaments'
    paginate_by = 12
    
    def get_queryset(self):
        # Filter by status, game, format, search
        pass
```

### 2. Tournament Detail Component

**Purpose**: Display comprehensive tournament information and enable registration

**Template**: `templates/tournaments/tournament_detail.html`

**View**: `TournamentDetailView` (DetailView)

**Key Features**:
- Tournament header with name, status, game
- Statistics cards (participants, max players, prize pool, format)
- Registration card (sidebar)
- Participant list
- Match list (if tournament started)
- Rules display
- Tournament timeline

**Interface**:
```python
class TournamentDetailView(DetailView):
    model = Tournament
    template_name = 'tournaments/tournament_detail.html'
    context_object_name = 'tournament'
    
    def get_context_data(self, **kwargs):
        # Add participants, matches, registration status
        pass
```

### 3. Tournament Registration Component

**Purpose**: Handle user registration for tournaments

**Template**: `templates/tournaments/tournament_register.html`

**View**: `tournament_register` (function-based view)

**Key Features**:
- Player information form
- Team selection (for team tournaments)
- Rules agreement checkbox
- Payment processing (if entry fee)
- Registration summary sidebar

**Interface**:
```python
@login_required
def tournament_register(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)
    can_register, message = tournament.can_user_register(request.user)
    
    if not can_register:
        # Handle error
        pass
    
    # Create participant
    Participant.objects.create(...)
    
    return redirect('tournaments:detail', slug=slug)
```

### 4. Bracket Visualization Component

**Purpose**: Display tournament bracket with match progression

**Template**: `templates/tournaments/bracket.html`

**View**: `BracketView` (DetailView)

**Key Features**:
- Round-by-round match display
- Participant names and scores
- Match status indicators
- Winner highlighting
- Zoom controls
- Responsive horizontal scrolling

**Interface**:
```python
class BracketView(DetailView):
    model = Tournament
    template_name = 'tournaments/bracket.html'
    
    def get_context_data(self, **kwargs):
        # Organize matches by bracket and round
        pass
```

### 5. Match Management Component

**Purpose**: Handle match score reporting and disputes

**Views**: 
- `match_report_score` (function-based)
- `match_dispute` (function-based)

**Key Features**:
- Score input form
- Winner determination
- Bracket progression
- Dispute filing
- Admin resolution

## Data Models

### Existing Models (Already Implemented)

#### Tournament Model
```python
class Tournament(models.Model):
    # Identity
    id = UUIDField(primary_key=True)
    name = CharField(max_length=200)
    slug = SlugField(unique=True)
    description = TextField()
    
    # Configuration
    game = ForeignKey(Game)
    format = CharField(choices=FORMAT_CHOICES)
    status = CharField(choices=STATUS_CHOICES)
    
    # Participants
    max_participants = IntegerField()
    total_registered = IntegerField()
    
    # Schedule
    registration_start = DateTimeField()
    registration_end = DateTimeField()
    start_datetime = DateTimeField()
    
    # Prize
    prize_pool = DecimalField()
    entry_fee = DecimalField()
```

#### Participant Model
```python
class Participant(models.Model):
    id = UUIDField(primary_key=True)
    tournament = ForeignKey(Tournament)
    user = ForeignKey(User, null=True)
    team = ForeignKey(Team, null=True)
    
    status = CharField(choices=STATUS_CHOICES)
    seed = IntegerField(null=True)
    checked_in = BooleanField()
    
    # Statistics
    matches_won = IntegerField()
    matches_lost = IntegerField()
    final_placement = IntegerField(null=True)
```

#### Match Model
```python
class Match(models.Model):
    id = UUIDField(primary_key=True)
    tournament = ForeignKey(Tournament)
    bracket = ForeignKey(Bracket)
    
    round_number = IntegerField()
    match_number = IntegerField()
    
    participant1 = ForeignKey(Participant)
    participant2 = ForeignKey(Participant)
    
    winner = ForeignKey(Participant, null=True)
    score_p1 = IntegerField()
    score_p2 = IntegerField()
    
    status = CharField(choices=STATUS_CHOICES)
    scheduled_time = DateTimeField(null=True)
```

#### Bracket Model
```python
class Bracket(models.Model):
    id = UUIDField(primary_key=True)
    tournament = ForeignKey(Tournament)
    bracket_type = CharField(choices=BRACKET_TYPE_CHOICES)
    
    total_rounds = IntegerField()
    current_round = IntegerField()
    completed = BooleanField()
```

### Model Methods

#### Tournament Methods
- `is_registration_open`: Check if registration is currently open
- `is_full`: Check if tournament has reached max participants
- `spots_remaining`: Calculate available spots
- `registration_progress`: Calculate percentage filled
- `can_user_register(user)`: Validate if user can register
- `start_tournament()`: Initialize tournament and create bracket
- `create_bracket()`: Generate bracket structure

#### Participant Methods
- `display_name`: Get user or team name
- `win_rate`: Calculate win percentage
- `check_in_participant()`: Mark as checked in

#### Match Methods
- `is_ready`: Check if both participants assigned
- `is_bye`: Check if bye match
- `report_score(score_p1, score_p2)`: Record match result
- `progress_bracket()`: Move winners to next matches

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Tournament List Filtering Consistency
*For any* combination of filters (game, status, search term), the displayed tournaments should match ALL applied filter criteria simultaneously.

**Validates: Requirements 1.3, 8.1, 8.2, 8.3, 8.4**

### Property 2: Registration Capacity Enforcement
*For any* tournament, the total number of registered participants should never exceed the max_participants value.

**Validates: Requirements 2.2, 10.1**

### Property 3: Registration Status Accuracy
*For any* user and tournament, if the user is registered, the system should display their registration status and prevent duplicate registration.

**Validates: Requirements 2.5, 10.1**

### Property 4: Bracket Match Progression
*For any* completed match with a winner, the winner should be assigned to the next_match_winner if it exists, and the bracket should reflect this progression.

**Validates: Requirements 4.3, 6.4**

### Property 5: Match Score Validation
*For any* match score submission, if score_p1 equals score_p2, the system should reject the submission with an error message.

**Validates: Requirements 6.3, 10.2**

### Property 6: Participant Statistics Consistency
*For any* participant, the sum of matches_won and matches_lost should equal the total number of completed matches they participated in.

**Validates: Requirements 5.1, 6.4**

### Property 7: Tournament Status Transitions
*For any* tournament, status transitions should follow the valid sequence: draft → registration → check_in → in_progress → completed, and no status should skip intermediate states.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

### Property 8: Search Result Relevance
*For any* search query, all returned tournaments should contain the search term in either their name or description fields.

**Validates: Requirements 8.1**

### Property 9: Responsive Layout Adaptation
*For any* viewport width, the tournament grid should display 1 column on mobile (<768px), 2 columns on tablet (768-1024px), and 3 columns on desktop (>1024px).

**Validates: Requirements 9.1, 9.2, 9.3**

### Property 10: Registration Validation Completeness
*For any* registration attempt, if the tournament is full, registration closed, or user already registered, the system should prevent registration and display a specific error message.

**Validates: Requirements 2.2, 10.1, 10.2**

## Error Handling

### User-Facing Errors

1. **Registration Errors**
   - Tournament full: "This tournament is full. Registration is closed."
   - Already registered: "You are already registered for this tournament."
   - Registration closed: "Registration for this tournament has closed."
   - Payment failed: "Payment processing failed. Please try again."

2. **Match Errors**
   - Invalid score: "Scores cannot be tied. Please enter valid scores."
   - Unauthorized: "You do not have permission to report scores for this match."
   - Match completed: "This match has already been completed."

3. **Bracket Errors**
   - Not generated: "The tournament bracket will be generated once registration closes."
   - Insufficient participants: "Not enough participants to generate bracket."

### System Errors

1. **Database Errors**
   - Log error with full stack trace
   - Display: "An error occurred. Please try again later."
   - Notify administrators

2. **Validation Errors**
   - Display field-specific errors
   - Highlight invalid fields
   - Preserve user input

3. **Permission Errors**
   - Redirect to login if not authenticated
   - Display 403 page if unauthorized
   - Log unauthorized access attempts

### Error Logging

```python
import logging

logger = logging.getLogger(__name__)

try:
    # Operation
    pass
except Exception as e:
    logger.error(f"Tournament registration failed: {str(e)}", 
                 exc_info=True,
                 extra={'user_id': user.id, 'tournament_id': tournament.id})
    messages.error(request, "An error occurred during registration.")
```

## Testing Strategy

### Unit Testing

**Framework**: Django's built-in TestCase

**Coverage Areas**:
1. Model methods
   - `Tournament.can_user_register()`
   - `Match.report_score()`
   - `Participant.check_in_participant()`

2. View logic
   - Registration validation
   - Filter application
   - Permission checks

3. Template rendering
   - Context data correctness
   - Conditional display logic

**Example Unit Test**:
```python
class TournamentModelTest(TestCase):
    def test_registration_full_tournament(self):
        tournament = Tournament.objects.create(
            name="Test Tournament",
            max_participants=2,
            total_registered=2
        )
        user = User.objects.create(username="testuser")
        
        can_register, message = tournament.can_user_register(user)
        
        self.assertFalse(can_register)
        self.assertEqual(message, "Tournament is full")
```

### Property-Based Testing

**Framework**: Hypothesis for Python

**Configuration**: Minimum 100 iterations per property test

**Test Structure**:
```python
from hypothesis import given, strategies as st
from hypothesis.extra.django import TestCase

class TournamentPropertyTests(TestCase):
    @given(
        max_participants=st.integers(min_value=2, max_value=100),
        registered_count=st.integers(min_value=0, max_value=100)
    )
    def test_property_registration_capacity(self, max_participants, registered_count):
        # Property test implementation
        pass
```

### Integration Testing

**Areas**:
1. Registration flow (user → participant → notification)
2. Match progression (score → winner → next match)
3. Bracket generation (participants → matches → rounds)
4. Payment integration (entry fee → payment → confirmation)

### Frontend Testing

**Tools**: 
- Selenium for browser automation
- Django's LiveServerTestCase

**Test Cases**:
1. Search and filter interactions
2. Registration form submission
3. Responsive layout verification
4. HTMX dynamic updates

### Test Data Generation

**Fixtures**:
- Sample tournaments (various statuses)
- Test users and teams
- Match data with scores
- Bracket structures

**Factory Pattern**:
```python
class TournamentFactory:
    @staticmethod
    def create_tournament(**kwargs):
        defaults = {
            'name': 'Test Tournament',
            'max_participants': 16,
            'status': 'registration',
            # ... other defaults
        }
        defaults.update(kwargs)
        return Tournament.objects.create(**defaults)
```

## Security Considerations

### Authentication & Authorization

1. **Registration**: Requires authenticated user
2. **Score Reporting**: Only participants or organizers
3. **Tournament Management**: Only organizers or admins
4. **Bracket Generation**: Only organizers or admins

### Input Validation

1. **Score Values**: Must be non-negative integers
2. **Search Terms**: Sanitized to prevent SQL injection
3. **File Uploads**: Validated type and size (disputes)
4. **Date Ranges**: Validated logical consistency

### CSRF Protection

All forms include `{% csrf_token %}` for POST requests.

### Rate Limiting

Consider implementing rate limiting for:
- Registration attempts
- Score submissions
- Search queries

## Performance Optimization

### Database Queries

1. **Select Related**: Pre-fetch related objects
   ```python
   Tournament.objects.select_related('game', 'organizer')
   ```

2. **Prefetch Related**: Optimize many-to-many queries
   ```python
   tournament.participants.prefetch_related('user', 'team')
   ```

3. **Indexing**: Database indexes on frequently queried fields
   - `status`, `start_datetime`
   - `game`, `status`
   - `is_public`, `is_featured`

### Caching Strategy

1. **Tournament List**: Cache for 5 minutes
2. **Bracket Data**: Cache until match update
3. **Static Assets**: Browser caching with versioning

### Pagination

- List views: 12 items per page
- Match lists: 20 items per page
- Participant lists: 50 items per page

## Deployment Considerations

### Environment Variables

```
TOURNAMENT_MAX_PARTICIPANTS=256
TOURNAMENT_REGISTRATION_BUFFER_HOURS=24
BRACKET_GENERATION_TIMEOUT=300
```

### Database Migrations

Ensure all migrations are applied:
```bash
python manage.py migrate tournaments
```

### Static Files

Collect static files for production:
```bash
python manage.py collectstatic
```

### Monitoring

- Track tournament creation rate
- Monitor registration failures
- Alert on bracket generation errors
- Log match dispute frequency

## Future Enhancements

1. **Real-time Updates**: WebSocket integration for live bracket updates
2. **Streaming Integration**: Embed Twitch streams in tournament pages
3. **Advanced Statistics**: Player performance analytics
4. **Mobile App**: Native mobile application
5. **Tournament Templates**: Pre-configured tournament setups
6. **Automated Scheduling**: AI-powered match scheduling
7. **Spectator Mode**: Live match viewing for non-participants
8. **Replay System**: Match replay storage and playback

