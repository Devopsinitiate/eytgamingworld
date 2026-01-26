# Implementation Plan: User Profile & Dashboard System

## Current State Analysis
- ✅ User model exists in core/models.py with basic profile fields
- ✅ UserGameProfile model exists with statistics tracking
- ✅ Dashboard app exists with basic dashboard_home view
- ✅ Redis/cache configured in settings
- ✅ Team achievement system exists (can be used as reference)
- ❌ No Activity, Achievement, UserAchievement, Recommendation, ProfileCompleteness, or UserReport models
- ❌ User model missing: banner, online_status_visible, activity_visible, statistics_visible fields
- ❌ No profile-specific views or templates beyond basic dashboard
- ❌ No statistics, activity, or recommendation services

## Implementation Tasks

- [x] 1. Extend User model and create new models









  - [x] 1.1 Add new fields to User model via migration


    - Add banner (ImageField)
    - Add online_status_visible (BooleanField, default=True)
    - Add activity_visible (BooleanField, default=True)
    - Add statistics_visible (BooleanField, default=True)
    - _Requirements: 2.5, 9.2, 10.2_
  
  - [x] 1.2 Create Activity model


    - User activity log with activity_type, content_type, object_id, data (JSONField)
    - Indexes on (user, created_at) and (activity_type, created_at)
    - _Requirements: 1.3, 8.1, 8.2_
  
  - [x] 1.3 Create Achievement model


    - Achievement definitions with name, slug, description, type, rarity, icon
    - Fields: is_progressive, target_value, points_reward, is_active, is_hidden
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [x] 1.4 Create UserAchievement model


    - User's earned achievements with progress tracking
    - Fields: current_value, is_completed, in_showcase, showcase_order
    - Unique constraint on (user, achievement)
    - _Requirements: 7.1, 7.2, 7.5_
  
  - [x] 1.5 Create Recommendation model










    - Cached recommendations with content_type, object_id, score, reason
    - Fields: is_dismissed, dismissed_at, expires_at
    - _Requirements: 13.1, 13.2, 13.3, 13.4_
  
  - [x] 1.6 Create ProfileCompleteness model


    - OneToOne with User, tracks total_points, percentage
    - FIELD_WEIGHTS dictionary with weighted scoring
    - calculate_for_user() class method
    - _Requirements: 11.1, 11.2, 11.4_
  

  - [x] 1.7 Create UserReport model

    - User reports for moderation with category, description, status
    - Fields: reporter, reported_user, reviewed_by, resolution_notes
    - _Requirements: 10.3_

  
  - [x] 1.8 Register all new models in admin

    - Activity, Achievement, UserAchievement, Recommendation, ProfileCompleteness, UserReport
    - _Requirements: All_

- [x] 1.9 Write property test for win rate calculation





  - **Property 1: Statistics calculation correctness**
  - **Validates: Requirements 3.1, 3.5**

- [x] 1.10 Write property test for profile completeness bounds



  - **Property 2: Profile completeness bounds**
  - **Validates: Requirements 11.1, 11.2**

- [x] 2. Implement ProfileCompleteness service





  - [x] 2.1 Create signal handlers to recalculate on profile updates


    - Connect to User post_save signal
    - Connect to UserGameProfile post_save/post_delete signals
    - Call ProfileCompleteness.calculate_for_user() on changes
    - _Requirements: 11.2_

- [x] 2.2 Write property test for profile completeness calculation



  - **Property 35: Profile completeness calculation accuracy**
  - **Validates: Requirements 11.1, 11.2**

- [x] 2.3 Write property test for incomplete fields list



  - **Property 36: Incomplete fields list accuracy**
  - **Validates: Requirements 11.4**

- [x] 2.4 Write property test for profile completeness achievement



  - **Property 30: Profile completeness achievement award**
  - **Validates: Requirements 11.3**

- [x] 3. Implement Statistics Service





  - [x] 3.1 Create dashboard/services.py with StatisticsService class


    - Implement get_user_statistics() - aggregate from Participant model
    - Implement get_game_statistics(user_id, game_id) - per-game stats
    - Implement get_tournament_history(user_id, filters) - with filtering
    - Implement calculate_win_rate(user_id, game_id=None) - percentage calculation
    - Implement get_performance_trend(user_id, days=30) - trend data
    - Add Redis caching with 1-hour TTL using cache keys like f"user_stats:{user_id}"
    - Implement invalidate_cache(user_id) method
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 16.1, 16.2_

- [x] 3.2 Write property test for statistics bounds



  - **Property 1: Statistics calculation correctness**
  - **Validates: Requirements 3.1, 3.5**

- [x] 3.3 Write property test for cache consistency



  - **Property 19: Cache consistency**
  - **Validates: Requirements 16.1, 16.2, 16.3**

- [x] 3.4 Write property test for cache TTL



  - **Property 20: Cache TTL enforcement**
  - **Validates: Requirements 16.1, 16.5**

- [x] 4. Implement Activity Service





  - [x] 4.1 Create dashboard/services.py ActivityService class


    - Implement record_activity(user_id, activity_type, data) - create Activity record
    - Implement get_activity_feed(user_id, filters, page) - with filtering and pagination
    - Implement get_activity_types() - return list of activity types
    - Implement delete_old_activities(days=90) - cleanup method
    - _Requirements: 1.3, 8.1, 8.2, 8.3_

- [x] 4.2 Write property test for activity chronological ordering









  - **Property 5: Activity feed chronological ordering**
  - **Validates: Requirements 1.3, 8.1**

- [x] 4.3 Write property test for activity filtering






  - **Property 13: Activity feed filtering**
  - **Validates: Requirements 8.3**



- [x] 4.4 Write property test for activity pagination






  - **Property 11: Pagination consistency**
  - **Validates: Requirements 5.5, 8.5**

  - [x] 4.5 Create dashboard/signals.py with signal handlers


    - Connect to tournament registration/completion signals
    - Connect to team join/leave signals
    - Connect to achievement earned signals
    - Connect to payment completed signals
    - Connect to User post_save for profile updates
    - Call ActivityService.record_activity() in each handler
    - _Requirements: 8.2_

- [x] 5. Implement Achievement System





  - [x] 5.1 Create dashboard/services.py AchievementService class


    - Implement check_achievements(user_id, event_type) - check and award if criteria met
    - Implement award_achievement(user_id, achievement_id) - create UserAchievement
    - Implement get_user_achievements(user_id) - return QuerySet
    - Implement get_achievement_progress(user_id, achievement_id) - return progress dict
    - Implement update_showcase(user_id, achievement_ids) - update showcase (max 6)
    - Implement get_rare_achievements(user_id) - achievements earned by <10% of users
    - _Requirements: 7.1, 7.5_

- [x] 5.2 Write property test for achievement progress bounds







  - **Property 9: Achievement progress bounds**
  - **Validates: Requirements 7.2**

- [x] 5.3 Write property test for achievement showcase limit










  - **Property 10: Achievement showcase limit**
  - **Validates: Requirements 7.5**




- [x]* 5.4 Write property test for rare achievement highlighting

  - **Property 24: Rare achievement highlighting**
  - **Validates: Requirements 7.4**

  - [x] 5.5 Create initial achievement definitions via data migration


    - First tournament win (tournament type)
    - 10 tournaments participated (tournament type)
    - Top 3 finish (tournament type)
    - Join first team (social type)
    - Profile completion (platform type)
    - _Requirements: 7.1, 7.3_

- [x] 6. Implement Recommendation Service





  - [x] 6.1 Create dashboard/services.py RecommendationService class


    - Implement get_tournament_recommendations(user_id) - match game profiles and skill
    - Implement get_team_recommendations(user_id) - match recruiting teams
    - Implement calculate_recommendation_score(user, item) - scoring algorithm
    - Implement dismiss_recommendation(user_id, rec_id) - mark as dismissed
    - Implement refresh_recommendations(user_id) - regenerate recommendations
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [x] 6.2 Write property test for recommendation dismissal



  - **Property 15: Recommendation dismissal persistence**
  - **Validates: Requirements 13.4**

  - [x] 6.3 Create dashboard/tasks.py with Celery task for daily refresh


    - refresh_user_recommendations task
    - Schedule to run daily
    - _Requirements: 13.5_

- [x] 7. Implement Privacy Service




  - [x] 7.1 Create dashboard/services.py PrivacyService class


    - Implement can_view_profile(viewer, profile_owner) - check privacy settings
    - Implement can_view_statistics(viewer, profile_owner) - check statistics_visible
    - Implement can_view_activity(viewer, profile_owner) - check activity_visible
    - Implement filter_profile_data(viewer, profile_data) - filter based on permissions
    - Implement get_privacy_settings(user_id) - return settings dict
    - Implement update_privacy_settings(user_id, settings) - update User fields
    - Implement are_friends(user1, user2) - placeholder returning False (Phase 2)
    - _Requirements: 2.5, 9.2, 10.2, 10.5_

- [x] 7.2 Write property test for privacy enforcement




  - **Property 8: Privacy enforcement**
  - **Validates: Requirements 2.5, 10.2, 10.5**

- [x] 8. Implement Payment Summary Service




  - [x] 8.1 Create dashboard/services.py PaymentSummaryService class


    - Implement get_payment_summary(user_id) - aggregate payment data
    - Implement get_recent_payments(user_id, limit=5) - last N payments
    - Implement get_saved_payment_methods_count(user_id) - count from payments module
    - Implement has_default_payment_method(user_id) - check for default
    - Query payments.models.Payment and payments.models.PaymentMethod
    - _Requirements: 12.1, 12.2, 12.3_

- [x] 8.2 Write property test for payment summary accuracy






  - **Property 31: Payment summary accuracy**
  - **Validates: Requirements 12.1, 12.2**

- [x] 8.3 Write property test for default payment method uniqueness






  - **Property 32: Default payment method uniqueness**
  - **Validates: Requirements 12.3**

- [x] 9. Implement Profile Export Service






  - [x] 9.1 Create dashboard/services.py ProfileExportService class


    - Implement generate_export(user_id) - return JSON dict
    - Include: profile info, game profiles, tournament history, team memberships, payment history
    - Exclude: password hash, payment method details
    - Use security.models.AuditLog for logging
    - _Requirements: 17.1, 17.2, 17.5_

- [x] 9.2 Write property test for export data completeness




  - **Property 21: Export data completeness**
  - **Validates: Requirements 17.1, 17.2, 17.5**


- [x] 9.3 Write property test for export audit logging




  - **Property 22: Export audit logging**
  - **Validates: Requirements 17.4**

- [x] 10. Implement Dashboard Views





  - [x] 10.1 Enhance dashboard/views.py dashboard_home view


    - Call StatisticsService.get_user_statistics() for stats cards
    - Call ActivityService.get_activity_feed() for recent activity (limit 10)
    - Query Tournament model for upcoming events (7-day window)
    - Call RecommendationService.get_tournament_recommendations() (limit 3)
    - Call PaymentSummaryService.get_payment_summary()
    - Pass all data to template context
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 12.1_

- [x] 10.2 Write property test for upcoming events time window





  - **Property 6: Upcoming events time window**
  - **Validates: Requirements 1.4**

- [x] 10.3 Write property test for dashboard quick actions





  - **Property 37: Dashboard quick actions completeness**
  - **Validates: Requirements 1.5**


- [x] 10.4 Write property test for statistics cards accuracy







  - **Property 38: Dashboard statistics cards accuracy**
  - **Validates: Requirements 1.2**

  - [x] 10.5 Create dashboard/views.py dashboard_activity view


    - Accept filter parameters (activity_type, date_range)
    - Call ActivityService.get_activity_feed() with filters
    - Implement pagination (25 per page) using Django Paginator
    - _Requirements: 8.3, 8.5_

  - [x] 10.6 Create dashboard/views.py dashboard_stats view


    - Call StatisticsService.get_user_statistics()
    - Call StatisticsService.get_performance_trend(days=30)
    - Pass data for Chart.js visualization
    - _Requirements: 3.4_

- [x] 11. Implement Profile Views





  - [x] 11.1 Create dashboard/views.py profile_view view


    - Accept username parameter
    - Load User and related game profiles
    - Call PrivacyService to check permissions
    - Call StatisticsService if viewer can see stats
    - Call ActivityService if viewer can see activity
    - Load UserAchievement.objects.filter(in_showcase=True)
    - Pass filtered data to template
    - _Requirements: 2.1, 10.1, 10.2, 10.5_

  - [x] 11.2 Create dashboard/views.py profile_edit view


    - Use ProfileEditForm for validation
    - Handle avatar upload with Pillow resize to 400x400
    - Handle banner upload with Pillow resize to 1920x400
    - Validate file sizes (2MB avatar, 5MB banner)
    - Call ProfileCompleteness.calculate_for_user() after save
    - Call ActivityService.record_activity() for profile_updated
    - _Requirements: 2.2, 2.3, 2.4_

- [x] 11.3 Write property test for avatar image processing






  - **Property 16: Avatar image processing**
  - **Validates: Requirements 2.3**

- [x] 11.4 Write property test for banner image processing





  - **Property 16b: Banner image processing**
  - **Validates: Requirements 16.5**

- [x] 11.5 Write property test for profile field validation





  - **Property 17: Profile field validation**
  - **Validates: Requirements 2.2**

  - [x] 11.6 Create dashboard/views.py profile_export view


    - Call ProfileExportService.generate_export()
    - Create AuditLog entry with timestamp and IP
    - Return JsonResponse with download headers
    - Filename format: {username}_profile_{date}.json
    - _Requirements: 17.1, 17.3, 17.4_

- [x] 12. Implement Game Profile Views




  - [x] 12.1 Create dashboard/views.py game profile management views

    - game_profile_list - list user's UserGameProfile objects
    - game_profile_create - create new UserGameProfile with GameProfileForm
    - game_profile_edit - edit existing UserGameProfile
    - game_profile_delete - check for tournament participations before delete
    - game_profile_set_main - unset previous main, set new main
    - All views require login and ownership check
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 12.2 Write property test for main game uniqueness






  - **Property 3: Main game uniqueness**
  - **Validates: Requirements 4.2**

- [x] 12.3 Write property test for game profile deletion protection







  - **Property 4: Game profile deletion protection**
  - **Validates: Requirements 4.4**

- [x] 12.4 Write property test for game profile sorting





  - **Property 7: Game profile sorting**
  - **Validates: Requirements 4.5**

- [x] 13. Implement Tournament History Views

















  - [x] 13.1 Create dashboard/views.py tournament_history view


    - Query Participant.objects.filter(user=request.user)
    - Accept filter parameters (game, date_range, placement)
    - Apply filters to QuerySet
    - Implement pagination (20 per page) using Django Paginator
    - Select_related tournament and game for optimization
    - _Requirements: 5.1, 5.2, 5.5_

- [x] 13.2 Write property test for tournament history filtering






  - **Property 12: Tournament history filtering**
  - **Validates: Requirements 5.2**

  - [x] 13.3 Create dashboard/views.py tournament_detail_history view

    - Query Match objects for specific tournament and user
    - Show match history with results
    - Show opponents faced
    - Show scores and timestamps
    - _Requirements: 5.3_

- [x] 14. Implement Team Views




  - [x] 14.1 Create dashboard/views.py team_membership view


    - Query TeamMember.objects.filter(user=request.user, status='active')
    - Query TeamMember.objects.filter(user=request.user, status='left') for history
    - Calculate team statistics from tournament participations
    - Query TeamInvitation.objects.filter(user=request.user, status='pending')
    - Pass all data to template
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 14.2 Write property test for mutual teams identification






  - **Property 14: Mutual teams identification**
  - **Validates: Requirements 10.4**

- [x] 15. Implement Settings Views




  - [x] 15.1 Create dashboard/views.py settings views


    - settings_profile - ProfileEditForm for basic info
    - settings_privacy - PrivacySettingsForm for visibility settings
    - settings_notifications - NotificationPreferencesForm (integrate with notifications app)
    - settings_security - PasswordChangeForm with current password verification
    - settings_connected_accounts - display Steam, Discord, Twitch connections
    - All views require login
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 15.2 Write property test for password change security








  - **Property 18: Password change security**
  - **Validates: Requirements 9.4**

- [x] 16. Implement Account Deletion




  - [x] 16.1 Create dashboard/views.py account_delete view

    - Display confirmation dialog with consequences
    - Require password re-entry for verification
    - Anonymize user data: replace name, email, bio with placeholders
    - Keep tournament Participant records but remove personal identifiers
    - Send confirmation email before deletion
    - Call logout(request) immediately after deletion
    - Create AuditLog entry
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [x] 16.2 Write property test for account deletion anonymization





  - **Property 23: Account deletion anonymization**
  - **Validates: Requirements 18.3, 18.4, 18.5**

- [x] 17. Implement Social Interaction Features





  - [x] 17.1 Create dashboard/views.py user_report view


    - Accept username parameter
    - Use UserReportForm with category and description
    - Validate reporter != reported_user
    - Create UserReport record with status='pending'
    - Send notification to admin users
    - Redirect with success message
    - _Requirements: 10.3_

- [x] 17.2 Write property test for report submission validation







  - **Property 33: Report submission validation**
  - **Validates: Requirements 10.3**


  - [x] 17.3 Add placeholder buttons in profile template

    - "Add Friend" button (disabled, data-tooltip="Coming Soon")
    - "Send Message" button (disabled, data-tooltip="Coming Soon")
    - Style as disabled with cursor-not-allowed
    - _Requirements: 10.3_

- [x] 18. Create Dashboard Templates





  - [x] 18.1 Update templates/dashboard/home.html


    - Extend base.html
    - Statistics cards section (tournaments, win rate, teams, notifications)
    - Activity feed section with activity list
    - Upcoming events section (7-day window)
    - Quick actions section (4 buttons)
    - Recommendations section (tournament and team recommendations)
    - Payment summary section (total spent, recent payments)
    - Responsive grid layout
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 12.1_

  - [x] 18.2 Create dashboard component templates

    - templates/dashboard/components/stats_cards.html
    - templates/dashboard/components/activity_feed.html
    - templates/dashboard/components/quick_actions.html
    - templates/dashboard/components/recommendations.html
    - templates/dashboard/components/mobile_nav.html
    - Use {% include %} in main templates
    - _Requirements: 1.2, 1.3, 1.5, 14.3_

- [x] 19. Create Profile Templates ✅ COMPLETE (Dec 9, 2024)







  - [x] 19.1 Create templates/dashboard/profile_view.html ✅


    - Profile header with avatar and banner images
    - Bio section with display_name and bio text
    - Game profiles section (list of UserGameProfile)
    - Achievements showcase (in_showcase=True achievements)
    - Statistics section (conditional on can_view_statistics)
    - Activity feed (conditional on can_view_activity)
    - Social action buttons (report, add friend, message)
    - **FIXED**: Removed invalid `|replace:"_":" "` filter (line 271) - Django doesn't have built-in replace filter
    - _Requirements: 2.1, 10.1, 10.2, 10.3_

  - [x] 19.2 Create templates/dashboard/profile_edit.html ✅


    - ProfileEditForm with all fields
    - Avatar upload input with preview using JavaScript
    - Banner upload input with preview using JavaScript
    - Profile completeness widget showing percentage and incomplete fields
    - Save button
    - **REDESIGNED**: Complete redesign with EYT Gaming branding (#b91c1c)
    - **IMPLEMENTED**: Clip-path styling (eyt-clip-path, eyt-clip-path-sm, eyt-clip-path-rev, eyt-clip-path-rev-sm)
    - **IMPLEMENTED**: Responsive layout (desktop 2/3 + 1/3, mobile single column)
    - **IMPLEMENTED**: Image preview functionality for avatar and banner
    - **IMPLEMENTED**: Profile completeness widget with progress bar
    - **IMPLEMENTED**: Gaming accounts section (Discord, Steam, Twitch)
    - **IMPLEMENTED**: Sidebar with quick links, tips, and account stats
    - _Requirements: 2.2, 2.3, 11.2_

  - [x] 19.3 Create profile component templates


    - templates/dashboard/components/game_profiles_list.html
    - templates/dashboard/components/game_profile_form.html
    - templates/dashboard/components/completeness_widget.html
    - templates/dashboard/components/report_user_modal.html
    - _Requirements: 4.3, 11.2, 10.3_

- [x] 20. Create Settings Templates







  - [x] 20.1 Create settings templates


    - templates/dashboard/settings/profile.html - ProfileEditForm
    - templates/dashboard/settings/privacy.html - PrivacySettingsForm
    - templates/dashboard/settings/notifications.html - NotificationPreferencesForm
    - templates/dashboard/settings/security.html - PasswordChangeForm
    - templates/dashboard/settings/connected_accounts.html - Steam, Discord, Twitch
    - templates/dashboard/settings/delete_account.html - Confirmation dialog
    - All extend base.html with settings sidebar navigation
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 18.1_

- [x] 21. Implement Responsive CSS





  - [x] 21.1 Create static/css/dashboard.css with responsive layouts


    - Desktop (>1024px): Multi-column grid layout
    - Tablet (768-1024px): Two-column layout
    - Mobile (<768px): Single-column stacked layout
    - Mobile bottom navigation bar (fixed position, z-index high)
    - Use CSS Grid and Flexbox
    - Media queries for breakpoints
    - _Requirements: 14.1, 14.2, 14.3_

- [x] 21.2 Write property test for mobile navigation presence













  - **Property 39: Mobile navigation presence**
  - **Validates: Requirements 14.3**


- [x] 21.3 Write property test for mobile layout responsiveness












  - **Property 40: Mobile layout responsiveness**
  - **Validates: Requirements 14.1, 14.2**

  - [x] 21.4 Implement responsive image serving in templates


    - Use {% thumbnail %} template tag or Pillow to create variants
    - Avatar sizes: 50px, 100px, 200px, 400px
    - Banner sizes: 640px, 1280px, 1920px
    - Use srcset attribute in <img> tags
    - _Requirements: 14.5_

- [x] 21.5 Write property test for responsive image sizing







  - **Property 34: Responsive image sizing**
  - **Validates: Requirements 14.5**

  - [x] 21.6 Ensure touch targets in CSS are 44x44 pixels minimum


    - Set min-width and min-height on buttons
    - Add padding to links
    - _Requirements: 14.4_

- [x] 21.7 Write property test for touch target accessibility





  - **Property 25: Touch target accessibility**
  - **Validates: Requirements 14.4**

- [x] 22. Implement Accessibility Features








  - [x] 22.1 Add keyboard navigation support in templates and CSS




    - Add :focus styles with 2px solid outline
    - Ensure logical tab order with tabindex where needed
    - Add skip navigation link at top of page
    - Implement focus trap for modals using JavaScript
    - _Requirements: 15.1_

  - [x] 22.2 Add ARIA labels and live regions in templates


    - Add aria-label to all icon-only buttons
    - Add aria-live="polite" to activity feed
    - Add aria-live="assertive" to error messages
    - Add role attributes where appropriate
    - _Requirements: 15.2, 15.5_

- [x] 22.3 Write property test for ARIA label completeness






  - **Property 27: ARIA label completeness**
  - **Validates: Requirements 15.2**

  - [x] 22.4 Ensure color contrast compliance in CSS


    - Use color contrast checker tool
    - Normal text: 4.5:1 minimum
    - Large text (18pt+): 3:1 minimum
    - Document color palette in CSS comments
    - _Requirements: 15.4_

- [x]* 22.5 Write property test for color contrast


  - **Property 26: Color contrast accessibility**
  - **Validates: Requirements 15.4**

  - [x] 22.6 Add non-color indicators in templates


    - Add icons next to status text (✓ for success, ✗ for error)
    - Add text labels for color-coded badges
    - Use patterns or shapes in addition to colors
    - _Requirements: 15.3_



- [x] 22.7 Write property test for non-color indicators

  - **Property 28: Non-color indicators**
  - **Validates: Requirements 15.3**

- [x] 23. Implement Performance Optimizations









  - [x] 23.1 Add database query optimization in views

    - Use select_related('game', 'user') for Participant queries
    - Use prefetch_related('game_profiles') for User queries
    - Add indexes to Activity model (user, created_at)
    - Use django-debug-toolbar to monitor query count
    - _Requirements: 16.4_

- [x] 23.2 Write property test for query optimization






  - **Property 29: Database query optimization**
  - **Validates: Requirements 16.4**

  - [x] 23.3 Implement Redis caching in services (already done in task 3.1)


    - StatisticsService uses cache with 1 hour TTL
    - ActivityService uses cache with 15 minutes TTL
    - RecommendationService uses cache with 24 hours TTL
    - _Requirements: 16.1, 16.2_

  - [x] 23.4 Add cache invalidation in signal handlers


    - Invalidate user stats on tournament completion
    - Invalidate activity feed on new activity
    - Invalidate recommendations on preference change
    - _Requirements: 16.3_

  - [x] 23.5 Optimize image serving in templates


    - Use Pillow to generate WebP versions
    - Add <picture> element with WebP and fallback
    - Add cache-control headers in nginx/settings
    - Add loading="lazy" to below-fold images
    - _Requirements: 16.5_

- [x] 24. Create URL Configuration





  - [x] 24.1 Update dashboard/urls.py with new URLs


    - path('', dashboard_home, name='home') - already exists
    - path('activity/', dashboard_activity, name='activity')
    - path('stats/', dashboard_stats, name='stats')
    - path('payments/summary/', dashboard_payment_summary, name='payment_summary')
    - _Requirements: 1.1, 8.1, 12.1_

  - [x] 24.2 Add profile URLs to dashboard/urls.py

    - path('profile/<str:username>/', profile_view, name='profile_view')
    - path('profile/edit/', profile_edit, name='profile_edit')
    - path('profile/export/', profile_export, name='profile_export')
    - path('profile/<str:username>/report/', user_report, name='user_report')
    - _Requirements: 2.1, 2.2, 10.1, 10.3, 17.1_

  - [x] 24.3 Add game profile URLs to dashboard/urls.py

    - path('games/', game_profile_list, name='game_profile_list')
    - path('games/add/', game_profile_create, name='game_profile_create')
    - path('games/<uuid:id>/edit/', game_profile_edit, name='game_profile_edit')
    - path('games/<uuid:id>/delete/', game_profile_delete, name='game_profile_delete')
    - path('games/<uuid:id>/set-main/', game_profile_set_main, name='game_profile_set_main')
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 24.4 Add settings URLs to dashboard/urls.py

    - path('settings/profile/', settings_profile, name='settings_profile')
    - path('settings/privacy/', settings_privacy, name='settings_privacy')
    - path('settings/notifications/', settings_notifications, name='settings_notifications')
    - path('settings/security/', settings_security, name='settings_security')
    - path('settings/accounts/', settings_connected_accounts, name='settings_accounts')
    - path('settings/delete/', account_delete, name='account_delete')
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 18.1_

- [x] 25. Create Forms




  - [x] 25.1 Create dashboard/forms.py with profile forms


    - ProfileEditForm(forms.ModelForm) - User model fields
    - AvatarUploadForm(forms.Form) - ImageField with validators
    - BannerUploadForm(forms.Form) - ImageField with validators
    - GameProfileForm(forms.ModelForm) - UserGameProfile model
    - Add clean methods for validation
    - _Requirements: 2.2, 2.3, 4.1_

  - [x] 25.2 Create settings forms in dashboard/forms.py

    - PrivacySettingsForm(forms.Form) - BooleanFields for visibility
    - NotificationPreferencesForm - integrate with notifications.forms
    - Use Django's PasswordChangeForm (already exists)
    - ConnectedAccountsForm(forms.Form) - display only, no inputs
    - AccountDeleteForm(forms.Form) - password confirmation field
    - _Requirements: 9.2, 9.3, 9.4, 9.5, 18.2_

  - [x] 25.3 Create social interaction forms in dashboard/forms.py

    - UserReportForm(forms.ModelForm) - UserReport model
    - ChoiceField for category
    - Textarea for description (max 1000 chars)
    - _Requirements: 10.3_

- [x] 26. Add Admin Interface




  - [x] 26.1 Update dashboard/admin.py to register models


    - @admin.register(Activity) with list_display, list_filter, search_fields
    - @admin.register(Achievement) with list_display, list_filter
    - @admin.register(UserAchievement) with list_display, list_filter
    - @admin.register(Recommendation) with list_display, list_filter
    - @admin.register(ProfileCompleteness) with list_display, readonly_fields
    - @admin.register(UserReport) with list_display, list_filter, actions
    - _Requirements: All_

  - [x] 26.2 Create custom admin actions for moderation


    - UserReportAdmin: add actions for 'mark_as_investigating', 'mark_as_resolved', 'mark_as_dismissed'
    - AchievementAdmin: add action for 'activate_achievements', 'deactivate_achievements'
    - Add filters for status, category, date ranges
    - _Requirements: 10.3, 7.1_

- [x] 27. Create Background Tasks





  - [x] 27.1 Create dashboard/tasks.py with Celery tasks


    - @shared_task refresh_user_recommendations(user_id) - call RecommendationService
    - Schedule with Celery Beat to run daily
    - _Requirements: 13.5_

  - [x] 27.2 Create cleanup task in dashboard/tasks.py


    - @shared_task cleanup_old_activities() - delete Activity records older than 90 days
    - Schedule with Celery Beat to run weekly
    - _Requirements: Data privacy_

  - [x] 27.3 Create achievement check task in dashboard/tasks.py


    - @shared_task check_user_achievements(user_id, event_type)
    - Call from tournament completion signal
    - Call from profile update signal
    - _Requirements: 7.1_

- [x] 28. Write Integration Tests









  - [x] 28.1 Create dashboard/tests/test_integration.py with dashboard load test





    - Create test user and login
    - GET /dashboard/
    - Assert response 200
    - Assert all widgets present in HTML
    - Assert cache keys created
    - _Requirements: 1.1_

  - [x] 28.2 Test profile update flow



    - Create test user
    - POST to profile_edit with updated data
    - Assert User object updated
    - Assert ProfileCompleteness recalculated
    - Assert cache invalidated
    - Assert Activity record created
    - _Requirements: 2.2, 2.4, 11.2_

  - [x] 28.3 Test achievement award flow



    - Create test user and achievement
    - Trigger event (e.g., complete tournament)
    - Assert UserAchievement created
    - Assert Activity record created
    - Assert notification sent
    - _Requirements: 7.1_

  - [x] 28.4 Test privacy enforcement flow



    - Create two test users
    - Set user1 profile to private
    - Login as user2, GET user1 profile
    - Assert statistics not visible
    - Set user1 profile to public
    - Assert statistics visible
    - _Requirements: 2.5, 10.2, 10.5_

  - [x] 28.5 Test export flow



    - Create test user with data
    - GET profile_export
    - Assert JSON response
    - Assert all required sections present
    - Assert sensitive data excluded
    - Assert AuditLog created
    - _Requirements: 17.1, 17.2, 17.4, 17.5_

  - [x] 28.6 Test account deletion flow




    - Create test user
    - POST to account_delete with password
    - Assert User data anonymized
    - Assert tournament records retained
    - Assert user logged out
    - Assert AuditLog created
    - _Requirements: 18.1, 18.2, 18.3, 18.5_

- [x] 29. Final Checkpoint - Ensure all tests pass







  - Run python manage.py test dashboard
  - Run python manage.py check
  - Ensure all migrations applied
  - Verify all URLs accessible
  - Test responsive layouts manually
  - Ask the user if questions arise
