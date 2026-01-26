# Design Document: User Profile & Dashboard System

## Overview

The User Profile & Dashboard System is a Django-based feature that provides users with a centralized hub for managing their gaming identity, tracking performance, and accessing personalized insights. The system integrates with existing tournament, team, payment, and notification modules to aggregate data and present a comprehensive view of user activity and statistics.

### Key Design Goals

1. **Performance**: Efficient data aggregation with caching to handle complex statistics
2. **Modularity**: Clean separation between profile management, statistics calculation, and dashboard presentation
3. **Extensibility**: Easy to add new statistics, achievements, and dashboard widgets
4. **Privacy**: Granular control over what information is visible to other users
5. **Accessibility**: Full WCAG 2.1 AA compliance for all interfaces
6. **Responsiveness**: Mobile-first design that works seamlessly across all devices

### Technology Stack

- **Backend**: Django 4.x with Django ORM
- **Caching**: Redis for statistics and query result caching
- **Frontend**: Django templates with Alpine.js for interactivity
- **Charts**: Chart.js for performance trend visualization
- **Image Processing**: Pillow for avatar resizing and optimization
- **Testing**: pytest with Hypothesis for property-based testing

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Presentation Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Dashboard   │  │   Profile    │  │   Settings   │      │
│  │   Views      │  │    Views     │  │    Views     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                        Service Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Statistics  │  │ Achievement  │  │Recommendation│      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Activity   │  │Profile Export│  │   Privacy    │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                         Data Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     User     │  │UserGameProfile│ │  Activity    │      │
│  │    Model     │  │    Model     │  │    Model     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Achievement  │  │UserAchievement│ │Recommendation│      │
│  │    Model     │  │    Model     │  │    Model     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    External Dependencies                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Tournaments  │  │    Teams     │  │   Payments   │      │
│  │    Module    │  │    Module    │  │    Module    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │Notifications │  │    Redis     │                        │
│  │    Module    │  │    Cache     │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### Presentation Layer
- **Dashboard Views**: Render personalized dashboard with activity feed, statistics, and quick actions
- **Profile Views**: Display and edit user profiles, game profiles, and public profile pages
- **Settings Views**: Manage account settings, privacy, notifications, and connected accounts

#### Service Layer
- **Statistics Service**: Calculate and cache user performance metrics across games and tournaments
- **Achievement Service**: Track progress, award achievements, and manage achievement showcase
- **Recommendation Service**: Generate personalized tournament and team recommendations
- **Activity Service**: Record and retrieve user activity feed
- **Profile Export Service**: Generate JSON exports of user data
- **Privacy Service**: Enforce privacy settings across profile and activity visibility
- **Payment Summary Service**: Aggregate payment data for dashboard display (delegates to payments module)

#### Data Layer
- **User Model**: Core user data (already exists in core.models)
- **UserGameProfile Model**: Game-specific profiles and statistics (already exists)
- **Activity Model**: User activity log
- **Achievement Model**: Achievement definitions
- **UserAchievement Model**: User's earned achievements with progress
- **Recommendation Model**: Cached recommendations for users

## Components and Interfaces

### 1. Dashboard Component

**Purpose**: Main landing page after login showing personalized content

**Views**:
- `dashboard_home(request)` - Main dashboard view (already exists, needs enhancement)
- `dashboard_activity(request)` - Activity feed with filtering
- `dashboard_stats(request)` - Detailed statistics view

**Templates**:
- `dashboard/home.html` - Main dashboard layout
- `dashboard/activity_feed.html` - Activity feed component
- `dashboard/stats_cards.html` - Statistics cards component
- `dashboard/quick_actions.html` - Quick action buttons component
- `dashboard/recommendations.html` - Recommendations widget
- `dashboard/mobile_nav.html` - Mobile bottom navigation bar

**Quick Actions**:
The dashboard provides prominent buttons for frequently used actions:
1. Register for Tournament - Links to tournament list with registration filter
2. Join Team - Links to team recruitment page
3. View Notifications - Links to notifications page
4. Manage Payment Methods - Links to payment methods management

**Statistics Cards**:
The dashboard displays key metrics in card format:
1. Total Tournaments - Count of tournaments participated in
2. Win Rate - Overall win percentage across all games
3. Current Teams - Number of active team memberships
4. Unread Notifications - Count of unread notifications

**Mobile Navigation**:
On mobile devices (< 768px), a bottom navigation bar is displayed with:
1. Dashboard icon - Links to dashboard home
2. Profile icon - Links to user's profile
3. Notifications icon - Links to notifications (with badge for unread count)
4. Menu icon - Opens slide-out menu with additional options

**Responsive Layout**:
- Desktop (> 1024px): Multi-column layout with sidebar
- Tablet (768-1024px): Two-column layout
- Mobile (< 768px): Single-column stacked layout with bottom navigation

**URL Patterns**:
```python
/dashboard/                    # Main dashboard
/dashboard/activity/           # Activity feed
/dashboard/stats/              # Detailed stats
```

### 2. Profile Component

**Purpose**: User profile management and public profile viewing

**Views**:
- `profile_view(request, username)` - View user profile (public or own)
- `profile_edit(request)` - Edit profile information
- `profile_avatar_upload(request)` - Handle avatar uploads
- `profile_completeness(request)` - Get profile completeness data
- `profile_export(request)` - Export user data

**Templates**:
- `profile/view.html` - Profile display page
- `profile/edit.html` - Profile editing form
- `profile/game_profiles.html` - Game profiles management
- `profile/completeness.html` - Profile completeness widget

**URL Patterns**:
```python
/profile/<username>/           # View profile
/profile/edit/                 # Edit own profile
/profile/avatar/upload/        # Avatar upload
/profile/export/               # Export data
```

### 3. Game Profile Component

**Purpose**: Manage game-specific profiles and statistics

**Views**:
- `game_profile_list(request)` - List user's game profiles
- `game_profile_create(request)` - Add new game profile
- `game_profile_edit(request, profile_id)` - Edit game profile
- `game_profile_delete(request, profile_id)` - Delete game profile
- `game_profile_set_main(request, profile_id)` - Set main game

**Templates**:
- `profile/game_profiles_list.html` - List of game profiles
- `profile/game_profile_form.html` - Game profile form
- `profile/game_profile_card.html` - Individual game profile card

**URL Patterns**:
```python
/profile/games/                # List game profiles
/profile/games/add/            # Add game profile
/profile/games/<id>/edit/      # Edit game profile
/profile/games/<id>/delete/    # Delete game profile
/profile/games/<id>/set-main/  # Set as main game
```

### 4. Statistics Component

**Purpose**: Calculate and display user performance statistics

**Service Class**: `StatisticsService`

**Methods**:
```python
class StatisticsService:
    def get_user_statistics(user_id: UUID) -> dict
    def get_game_statistics(user_id: UUID, game_id: UUID) -> dict
    def get_tournament_history(user_id: UUID, filters: dict) -> QuerySet
    def get_team_statistics(user_id: UUID) -> dict
    def calculate_win_rate(user_id: UUID, game_id: UUID = None) -> float
    def get_performance_trend(user_id: UUID, days: int = 30) -> list
    def invalidate_cache(user_id: UUID) -> None
```

**Cache Keys**:
```python
f"user_stats:{user_id}"                    # 1 hour TTL
f"user_game_stats:{user_id}:{game_id}"     # 1 hour TTL
f"user_tournament_history:{user_id}"       # 1 hour TTL
f"user_performance_trend:{user_id}:{days}" # 1 hour TTL
```

### 5. Achievement Component

**Purpose**: Track and award user achievements

**Service Class**: `AchievementService`

**Methods**:
```python
class AchievementService:
    def check_achievements(user_id: UUID, event_type: str) -> list
    def award_achievement(user_id: UUID, achievement_id: UUID) -> UserAchievement
    def get_user_achievements(user_id: UUID) -> QuerySet
    def get_achievement_progress(user_id: UUID, achievement_id: UUID) -> dict
    def update_showcase(user_id: UUID, achievement_ids: list) -> None
    def get_rare_achievements(user_id: UUID) -> QuerySet
```

**Achievement Types**:
- Tournament achievements (first win, 10 tournaments, top 3 finish)
- Team achievements (join team, team tournament win)
- Social achievements (add 10 friends, send 100 messages)
- Platform achievements (profile completion, 1 year member)

### 6. Activity Component

**Purpose**: Track and display user activity feed

**Service Class**: `ActivityService`

**Methods**:
```python
class ActivityService:
    def record_activity(user_id: UUID, activity_type: str, data: dict) -> Activity
    def get_activity_feed(user_id: UUID, filters: dict, page: int) -> QuerySet
    def get_activity_types() -> list
    def delete_old_activities(days: int = 90) -> int
```

**Activity Types**:
- `tournament_registered` - User registered for tournament
- `tournament_completed` - User completed tournament
- `team_joined` - User joined team
- `team_left` - User left team
- `achievement_earned` - User earned achievement
- `payment_completed` - User completed payment
- `profile_updated` - User updated profile

### 7. Recommendation Component

**Purpose**: Generate personalized recommendations

**Service Class**: `RecommendationService`

**Methods**:
```python
class RecommendationService:
    def get_tournament_recommendations(user_id: UUID) -> QuerySet
    def get_team_recommendations(user_id: UUID) -> QuerySet
    def dismiss_recommendation(user_id: UUID, rec_id: UUID) -> None
    def refresh_recommendations(user_id: UUID) -> None
    def calculate_recommendation_score(user: User, item: Model) -> float
```

**Recommendation Algorithm**:
1. Match user's game profiles with tournament/team games
2. Match skill level (±1 level)
3. Consider past participation patterns
4. Exclude dismissed recommendations (30-day cooldown)
5. Score and rank by relevance

### 8. Privacy Component

**Purpose**: Enforce privacy settings

**Service Class**: `PrivacyService`

**Methods**:
```python
class PrivacyService:
    def can_view_profile(viewer: User, profile_owner: User) -> bool
    def can_view_statistics(viewer: User, profile_owner: User) -> bool
    def can_view_activity(viewer: User, profile_owner: User) -> bool
    def filter_profile_data(viewer: User, profile_data: dict) -> dict
    def get_privacy_settings(user_id: UUID) -> dict
    def update_privacy_settings(user_id: UUID, settings: dict) -> None
    def are_friends(user1: User, user2: User) -> bool  # Placeholder for Phase 2
```

**Privacy Levels**:
- Public: Visible to everyone
- Friends: Visible to friends only (Phase 2 - currently treated as private)
- Private: Visible only to user

**Design Rationale**: The privacy system is designed with friend-level privacy in mind, but since the friend system is a Phase 2 feature, "friends-only" privacy currently behaves the same as "private". The `are_friends()` method is implemented as a placeholder that returns False, allowing the privacy logic to be complete while deferring the friend system implementation. When the friend system is implemented in Phase 2, only the `are_friends()` method needs to be updated.

### 9. Account Settings Component

**Purpose**: Manage account settings and preferences

**Views**:
- `settings_profile(request)` - Profile settings
- `settings_privacy(request)` - Privacy settings
- `settings_notifications(request)` - Notification preferences
- `settings_security(request)` - Security settings (password change)
- `settings_connected_accounts(request)` - Manage connected accounts
- `account_delete(request)` - Account deletion

**URL Patterns**:
```python
/settings/profile/             # Profile settings
/settings/privacy/             # Privacy settings
/settings/notifications/       # Notification preferences
/settings/security/            # Security settings
/settings/accounts/            # Connected accounts
/settings/delete/              # Delete account
```

### 10. Payment Integration Component

**Purpose**: Display payment summary and quick access to payment features

**Service Class**: `PaymentSummaryService`

**Methods**:
```python
class PaymentSummaryService:
    def get_payment_summary(user_id: UUID) -> dict
    def get_recent_payments(user_id: UUID, limit: int = 5) -> QuerySet
    def get_saved_payment_methods_count(user_id: UUID) -> int
    def has_default_payment_method(user_id: UUID) -> bool
```

**Views**:
- `dashboard_payment_summary(request)` - Payment summary widget for dashboard
- Integration with existing payment views from payments module

**Dashboard Widget Data**:
```python
{
    'total_spent': Decimal,
    'recent_payments_count': int,
    'saved_payment_methods_count': int,
    'recent_payments': QuerySet[Payment],  # Last 5
    'has_default_method': bool
}
```

**URL Patterns**:
```python
/dashboard/payments/summary/   # Payment summary API endpoint
# Links to existing payment module URLs:
# /payments/history/
# /payments/methods/
```

**Design Rationale**: Rather than duplicating payment functionality, this component provides a dashboard widget that aggregates payment data and links to the existing payment module for detailed management. This maintains separation of concerns and avoids code duplication. The PaymentSummaryService acts as a facade that queries the payments module's models and returns aggregated data suitable for dashboard display.

### 11. Social Interaction Component

**Purpose**: Enable basic social interactions between users

**Views**:
- `user_report(request, username)` - Report user for inappropriate behavior
- `user_message(request, username)` - Send direct message to user (future)
- `friend_request_send(request, username)` - Send friend request (future)

**Templates**:
- `profile/report_user_modal.html` - Report user form modal
- `profile/social_actions.html` - Social action buttons component

**URL Patterns**:
```python
/profile/<username>/report/    # Report user
/profile/<username>/message/   # Send message (future)
/profile/<username>/friend/    # Friend request (future)
```

**Report Categories**:
- Inappropriate username or avatar
- Harassment or abusive behavior
- Spam or advertising
- Cheating or unfair play
- Other (with description)

**Design Rationale**: The report functionality is implemented immediately as it's critical for platform safety. Friend system and messaging are marked as future enhancements in Phase 2, but the UI includes placeholder buttons that can be enabled when those features are implemented. This allows the profile page to be complete while deferring complex social features.

## Data Models

### User Model Extensions

**Note**: The User model already exists in `core.models`. The following fields need to be added via a migration:

```python
# Add to User model in core/models.py
class User(AbstractBaseUser, PermissionsMixin):
    # ... existing fields ...
    
    # New fields for profile dashboard
    banner = models.ImageField(upload_to='banners/', null=True, blank=True)
    online_status_visible = models.BooleanField(default=True)
    activity_visible = models.BooleanField(default=True)
    statistics_visible = models.BooleanField(default=True)
```

**Design Rationale**: Rather than creating a separate UserProfile model, we extend the existing User model with additional fields needed for the profile dashboard. This keeps user data centralized and avoids unnecessary joins. The privacy fields (online_status_visible, activity_visible, statistics_visible) provide granular control over what information is visible to others.

### Activity Model

```python
class Activity(models.Model):
    """User activity log"""
    
    ACTIVITY_TYPES = [
        ('tournament_registered', 'Tournament Registered'),
        ('tournament_completed', 'Tournament Completed'),
        ('team_joined', 'Team Joined'),
        ('team_left', 'Team Left'),
        ('achievement_earned', 'Achievement Earned'),
        ('payment_completed', 'Payment Completed'),
        ('profile_updated', 'Profile Updated'),
        ('friend_added', 'Friend Added'),
        ('game_profile_added', 'Game Profile Added'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    
    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Activity data (JSON for flexibility)
    data = models.JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
        ]
```

### Achievement Model

```python
class Achievement(models.Model):
    """Achievement definitions"""
    
    ACHIEVEMENT_TYPES = [
        ('tournament', 'Tournament'),
        ('team', 'Team'),
        ('social', 'Social'),
        ('platform', 'Platform'),
    ]
    
    RARITY_LEVELS = [
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    rarity = models.CharField(max_length=20, choices=RARITY_LEVELS, default='common')
    
    # Icon and display
    icon = models.ImageField(upload_to='achievements/', null=True, blank=True)
    icon_url = models.URLField(blank=True)  # Alternative to uploaded icon
    
    # Requirements
    is_progressive = models.BooleanField(default=False)
    target_value = models.IntegerField(default=1)  # For progressive achievements
    points_reward = models.IntegerField(default=10)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False)  # Hidden until earned
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'achievements'
        ordering = ['achievement_type', 'name']
```

### UserAchievement Model

```python
class UserAchievement(models.Model):
    """User's earned achievements"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='user_achievements')
    
    # Progress tracking
    current_value = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    
    # Showcase
    in_showcase = models.BooleanField(default=False)
    showcase_order = models.IntegerField(default=0)
    
    # Metadata
    earned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_achievements'
        unique_together = ['user', 'achievement']
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user', 'is_completed']),
            models.Index(fields=['user', 'in_showcase', 'showcase_order']),
        ]
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage for progressive achievements"""
        if not self.achievement.is_progressive:
            return 100 if self.is_completed else 0
        return min(100, (self.current_value / self.achievement.target_value) * 100)
```

### Recommendation Model

```python
class Recommendation(models.Model):
    """Cached recommendations for users"""
    
    RECOMMENDATION_TYPES = [
        ('tournament', 'Tournament'),
        ('team', 'Team'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    
    # Generic relation to recommended item
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Recommendation metadata
    score = models.FloatField(default=0.0)  # Relevance score
    reason = models.CharField(max_length=200)  # Why recommended
    
    # Status
    is_dismissed = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Recommendations expire after 24 hours
    
    class Meta:
        db_table = 'recommendations'
        ordering = ['-score', '-created_at']
        indexes = [
            models.Index(fields=['user', 'recommendation_type', '-score']),
            models.Index(fields=['user', 'is_dismissed']),
        ]
```

### UserReport Model

```python
class UserReport(models.Model):
    """User reports for moderation"""
    
    REPORT_CATEGORIES = [
        ('inappropriate_content', 'Inappropriate Username or Avatar'),
        ('harassment', 'Harassment or Abusive Behavior'),
        ('spam', 'Spam or Advertising'),
        ('cheating', 'Cheating or Unfair Play'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    
    # Report details
    category = models.CharField(max_length=50, choices=REPORT_CATEGORIES)
    description = models.TextField(max_length=1000)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reported_user', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]
```

**Design Rationale**: User reports are essential for platform safety and moderation. Reports are tracked with status workflow (pending → investigating → resolved/dismissed) and include audit trail with reviewer information. This allows moderators to efficiently handle user reports and track patterns of problematic behavior.

### ProfileCompleteness Model

```python
class ProfileCompleteness(models.Model):
    """Track profile completeness with weighted fields"""
    
    FIELD_WEIGHTS = {
        'first_name': 5,
        'last_name': 5,
        'display_name': 5,
        'avatar': 10,
        'bio': 10,
        'date_of_birth': 5,
        'country': 5,
        'city': 3,
        'discord_username': 7,
        'steam_id': 7,
        'twitch_username': 7,
        'game_profile': 15,  # At least one game profile
        'email_verified': 10,
        'phone_number': 6,
    }
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='completeness')
    
    # Completeness tracking
    total_points = models.IntegerField(default=0)
    max_points = models.IntegerField(default=100)
    percentage = models.IntegerField(default=0)
    
    # Field completion status (JSON for flexibility)
    completed_fields = models.JSONField(default=dict)
    incomplete_fields = models.JSONField(default=list)
    
    # Metadata
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'profile_completeness'
    
    @classmethod
    def calculate_for_user(cls, user):
        """Calculate profile completeness for a user"""
        total_points = 0
        completed = {}
        incomplete = []
        
        # Check each field
        if user.first_name:
            total_points += cls.FIELD_WEIGHTS['first_name']
            completed['first_name'] = True
        else:
            incomplete.append('first_name')
        
        if user.last_name:
            total_points += cls.FIELD_WEIGHTS['last_name']
            completed['last_name'] = True
        else:
            incomplete.append('last_name')
        
        if user.display_name:
            total_points += cls.FIELD_WEIGHTS['display_name']
            completed['display_name'] = True
        else:
            incomplete.append('display_name')
        
        if user.avatar:
            total_points += cls.FIELD_WEIGHTS['avatar']
            completed['avatar'] = True
        else:
            incomplete.append('avatar')
        
        if user.bio:
            total_points += cls.FIELD_WEIGHTS['bio']
            completed['bio'] = True
        else:
            incomplete.append('bio')
        
        if user.date_of_birth:
            total_points += cls.FIELD_WEIGHTS['date_of_birth']
            completed['date_of_birth'] = True
        else:
            incomplete.append('date_of_birth')
        
        if user.country:
            total_points += cls.FIELD_WEIGHTS['country']
            completed['country'] = True
        else:
            incomplete.append('country')
        
        if user.city:
            total_points += cls.FIELD_WEIGHTS['city']
            completed['city'] = True
        else:
            incomplete.append('city')
        
        if user.discord_username:
            total_points += cls.FIELD_WEIGHTS['discord_username']
            completed['discord_username'] = True
        else:
            incomplete.append('discord_username')
        
        if user.steam_id:
            total_points += cls.FIELD_WEIGHTS['steam_id']
            completed['steam_id'] = True
        else:
            incomplete.append('steam_id')
        
        if user.twitch_username:
            total_points += cls.FIELD_WEIGHTS['twitch_username']
            completed['twitch_username'] = True
        else:
            incomplete.append('twitch_username')
        
        if user.game_profiles.exists():
            total_points += cls.FIELD_WEIGHTS['game_profile']
            completed['game_profile'] = True
        else:
            incomplete.append('game_profile')
        
        if user.is_verified:
            total_points += cls.FIELD_WEIGHTS['email_verified']
            completed['email_verified'] = True
        else:
            incomplete.append('email_verified')
        
        if user.phone_number:
            total_points += cls.FIELD_WEIGHTS['phone_number']
            completed['phone_number'] = True
        else:
            incomplete.append('phone_number')
        
        percentage = int((total_points / cls.FIELD_WEIGHTS.values().__iter__().__class__(cls.FIELD_WEIGHTS.values()).__sizeof__()) * 100)
        
        # Update or create completeness record
        completeness, created = cls.objects.update_or_create(
            user=user,
            defaults={
                'total_points': total_points,
                'max_points': sum(cls.FIELD_WEIGHTS.values()),
                'percentage': percentage,
                'completed_fields': completed,
                'incomplete_fields': incomplete,
            }
        )
        
        # Update user's profile_completed flag
        if percentage == 100 and not user.profile_completed:
            user.profile_completed = True
            user.add_points(50)  # Award bonus points
            user.save(update_fields=['profile_completed'])
        
        return completeness
```

**Design Rationale**: The ProfileCompleteness model uses a weighted point system where more important fields (avatar, bio, game profiles) are worth more points than optional fields (city, phone). The total is normalized to a 0-100 percentage. The calculation method is implemented as a class method for easy reuse and testing.

## 

## Error Handling

### Validation Errors

**Profile Updates**:
- Invalid email format → Return form error with specific field message
- Avatar file too large (>2MB) → Return error "Avatar must be under 2MB"
- Banner file too large (>5MB) → Return error "Banner must be under 5MB"
- Invalid image format → Return error "Image must be JPG, PNG, or GIF"
- Username already taken → Return error "Username is already in use"

**Game Profile Management**:
- Duplicate game profile → Return error "You already have a profile for this game"
- Delete profile with tournament history → Return error "Cannot delete game profile with tournament history"
- Invalid skill rating → Return error "Skill rating must be between 0 and 5000"

**Privacy Settings**:
- Invalid privacy level → Return error "Invalid privacy setting"
- Conflicting settings → Auto-resolve to most restrictive

### System Errors

**Database Errors**:
- Connection timeout → Retry up to 3 times with exponential backoff
- Query timeout → Return cached data if available, otherwise show error message
- Integrity constraint violation → Log error and return user-friendly message

**Cache Errors**:
- Redis connection failure → Fall back to database queries
- Cache miss → Calculate fresh data and cache result
- Serialization error → Log error and skip caching

**External Service Errors**:
- Image processing failure → Use default avatar/banner
- Statistics calculation timeout → Return partial statistics with warning
- Export generation failure → Queue for retry and notify user via email
- Cache service unavailable → Fall back to direct database queries with performance warning

### User Feedback

All errors should:
1. Display user-friendly messages (no technical jargon)
2. Provide actionable next steps when possible
3. Log detailed error information for debugging
4. Maintain form state to prevent data loss
5. Use appropriate HTTP status codes (400 for validation, 500 for server errors)

## Testing Strategy

### Unit Testing

**Framework**: pytest with pytest-django

**Coverage Areas**:
1. **Model Methods**:
   - User profile completeness calculation
   - UserGameProfile win rate calculation
   - Achievement progress calculation
   - Activity feed filtering

2. **Service Layer**:
   - StatisticsService calculations
   - AchievementService award logic
   - RecommendationService scoring
   - PrivacyService permission checks

3. **View Logic**:
   - Dashboard data aggregation
   - Profile edit validation
   - Settings update handling
   - Export generation

4. **Form Validation**:
   - Profile form validation
   - Game profile form validation
   - Settings form validation

**Example Unit Tests**:
```python
def test_profile_completeness_calculation():
    """Test that profile completeness is calculated correctly"""
    user = create_test_user(first_name="John", last_name="Doe")
    assert user.check_profile_completeness() == False
    
def test_win_rate_calculation():
    """Test win rate calculation for game profiles"""
    profile = create_game_profile(matches_played=10, matches_won=7)
    assert profile.win_rate == 70.0

def test_achievement_award():
    """Test awarding achievement to user"""
    user = create_test_user()
    achievement = create_achievement(name="First Win")
    result = AchievementService.award_achievement(user.id, achievement.id)
    assert result.is_completed == True
```

### Property-Based Testing

**Framework**: Hypothesis

**Library Configuration**:
- Minimum 100 iterations per property test
- Use Hypothesis strategies for generating test data
- Each property test must reference its design document property with format: `**Feature: user-profile-dashboard, Property {number}: {property_text}**`

**Property Test Areas**:

1. **Statistics Calculations**:
   - Win rate calculations always between 0 and 100
   - Total matches = matches won + matches lost
   - Aggregated statistics match sum of individual records

2. **Profile Completeness**:
   - Completeness percentage always between 0 and 100
   - Adding fields increases or maintains completeness
   - Removing fields decreases or maintains completeness

3. **Achievement Progress**:
   - Progress percentage always between 0 and 100
   - Completed achievements have progress = 100
   - Progressive achievements increase monotonically

4. **Privacy Enforcement**:
   - Private profiles never expose statistics to non-friends
   - Public profiles always expose allowed data
   - Privacy settings are consistently enforced

5. **Caching Consistency**:
   - Cached data matches fresh calculation
   - Cache invalidation removes stale data
   - Cache TTL is respected

**Example Property Tests**:
```python
@given(matches_played=st.integers(min_value=0, max_value=1000),
       matches_won=st.integers(min_value=0, max_value=1000))
def test_win_rate_bounds(matches_played, matches_won):
    """Property: Win rate is always between 0 and 100"""
    matches_won = min(matches_won, matches_played)  # Ensure valid data
    profile = create_game_profile(matches_played=matches_played, matches_won=matches_won)
    assert 0 <= profile.win_rate <= 100

@given(user_data=user_strategy())
def test_profile_completeness_bounds(user_data):
    """Property: Profile completeness is always between 0 and 100"""
    user = create_user(**user_data)
    completeness = calculate_profile_completeness(user)
    assert 0 <= completeness <= 100
```

### Integration Testing

**Test Scenarios**:
1. **Dashboard Load**:
   - User logs in → Dashboard displays with all widgets
   - Statistics are calculated and cached
   - Activity feed loads with pagination

2. **Profile Update Flow**:
   - User edits profile → Changes are saved
   - Profile completeness is recalculated
   - Cache is invalidated
   - Activity is recorded

3. **Achievement Award Flow**:
   - User completes action → Achievement check is triggered
   - Achievement is awarded if criteria met
   - Notification is sent
   - Activity is recorded

4. **Privacy Enforcement**:
   - User sets profile to private → Other users cannot see statistics
   - User sets profile to public → Statistics are visible
   - Friends can see friend-only content

### End-to-End Testing

**Test Scenarios**:
1. Complete profile setup journey
2. View another user's profile
3. Manage game profiles
4. Export profile data
5. Delete account

### Performance Testing

**Benchmarks**:
- Dashboard load time < 500ms (with cache)
- Profile page load time < 300ms
- Statistics calculation < 200ms
- Export generation < 5 seconds

**Load Testing**:
- 100 concurrent users viewing dashboards
- 50 concurrent profile updates
- Cache hit rate > 80%

## 
Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I've identified several areas where properties can be consolidated to eliminate redundancy:

**Redundancy Analysis**:
1. Properties 1.2, 3.1, 3.2, 3.3 all test that specific data fields are displayed - these can be consolidated into a single property about complete data display
2. Properties 2.5, 10.2, 10.5 all test privacy enforcement - these can be consolidated into a comprehensive privacy property
3. Properties 5.5 and 8.5 both test pagination logic - these can be consolidated into a single pagination property
4. Properties 16.1, 16.2, 16.3 all test caching behavior - these can be consolidated into a comprehensive caching property
5. Properties 17.1, 17.2, 17.5 all test export data completeness - these can be consolidated into a single export property

**Consolidated Properties**:
After reflection, I'll write properties that provide unique validation value without logical redundancy.

### Core Properties

**Property 1: Statistics calculation correctness**
*For any* user with match history, the sum of matches won and matches lost must equal total matches played, and win rate must be between 0 and 100 percent
**Validates: Requirements 3.1, 3.5**

**Property 2: Profile completeness bounds**
*For any* user profile, the completeness percentage must be between 0 and 100 percent, and adding completed fields must increase or maintain the percentage
**Validates: Requirements 11.1, 11.2**

**Property 3: Main game uniqueness**
*For any* user, at most one game profile can be marked as the main game at any time
**Validates: Requirements 4.2**

**Property 4: Game profile deletion protection**
*For any* game profile with associated tournament participations, deletion attempts must be rejected
**Validates: Requirements 4.4**

**Property 5: Activity feed chronological ordering**
*For any* activity feed, activities must be displayed in reverse chronological order (newest first)
**Validates: Requirements 1.3, 8.1**

**Property 6: Upcoming events time window**
*For any* dashboard display, upcoming events must only include items with dates within the next 7 days from the current time
**Validates: Requirements 1.4**

**Property 7: Game profile sorting**
*For any* list of game profiles, the main game must appear first, followed by other games sorted by skill rating in descending order
**Validates: Requirements 4.5**

**Property 8: Privacy enforcement**
*For any* private profile viewed by a non-friend, only basic information (username, avatar, bio) must be visible, and statistics and activity must be hidden
**Validates: Requirements 2.5, 10.2, 10.5**

**Property 9: Achievement progress bounds**
*For any* progressive achievement, the progress percentage must be between 0 and 100 percent, and completed achievements must have progress equal to 100 percent
**Validates: Requirements 7.2**

**Property 10: Achievement showcase limit**
*For any* user, the number of achievements in showcase must not exceed 6
**Validates: Requirements 7.5**

**Property 11: Pagination consistency**
*For any* paginated list (tournament history with 20 per page, activity feed with 25 per page), the total number of items across all pages must equal the total count, and no items must be duplicated or missing
**Validates: Requirements 5.5, 8.5**

**Property 12: Tournament history filtering**
*For any* filtered tournament history, all returned tournaments must match the filter criteria (game, date range, placement)
**Validates: Requirements 5.2**

**Property 13: Activity feed filtering**
*For any* filtered activity feed, all returned activities must match the filter criteria (activity type, date range)
**Validates: Requirements 8.3**

**Property 14: Mutual teams identification**
*For any* two users, the mutual teams displayed must be exactly the set intersection of teams where both users are members
**Validates: Requirements 10.4**

**Property 15: Recommendation dismissal persistence**
*For any* dismissed recommendation, it must not reappear in the user's recommendations for 30 days
**Validates: Requirements 13.4**

**Property 16: Avatar image processing**
*For any* uploaded avatar image, the processed image must be exactly 400x400 pixels, and images larger than 2MB must be rejected
**Validates: Requirements 2.3**

**Property 16b: Banner image processing**
*For any* uploaded banner image, the processed image must be exactly 1920x400 pixels, and images larger than 5MB must be rejected
**Validates: Requirements 16.5**

**Property 17: Profile field validation**
*For any* profile update with invalid data, the system must reject the update and return specific field error messages
**Validates: Requirements 2.2**

**Property 18: Password change security**
*For any* password change attempt, the current password must be verified, new password strength must be validated, and the password hash must be updated only when both checks pass
**Validates: Requirements 9.4**

**Property 19: Cache consistency**
*For any* cached statistics, the cached value must match the freshly calculated value, and cache must be invalidated when underlying data changes
**Validates: Requirements 16.1, 16.2, 16.3**

**Property 20: Cache TTL enforcement**
*For any* cached data, requests within the TTL period must return cached data, and requests after TTL expiration must trigger fresh calculation
**Validates: Requirements 16.1, 16.5**

**Property 21: Export data completeness**
*For any* user data export, the JSON must include all required sections (profile, game profiles, tournament history, team memberships, payment history) and must exclude sensitive data (password hash, payment method details)
**Validates: Requirements 17.1, 17.2, 17.5**

**Property 22: Export audit logging**
*For any* data export request, a log entry must be created with timestamp and IP address
**Validates: Requirements 17.4**

**Property 23: Account deletion anonymization**
*For any* deleted account, all personal information must be replaced with placeholder values, tournament participation records must be retained without personal identifiers, and the user must be immediately logged out
**Validates: Requirements 18.3, 18.4, 18.5**

**Property 24: Rare achievement highlighting**
*For any* achievement earned by fewer than 10 percent of users, it must be highlighted when displayed
**Validates: Requirements 7.4**

**Property 25: Touch target accessibility**
*For any* interactive element on mobile, the touch target size must be at least 44x44 pixels
**Validates: Requirements 14.4**

**Property 26: Color contrast accessibility**
*For any* text displayed, the contrast ratio must be at least 4.5:1 for normal text and 3:1 for large text
**Validates: Requirements 15.4**

**Property 27: ARIA label completeness**
*For any* interactive element, a descriptive ARIA label must be present
**Validates: Requirements 15.2**

**Property 28: Non-color indicators**
*For any* information conveyed by color, additional non-color indicators (icons or text) must also be present
**Validates: Requirements 15.3**

**Property 29: Database query optimization**
*For any* dashboard load, the number of database queries must not exceed a defined threshold (e.g., 20 queries)
**Validates: Requirements 16.4**

**Property 30: Profile completeness achievement award**
*For any* user whose profile reaches 100 percent completeness, the profile completion achievement must be awarded and 50 bonus points must be added
**Validates: Requirements 11.3**

**Property 31: Payment summary accuracy**
*For any* user, the payment summary total spent must equal the sum of all completed payment amounts, and recent payments count must match the count of payments in the last 30 days
**Validates: Requirements 12.1, 12.2**

**Property 32: Default payment method uniqueness**
*For any* user, at most one payment method can be marked as default at any time
**Validates: Requirements 12.3**

**Property 33: Report submission validation**
*For any* user report submission, the reporter and reported user must be different users, and the description must not be empty
**Validates: Requirements 10.3**

**Property 34: Responsive image sizing**
*For any* image served on mobile devices, the image dimensions must be within 10 percent variance of the device screen resolution
**Validates: Requirements 14.5**

**Property 35: Profile completeness calculation accuracy**
*For any* user, the profile completeness percentage must equal (total earned points / maximum possible points) * 100, rounded to nearest integer
**Validates: Requirements 11.1, 11.2**

**Property 36: Incomplete fields list accuracy**
*For any* user, the incomplete fields list must contain exactly those fields from FIELD_WEIGHTS that are empty or null
**Validates: Requirements 11.4**

**Property 37: Dashboard quick actions completeness**
*For any* dashboard display, all four quick action buttons (register for tournament, join team, view notifications, manage payment methods) must be present and functional
**Validates: Requirements 1.5**

**Property 38: Dashboard statistics cards accuracy**
*For any* dashboard display, the statistics cards must show accurate counts for total tournaments, win rate, current teams, and unread notifications
**Validates: Requirements 1.2**

**Property 39: Mobile navigation presence**
*For any* page viewed on mobile devices (viewport width < 768px), the bottom navigation bar must be present with all four navigation items
**Validates: Requirements 14.3**

**Property 40: Mobile layout responsiveness**
*For any* dashboard or profile page, when viewport width is less than 768px, the layout must switch to single-column stacked layout
**Validates: Requirements 14.1, 14.2**

## Security Considerations

### Authentication & Authorization

1. **Profile Access Control**:
   - Users can only edit their own profiles
   - Public profiles are viewable by all authenticated users
   - Private profiles enforce friend-only visibility
   - Admin users can view all profiles for moderation

2. **Data Export Security**:
   - Exports require authentication
   - Exports are logged with IP address for audit trail
   - Sensitive data (passwords, payment details) excluded from exports
   - Rate limiting on export requests (1 per hour per user)

3. **Account Deletion Security**:
   - Requires password re-entry for verification
   - Confirmation dialog with clear consequences
   - Irreversible action with email confirmation
   - Audit log entry created

### Data Privacy

1. **Privacy Settings**:
   - Granular control over profile visibility
   - Activity feed visibility control
   - Online status visibility control
   - Default to most restrictive settings for new users

2. **GDPR Compliance**:
   - Data export functionality for data portability
   - Account deletion with data anonymization
   - Clear privacy policy and consent
   - Audit trail for data access and modifications

3. **Data Minimization**:
   - Only collect necessary profile information
   - Optional fields clearly marked
   - No tracking without consent
   - Regular cleanup of old activity data (90 days)

### Input Validation

1. **Profile Data**:
   - Email format validation
   - Username length and character restrictions
   - Bio length limits (500 characters)
   - Date of birth validation (must be in past, age >= 13)

2. **Image Uploads**:
   - File type validation (JPG, PNG, GIF only)
   - File size limits (2MB for avatars, 5MB for banners)
   - Image dimension validation (avatars resized to 400x400, banners to 1920x400)
   - Malware scanning for uploaded files
   - Automatic orientation correction based on EXIF data

3. **SQL Injection Prevention**:
   - Use Django ORM for all database queries
   - Parameterized queries for raw SQL
   - Input sanitization for user-provided data

4. **XSS Prevention**:
   - Django template auto-escaping enabled
   - Sanitize user-generated content (bio, display name)
   - Content Security Policy headers

## Performance Optimization

### Caching Strategy

1. **Redis Cache Layers**:
   - **L1 - User Statistics**: 1 hour TTL
   - **L2 - Game Statistics**: 1 hour TTL
   - **L3 - Tournament History**: 1 hour TTL
   - **L4 - Activity Feed**: 15 minutes TTL
   - **L5 - Recommendations**: 24 hours TTL

2. **Cache Invalidation**:
   - Invalidate user stats on profile update
   - Invalidate game stats on match completion
   - Invalidate tournament history on tournament completion
   - Invalidate activity feed on new activity
   - Invalidate recommendations on user preference change

3. **Cache Warming**:
   - Pre-calculate statistics for active users
   - Background job to refresh popular profiles
   - Lazy loading for inactive users

### Database Optimization

1. **Indexing Strategy**:
   - Index on user_id for all user-related queries
   - Composite index on (user_id, created_at) for activity feed
   - Index on (user_id, is_completed) for achievements
   - Index on (user_id, is_main_game) for game profiles

2. **Query Optimization**:
   - Use select_related() for foreign key relationships
   - Use prefetch_related() for many-to-many relationships
   - Limit query results with pagination
   - Use only() and defer() to fetch only needed fields

3. **Database Connection Pooling**:
   - Connection pool size: 20
   - Max overflow: 10
   - Connection timeout: 30 seconds

### Frontend Optimization

1. **Image Optimization**:
   - Serve WebP format with fallback
   - Responsive images for different screen sizes using srcset
   - Image sizing strategy:
     - Mobile (< 768px): Serve images at 1x and 2x device pixel ratio
     - Tablet (768-1024px): Serve images at 1.5x device pixel ratio
     - Desktop (> 1024px): Serve images at native resolution
   - Avatar sizes: 50px, 100px, 200px, 400px (original)
   - Banner sizes: 640px, 1280px, 1920px
   - Lazy loading for below-the-fold images
   - CDN for static assets with cache headers (24 hours for avatars/banners)
   - Automatic image format detection and serving (WebP for supported browsers, JPEG/PNG fallback)

2. **JavaScript Optimization**:
   - Minify and bundle JavaScript
   - Code splitting for large components
   - Defer non-critical JavaScript
   - Use Alpine.js for lightweight interactivity

3. **CSS Optimization**:
   - Minify and bundle CSS
   - Critical CSS inlining
   - Remove unused CSS
   - Use CSS Grid and Flexbox for layouts

4. **Accessibility Optimization**:
   - Keyboard navigation support with visible focus indicators (2px solid outline)
   - Focus trap for modals and dialogs
   - Skip navigation links for screen readers
   - Logical tab order for all interactive elements
   - ARIA live regions for dynamic content updates
   - ARIA labels for all icon-only buttons
   - Color contrast validation in CI/CD pipeline

## Deployment Considerations

### Environment Configuration

1. **Development**:
   - DEBUG = True
   - Local Redis instance
   - SQLite database
   - No caching for development

2. **Staging**:
   - DEBUG = False
   - Shared Redis instance
   - PostgreSQL database
   - Full caching enabled
   - Performance monitoring

3. **Production**:
   - DEBUG = False
   - Redis cluster for high availability
   - PostgreSQL with read replicas
   - Full caching with monitoring
   - Error tracking (Sentry)
   - Performance monitoring (New Relic)

### Monitoring & Alerting

1. **Application Metrics**:
   - Dashboard load time
   - Profile page load time
   - Statistics calculation time
   - Cache hit rate
   - Database query count

2. **System Metrics**:
   - CPU usage
   - Memory usage
   - Redis memory usage
   - Database connection pool usage
   - Disk I/O

3. **Alerts**:
   - Dashboard load time > 1 second
   - Cache hit rate < 70%
   - Database query count > 50 per request
   - Error rate > 1%
   - Redis memory usage > 80%

### Backup & Recovery

1. **Database Backups**:
   - Daily full backups
   - Hourly incremental backups
   - 30-day retention policy
   - Automated backup testing

2. **Redis Backups**:
   - RDB snapshots every 6 hours
   - AOF for durability
   - Backup to S3

3. **Disaster Recovery**:
   - Recovery Time Objective (RTO): 4 hours
   - Recovery Point Objective (RPO): 1 hour
   - Documented recovery procedures
   - Regular disaster recovery drills

## Future Enhancements

### Phase 2 Features (Deferred from Requirements)

**Note**: The requirements document mentions several features that are being deferred to Phase 2 to focus on core functionality first. The UI includes placeholder buttons for these features to maintain a complete user experience.

1. **Social Features** (Referenced in Req 10.3):
   - Friend system with friend requests and friend lists
   - Direct messaging between users
   - Profile comments
   - Activity feed sharing
   - "Add Friend" and "Send Message" buttons are present but disabled with tooltips explaining "Coming Soon"

2. **Advanced Statistics**:
   - Head-to-head comparisons
   - Platform-wide leaderboards
   - Skill rating trends with predictive analytics
   - Performance predictions using ML

3. **Gamification**:
   - Daily challenges
   - Streak tracking
   - Seasonal events
   - Exclusive rewards

### Phase 3 Features

1. **Mobile App**:
   - Native iOS app
   - Native Android app
   - Push notifications
   - Offline mode

2. **AI Features**:
   - Personalized coaching tips
   - Match analysis
   - Opponent scouting
   - Tournament predictions

3. **Integration**:
   - Twitch streaming integration
   - Discord rich presence
   - Steam achievements sync
   - Third-party tournament platforms
