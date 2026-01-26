from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    # Team list and search
    path('', views.TeamListView.as_view(), name='list'),
    
    # Team creation
    path('create/', views.TeamCreateView.as_view(), name='create'),
    
    # Team detail
    path('<slug:slug>/', views.TeamDetailView.as_view(), name='detail'),
    
    # Team settings (captain only)
    path('<slug:slug>/settings/', views.TeamSettingsView.as_view(), name='settings'),
    
    # Roster management (captain/co-captain)
    path('<slug:slug>/roster/', views.TeamRosterView.as_view(), name='roster'),
    
    # Team invitations
    path('<slug:slug>/invites/', views.TeamInvitesView.as_view(), name='invites'),
    path('<slug:slug>/invite/send/', views.TeamInviteSendView.as_view(), name='invite_send'),
    path('<slug:slug>/invite/<uuid:invite_id>/cancel/', views.TeamInviteCancelView.as_view(), name='invite_cancel'),
    path('invite/<uuid:invite_id>/accept/', views.TeamInviteAcceptView.as_view(), name='invite_accept'),
    path('invite/<uuid:invite_id>/decline/', views.TeamInviteDeclineView.as_view(), name='invite_decline'),
    path('api/user-search/', views.TeamUserSearchView.as_view(), name='user_search'),
    
    # Team applications
    path('<slug:slug>/apply/', views.TeamApplyView.as_view(), name='apply'),
    path('<slug:slug>/applications/', views.TeamApplicationsView.as_view(), name='applications'),
    path('<slug:slug>/application/<uuid:member_id>/approve/', views.TeamApplicationApproveView.as_view(), name='application_approve'),
    path('<slug:slug>/application/<uuid:member_id>/decline/', views.TeamApplicationDeclineView.as_view(), name='application_decline'),
    
    # Team announcements
    path('<slug:slug>/announcements/', views.TeamAnnouncementsView.as_view(), name='announcements'),
    path('<slug:slug>/announcements/post/', views.TeamAnnouncementPostView.as_view(), name='announcement_post'),
    
    # Team statistics
    path('<slug:slug>/stats/', views.TeamStatsView.as_view(), name='stats'),
    
    # Team achievements
    path('<slug:slug>/achievements/', views.TeamAchievementsView.as_view(), name='achievements'),
    
    # Team tournament history
    path('<slug:slug>/tournaments/', views.TeamTournamentHistoryView.as_view(), name='tournament_history'),
    
    # Team actions
    path('<slug:slug>/leave/', views.TeamLeaveView.as_view(), name='leave'),
    path('<slug:slug>/disband/', views.TeamDisbandView.as_view(), name='disband'),
    path('<slug:slug>/transfer-captaincy/', views.TeamTransferCaptaincyView.as_view(), name='transfer_captaincy'),
    path('<slug:slug>/member/<uuid:member_id>/remove/', views.TeamMemberRemoveView.as_view(), name='member_remove'),
    path('<slug:slug>/member/<uuid:member_id>/role/', views.TeamMemberRoleChangeView.as_view(), name='member_role_change'),
]
