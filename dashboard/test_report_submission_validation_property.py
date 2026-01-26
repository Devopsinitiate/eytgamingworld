"""
Property-based tests for report submission validation functionality.

This module tests the report submission validation property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from core.models import User
from dashboard.models import UserReport
from dashboard.forms import UserReportForm
import uuid


@pytest.mark.django_db
class TestReportSubmissionValidation:
    """
    **Feature: user-profile-dashboard, Property 33: Report submission validation**
    
    For any user report submission, the reporter and reported user must be different users,
    and the description must not be empty.
    
    **Validates: Requirements 10.3**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        category=st.sampled_from([
            'inappropriate_content',
            'harassment', 
            'spam',
            'cheating',
            'other'
        ]),
        description=st.text(
            min_size=1, 
            max_size=1000,
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))  # Exclude control characters
        ).filter(lambda x: x.strip() and '\x00' not in x)  # Exclude NUL characters and empty strings
    )
    def test_valid_report_submission_succeeds(self, category, description):
        """Property: Valid report submissions with different users and non-empty description succeed"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create reporter and reported user (different users)
        reporter = User.objects.create_user(
            email=f'reporter_{unique_id}@example.com',
            username=f'reporter_{unique_id}',
            password='testpass123'
        )
        
        reported_user = User.objects.create_user(
            email=f'reported_{unique_id}@example.com',
            username=f'reported_{unique_id}',
            password='testpass123'
        )
        
        # Create form with valid data
        form_data = {
            'category': category,
            'description': description
        }
        
        form = UserReportForm(
            data=form_data,
            reporter=reporter,
            reported_user=reported_user
        )
        
        # Form should be valid
        assert form.is_valid(), f"Form should be valid with different users and non-empty description. Errors: {form.errors}"
        
        # Save the report
        report = form.save(commit=False)
        report.reporter = reporter
        report.reported_user = reported_user
        report.save()
        
        # Verify report was created correctly
        assert report.reporter == reporter
        assert report.reported_user == reported_user
        assert report.category == category
        # Note: Description might be stripped of leading/trailing whitespace by the form or model
        assert report.description.strip() == description.strip()
        assert report.status == 'pending'
        
        # Cleanup
        report.delete()
        reporter.delete()
        reported_user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        category=st.sampled_from([
            'inappropriate_content',
            'harassment', 
            'spam',
            'cheating',
            'other'
        ]),
        description=st.one_of(
            st.just(''),  # Empty string
            st.text(max_size=100).filter(lambda x: not x.strip())  # Whitespace only
        )
    )
    def test_empty_description_fails_validation(self, category, description):
        """Property: Report submissions with empty or whitespace-only descriptions fail validation"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create reporter and reported user (different users)
        reporter = User.objects.create_user(
            email=f'reporter_{unique_id}@example.com',
            username=f'reporter_{unique_id}',
            password='testpass123'
        )
        
        reported_user = User.objects.create_user(
            email=f'reported_{unique_id}@example.com',
            username=f'reported_{unique_id}',
            password='testpass123'
        )
        
        # Create form with empty/whitespace description
        form_data = {
            'category': category,
            'description': description
        }
        
        form = UserReportForm(
            data=form_data,
            reporter=reporter,
            reported_user=reported_user
        )
        
        # Form should be invalid due to empty description
        assert not form.is_valid(), "Form should be invalid with empty or whitespace-only description"
        assert 'description' in form.errors, "Description field should have validation errors"
        
        # Cleanup
        reporter.delete()
        reported_user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        category=st.sampled_from([
            'inappropriate_content',
            'harassment', 
            'spam',
            'cheating',
            'other'
        ]),
        description=st.text(
            min_size=1, 
            max_size=1000,
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))
        ).filter(lambda x: x.strip() and '\x00' not in x)
    )
    def test_same_user_report_fails_validation(self, category, description):
        """Property: Report submissions where reporter and reported user are the same fail validation"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create a single user (reporter and reported user are the same)
        user = User.objects.create_user(
            email=f'user_{unique_id}@example.com',
            username=f'user_{unique_id}',
            password='testpass123'
        )
        
        # Create form with same user as reporter and reported
        form_data = {
            'category': category,
            'description': description
        }
        
        form = UserReportForm(
            data=form_data,
            reporter=user,
            reported_user=user
        )
        
        # Form should be invalid due to same user
        assert not form.is_valid(), "Form should be invalid when reporter and reported user are the same"
        assert '__all__' in form.errors or 'non_field_errors' in form.errors, \
            "Form should have non-field errors for same user validation"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        description=st.text(min_size=1001, max_size=2000)  # Description too long
    )
    def test_description_too_long_fails_validation(self, description):
        """Property: Report submissions with descriptions longer than 1000 characters fail validation"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create reporter and reported user (different users)
        reporter = User.objects.create_user(
            email=f'reporter_{unique_id}@example.com',
            username=f'reporter_{unique_id}',
            password='testpass123'
        )
        
        reported_user = User.objects.create_user(
            email=f'reported_{unique_id}@example.com',
            username=f'reported_{unique_id}',
            password='testpass123'
        )
        
        # Create form with description that's too long
        form_data = {
            'category': 'other',
            'description': description
        }
        
        form = UserReportForm(
            data=form_data,
            reporter=reporter,
            reported_user=reported_user
        )
        
        # Form should be invalid due to description length
        assert not form.is_valid(), "Form should be invalid with description longer than 1000 characters"
        assert 'description' in form.errors, "Description field should have validation errors for length"
        
        # Cleanup
        reporter.delete()
        reported_user.delete()
    
    def test_report_model_constraints(self):
        """Property: UserReport model enforces basic constraints"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create reporter and reported user
        reporter = User.objects.create_user(
            email=f'reporter_{unique_id}@example.com',
            username=f'reporter_{unique_id}',
            password='testpass123'
        )
        
        reported_user = User.objects.create_user(
            email=f'reported_{unique_id}@example.com',
            username=f'reported_{unique_id}',
            password='testpass123'
        )
        
        # Create valid report
        report = UserReport.objects.create(
            reporter=reporter,
            reported_user=reported_user,
            category='harassment',
            description='This user was being inappropriate in chat.'
        )
        
        # Verify default values
        assert report.status == 'pending', "Default status should be 'pending'"
        assert report.reviewed_by is None, "reviewed_by should be None initially"
        assert report.reviewed_at is None, "reviewed_at should be None initially"
        assert report.resolution_notes == '', "resolution_notes should be empty initially"
        
        # Verify required fields are set
        assert report.reporter == reporter
        assert report.reported_user == reported_user
        assert report.category == 'harassment'
        assert report.description == 'This user was being inappropriate in chat.'
        
        # Verify timestamps are set
        assert report.created_at is not None
        assert report.updated_at is not None
        
        # Cleanup
        report.delete()
        reporter.delete()
        reported_user.delete()
    
    @settings(max_examples=30, deadline=None)
    @given(
        num_reports=st.integers(min_value=1, max_value=5),
        category=st.sampled_from([
            'inappropriate_content',
            'harassment', 
            'spam',
            'cheating',
            'other'
        ])
    )
    def test_multiple_reports_same_user_allowed(self, num_reports, category):
        """Property: Multiple reports against the same user are allowed"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create reported user
        reported_user = User.objects.create_user(
            email=f'reported_{unique_id}@example.com',
            username=f'reported_{unique_id}',
            password='testpass123'
        )
        
        # Create multiple reporters
        reporters = []
        reports = []
        
        for i in range(num_reports):
            reporter = User.objects.create_user(
                email=f'reporter{i}_{unique_id}@example.com',
                username=f'reporter{i}_{unique_id}',
                password='testpass123'
            )
            reporters.append(reporter)
            
            # Create report
            report = UserReport.objects.create(
                reporter=reporter,
                reported_user=reported_user,
                category=category,
                description=f'Report {i+1} against this user.'
            )
            reports.append(report)
        
        # Verify all reports were created
        assert len(reports) == num_reports, f"Should have created {num_reports} reports"
        
        # Verify all reports point to the same reported user
        for report in reports:
            assert report.reported_user == reported_user
            assert report.status == 'pending'
        
        # Verify different reporters
        reporter_ids = [report.reporter.id for report in reports]
        assert len(set(reporter_ids)) == num_reports, "All reports should have different reporters"
        
        # Cleanup
        for report in reports:
            report.delete()
        for reporter in reporters:
            reporter.delete()
        reported_user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        category=st.sampled_from([
            'inappropriate_content',
            'harassment', 
            'spam',
            'cheating',
            'other'
        ]),
        description=st.text(
            min_size=1, 
            max_size=1000,
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))
        ).filter(lambda x: x.strip() and '\x00' not in x),
        status=st.sampled_from(['pending', 'investigating', 'resolved', 'dismissed'])
    )
    def test_report_status_transitions(self, category, description, status):
        """Property: Report status can be updated to any valid status"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create reporter and reported user
        reporter = User.objects.create_user(
            email=f'reporter_{unique_id}@example.com',
            username=f'reporter_{unique_id}',
            password='testpass123'
        )
        
        reported_user = User.objects.create_user(
            email=f'reported_{unique_id}@example.com',
            username=f'reported_{unique_id}',
            password='testpass123'
        )
        
        # Create report with default status
        report = UserReport.objects.create(
            reporter=reporter,
            reported_user=reported_user,
            category=category,
            description=description
        )
        
        # Verify initial status
        assert report.status == 'pending'
        
        # Update status
        report.status = status
        report.save()
        
        # Verify status was updated
        report.refresh_from_db()
        assert report.status == status, f"Status should be updated to {status}"
        
        # Cleanup
        report.delete()
        reporter.delete()
        reported_user.delete()
    
    def test_report_string_representation(self):
        """Property: UserReport string representation is informative"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create reporter and reported user
        reporter = User.objects.create_user(
            email=f'reporter_{unique_id}@example.com',
            username=f'reporter_{unique_id}',
            display_name='Reporter User',
            password='testpass123'
        )
        
        reported_user = User.objects.create_user(
            email=f'reported_{unique_id}@example.com',
            username=f'reported_{unique_id}',
            display_name='Reported User',
            password='testpass123'
        )
        
        # Create report
        report = UserReport.objects.create(
            reporter=reporter,
            reported_user=reported_user,
            category='harassment',
            description='Test report description'
        )
        
        # Verify string representation
        str_repr = str(report)
        assert 'Report:' in str_repr
        assert 'Reported User' in str_repr or reported_user.username in str_repr
        assert 'Reporter User' in str_repr or reporter.username in str_repr
        assert 'Pending' in str_repr  # Status display
        
        # Cleanup
        report.delete()
        reporter.delete()
        reported_user.delete()