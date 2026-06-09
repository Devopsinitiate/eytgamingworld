# Team Management Notification Triggers

This document provides a comprehensive overview of all notification triggers implemented for the team management system.

**Requirements:** 4.3, 5.3, 9.2, 15.4

## Overview

The team notification system is implemented through the `TeamNotificationService` class in `teams/notification_service.py`. Notifications are triggered at key points in the team lifecycle to keep members informed and engaged.

## Notification Categories

### 1. Team Invitations (Requirement 4.3)

#### 1.1 Invite Sent
- **Trigger:** When a captain/co-captain sends an invitation to a user
- **Recipients:** Invited user
- **Priority:** Normal
- **Delivery:** In-app + Email
- **Location:** `teams/views.py` - `TeamInviteSendView.post()`
- **Method:** `TeamNotificationService.notify_team_invite()`

#### 1.2 Invite Accepted
- **Trigger:** When a user accepts a team invitation
- **Recipients:** Team captain
- **Priority:** Normal
- **Delivery:** In-app
- **Location:** `teams/views.py` - `TeamInviteAcceptView.post()`
- **Method:** `TeamNotificationService.notify_invite_accepted()`

#### 1.3 Invite Declined
- **Trigger:** When a user declines a team invitation
- **Recipients:** Team captain
- **Priority:** Low
- **Delivery:** In-app
- **Location:** `teams/views.py` - `TeamInviteDeclineView.post()`
- **Method:** `TeamNotificationService.notify_invite_declined()`

### 2. Team Applications (Requirement 5.3)

#### 2.1 New Application
- **Trigger:** When a user applies to join a team
- **Recipients:** Team captain
- **Priority:** Normal
- **Delivery:** In-app + Email
- **Location:** `teams/views.py` - `TeamApplyView.post()`
- **Method:** `TeamNotificationService.notify_new_application()`

#### 2.2 Application Approved
- **Trigger:** When a captain/co-captain approves an application
- **Recipients:** Applicant
- **Priority:** Normal
- **Delivery:** In-app + Email
- **Location:** `teams/views.py` - `TeamApplicationApproveView.post()`
- **Method:** `TeamNotificationService.notify_application_approved()`

#### 2.3 Application Declined
- **Trigger:** When a captain/co-captain declines an application
- **Recipients:** Applicant
- **Priority:** Low
- **Delivery:** In-app
- **Location:** `teams/views.py` - `TeamApplicationDeclineView.post()`
- **Method:** `TeamNotificationService.notify_application_declined()`

### 3. Team Announcements (Requirement 9.2)

#### 3.1 New Announcement
- **Trigger:** When a captain/co-captain posts an announcement
- **Recipients:** All active team members (except poster)
- **Priority:** Based on announcement priority
  - Urgent → High priority
  - Important → Normal priority
  - Normal → Low priority
- **Delivery:** 
  - Urgent: In-app + Email
  - Important/Normal: In-app only
- **Location:** `teams/views.py` - `TeamAnnouncementPostView.post()`
- **Method:** `TeamNotificationService.notify_team_announcement()`

### 4. Role Changes

#### 4.1 Role Changed
- **Trigger:** When a captain changes a member's role
- **Recipients:** Member whose role changed
- **Priority:** 
  - High (for promotions to captain/co-captain)
  - Normal (for other changes)
- **Delivery:** 
  - High priority: In-app + Email
  - Normal priority: In-app only
- **Location:** `teams/views.py` - `TeamMemberRoleChangeView.post()`
- **Method:** `TeamNotificationService.notify_role_change()`

#### 4.2 Captaincy Transfer
- **Trigger:** When captaincy is transferred to another member
- **Recipients:** New captain
- **Priority:** High
- **Delivery:** In-app + Email
- **Location:** `teams/views.py` - `TeamTransferCaptaincyView.post()`
- **Method:** `TeamNotificationService.notify_captaincy_transfer()`

### 5. Team Events (Tournament-Related)

#### 5.1 Tournament Registration
- **Trigger:** When a team is registered for a tournament
- **Recipients:** All active team members (except registrant)
- **Priority:** Normal
- **Delivery:** In-app
- **Location:** `tournaments/views.py` - `tournament_register()`
- **Method:** `TeamNotificationService.notify_tournament_registration()`

#### 5.2 Tournament Starting
- **Trigger:** When a tournament is about to start (automated via Celery task)
- **Recipients:** All active team members
- **Priority:** High
- **Delivery:** In-app + Email
- **Location:** `tournaments/tasks.py` - `send_tournament_start_notifications()`
- **Method:** `TeamNotificationService.notify_tournament_starting()`

#### 5.3 Tournament Win
- **Trigger:** When a team wins a tournament (via signal)
- **Recipients:** All active team members
- **Priority:** High
- **Delivery:** In-app + Email
- **Location:** `teams/signals.py` - `check_tournament_achievements()`
- **Method:** `TeamNotificationService.notify_tournament_win()`

### 6. Team Achievements (Requirement 15.4)

#### 6.1 Achievement Earned
- **Trigger:** When a team earns an achievement (via signal)
- **Recipients:** All active team members
- **Priority:** Normal
- **Delivery:** In-app
- **Location:** `teams/signals.py` - `check_tournament_achievements()` and other achievement signals
- **Method:** `TeamNotificationService.notify_achievement_earned()`

### 7. Roster Changes

#### 7.1 Member Joined
- **Trigger:** When a new member joins the team (via invite acceptance or application approval)
- **Recipients:** Team captain
- **Priority:** Normal
- **Delivery:** In-app
- **Location:** 
  - `teams/views.py` - `TeamInviteAcceptView.post()`
  - `teams/views.py` - `TeamApplicationApproveView.post()`
- **Method:** `TeamNotificationService.notify_member_joined()`

#### 7.2 Member Left
- **Trigger:** When a member leaves the team
- **Recipients:** Team captain (or all members if specified)
- **Priority:** Normal (captain) / Low (all members)
- **Delivery:** In-app
- **Location:** `teams/views.py` - `TeamLeaveView.post()`
- **Method:** `TeamNotificationService.notify_member_left()`

#### 7.3 Member Removed
- **Trigger:** When a captain/co-captain removes a member
- **Recipients:** Removed member
- **Priority:** Normal
- **Delivery:** In-app + Email
- **Location:** `teams/views.py` - `TeamMemberRemoveView.post()`
- **Method:** `TeamNotificationService.notify_member_removed()`

#### 7.4 Team Disbanded
- **Trigger:** When a captain disbands the team
- **Recipients:** All active team members (except captain)
- **Priority:** Normal
- **Delivery:** In-app + Email
- **Location:** `teams/views.py` - `TeamDisbandView.post()`
- **Method:** `TeamNotificationService.notify_team_disbanded()`

## Notification Delivery Methods

The system supports multiple delivery methods:

1. **In-App:** Notifications appear in the user's notification center
2. **Email:** Notifications are sent via email (respects user preferences)
3. **Push:** Placeholder for future push notification support
4. **SMS:** Placeholder for future SMS support
5. **Discord:** Placeholder for future Discord webhook support

## Priority Levels

Notifications use four priority levels:

- **Urgent:** Critical notifications requiring immediate attention
- **High:** Important notifications (promotions, tournament events)
- **Normal:** Standard notifications (invites, applications, announcements)
- **Low:** Informational notifications (declines, minor updates)

## User Preferences

Users can configure notification preferences through the `NotificationPreference` model:

- Enable/disable in-app notifications
- Enable/disable email notifications
- Configure quiet hours
- Set notification preferences by type (tournament, team, coaching, etc.)

## Testing

All notification triggers are tested in `teams/test_notification_service.py`:

- 15 unit tests covering all notification types
- Tests verify correct recipients, priority levels, and delivery methods
- Tests validate notification content and metadata

## Signal-Based Notifications

Some notifications are triggered automatically via Django signals:

1. **Tournament Win:** Triggered when a team's tournament participant has `final_placement == 1`
2. **Achievements:** Triggered when achievement conditions are met (tournament wins, milestones, etc.)

These are defined in `teams/signals.py`.

## Future Enhancements

Potential future notification triggers:

- Match reminders (30 minutes before scheduled match)
- Practice session reminders
- Team event reminders
- Roster milestone notifications (e.g., team reaches full capacity)
- Inactivity warnings
- Tournament bracket updates
- Prize distribution notifications

## Architecture Notes

### Centralized Service

All team notifications go through `TeamNotificationService` to ensure:
- Consistent notification format
- Centralized logic for recipient selection
- Easy maintenance and updates
- Comprehensive testing coverage

### Metadata Storage

Notifications include rich metadata in JSON format:
- Team ID and name
- User IDs and names
- Tournament information
- Achievement details
- Custom event-specific data

This metadata enables:
- Rich notification rendering
- Deep linking to relevant pages
- Analytics and reporting
- Future notification enhancements

### Performance Considerations

- Bulk notification creation for team-wide announcements
- Async task processing for tournament notifications (via Celery)
- Efficient database queries with select_related/prefetch_related
- Notification batching for high-volume events

## Compliance

This implementation satisfies the following requirements:

- **Requirement 4.3:** Team invite notifications
- **Requirement 5.3:** Application status change notifications
- **Requirement 9.2:** Team announcement notifications with priority indicators
- **Requirement 15.4:** Team achievement notifications

All notification triggers are fully implemented, tested, and integrated into the team management workflow.
