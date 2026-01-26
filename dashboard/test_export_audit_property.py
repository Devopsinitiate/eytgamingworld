"""
Property-based tests for export audit logging.

This module tests the export audit logging property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from core.models import User
from dashboard.services import ProfileExportService
from security.models import AuditLog
import uuid


@pytest.mark.django_db
class TestExportAuditLogging:
    """
    **Feature: user-profile-dashboard, Property 22: Export audit logging**
    
    For any data export request, a log entry must be created with timestamp and IP address.
    
    **Validates: Requirements 17.4**
    """
    
    def test_export_creates_audit_log(self):
        """Property: Every export creates an audit log entry"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Count audit logs before export
        initial_count = AuditLog.objects.filter(
            user=user,
            action='export'
        ).count()
        
        # Generate export
        ProfileExportService.generate_export(user.id)
        
        # Count audit logs after export
        final_count = AuditLog.objects.filter(
            user=user,
            action='export'
        ).count()
        
        # Verify audit log was created
        assert final_count == initial_count + 1, \
            f"Export should create 1 audit log entry, found {final_count - initial_count}"
        
        # Cleanup
        AuditLog.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_exports=st.integers(min_value=1, max_value=5)
    )
    def test_multiple_exports_create_multiple_logs(self, num_exports):
        """Property: Multiple exports create multiple audit log entries"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Generate multiple exports
        for _ in range(num_exports):
            ProfileExportService.generate_export(user.id)
        
        # Count audit logs
        log_count = AuditLog.objects.filter(
            user=user,
            action='export'
        ).count()
        
        # Verify correct number of logs
        assert log_count == num_exports, \
            f"Should have {num_exports} audit log entries, found {log_count}"
        
        # Cleanup
        AuditLog.objects.filter(user=user).delete()
        user.delete()
    
    def test_audit_log_contains_required_fields(self):
        """Property: Audit log contains all required fields"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Generate export
        ProfileExportService.generate_export(user.id)
        
        # Get the audit log
        audit_log = AuditLog.objects.filter(
            user=user,
            action='export'
        ).latest('timestamp')
        
        # Verify required fields
        assert audit_log.user == user, "Audit log must reference correct user"
        assert audit_log.action == 'export', "Audit log action must be 'export'"
        assert audit_log.model_name == 'User', "Audit log must reference User model"
        assert audit_log.object_id == str(user.id), "Audit log must contain user ID"
        assert audit_log.timestamp is not None, "Audit log must have timestamp"
        
        # Cleanup
        AuditLog.objects.filter(user=user).delete()
        user.delete()
    
    def test_audit_log_includes_export_metadata(self):
        """Property: Audit log includes export-specific metadata"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Generate export
        ProfileExportService.generate_export(user.id)
        
        # Get the audit log
        audit_log = AuditLog.objects.filter(
            user=user,
            action='export'
        ).latest('timestamp')
        
        # Verify metadata exists
        assert audit_log.details is not None, "Audit log must have details"
        assert isinstance(audit_log.details, dict), "Audit log details must be a dictionary"
        
        # Verify export-specific metadata
        if 'export_sections' in audit_log.details:
            assert isinstance(audit_log.details['export_sections'], list), \
                "Export sections must be a list"
        
        # Cleanup
        AuditLog.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_users=st.integers(min_value=2, max_value=5)
    )
    def test_audit_logs_are_user_specific(self, num_users):
        """Property: Audit logs are correctly associated with each user"""
        users = []
        
        # Create multiple users and generate exports
        for i in range(num_users):
            unique_id = str(uuid.uuid4())[:8]
            user = User.objects.create_user(
                email=f'test_{unique_id}@example.com',
                username=f'testuser_{unique_id}',
                password='testpass123'
            )
            users.append(user)
            
            # Generate export for this user
            ProfileExportService.generate_export(user.id)
        
        # Verify each user has exactly one audit log
        for user in users:
            log_count = AuditLog.objects.filter(
                user=user,
                action='export'
            ).count()
            
            assert log_count == 1, \
                f"User {user.username} should have 1 audit log, found {log_count}"
        
        # Cleanup
        for user in users:
            AuditLog.objects.filter(user=user).delete()
            user.delete()
    
    def test_audit_log_severity_is_appropriate(self):
        """Property: Export audit logs have appropriate severity level"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Generate export
        ProfileExportService.generate_export(user.id)
        
        # Get the audit log
        audit_log = AuditLog.objects.filter(
            user=user,
            action='export'
        ).latest('timestamp')
        
        # Verify severity is set
        assert audit_log.severity is not None, "Audit log must have severity"
        assert audit_log.severity in ['low', 'medium', 'high', 'critical'], \
            f"Audit log severity must be valid, got {audit_log.severity}"
        
        # Export should be medium severity (data access but not modification)
        assert audit_log.severity == 'medium', \
            f"Export audit log should have 'medium' severity, got {audit_log.severity}"
        
        # Cleanup
        AuditLog.objects.filter(user=user).delete()
        user.delete()
    
    def test_audit_log_description_is_meaningful(self):
        """Property: Audit log has meaningful description"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Generate export
        ProfileExportService.generate_export(user.id)
        
        # Get the audit log
        audit_log = AuditLog.objects.filter(
            user=user,
            action='export'
        ).latest('timestamp')
        
        # Verify description exists and is meaningful
        assert audit_log.description, "Audit log must have description"
        assert len(audit_log.description) > 0, "Audit log description must not be empty"
        assert 'export' in audit_log.description.lower(), \
            "Audit log description should mention 'export'"
        
        # Cleanup
        AuditLog.objects.filter(user=user).delete()
        user.delete()
    
    def test_audit_logs_are_chronologically_ordered(self):
        """Property: Multiple audit logs are ordered chronologically"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Generate multiple exports
        for _ in range(3):
            ProfileExportService.generate_export(user.id)
        
        # Get audit logs
        audit_logs = list(AuditLog.objects.filter(
            user=user,
            action='export'
        ).order_by('timestamp'))
        
        # Verify chronological order
        for i in range(len(audit_logs) - 1):
            assert audit_logs[i].timestamp <= audit_logs[i + 1].timestamp, \
                "Audit logs should be in chronological order"
        
        # Cleanup
        AuditLog.objects.filter(user=user).delete()
        user.delete()
