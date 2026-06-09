"""
Tests for the security app: models, utility functions, and middleware.
"""
import json
import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.utils import timezone

from security.models import AuditLog, SecurityEvent
from security.utils import (
    get_client_ip, get_user_agent, log_audit_action, log_security_event,
    check_suspicious_activity, is_ip_blocked, sanitize_input,
    SecurityDecorator, audit_action, log_view_access, log_data_modification,
)
from security.middleware import SecurityHeadersMiddleware, AuditLogMiddleware

User = get_user_model()


class TestAuditLogModel:
    def test_create_audit_log(self, player_user):
        log = AuditLog.objects.create(
            user=player_user,
            action='login',
            description='User logged in',
            severity='low',
        )
        assert log.action == 'login'
        assert log.severity == 'low'

    def test_audit_log_str(self, player_user):
        log = AuditLog.objects.create(
            user=player_user, action='login',
            description='Login success',
        )
        expected = f'{player_user.email} - login - {log.timestamp}'
        assert str(log) == expected

    def test_audit_log_no_user(self):
        log = AuditLog.objects.create(
            action='failed_login',
            description='Failed login attempt',
            severity='medium',
        )
        assert log.user is None
        assert 'failed_login' in str(log)

    def test_audit_log_with_metadata(self, player_user):
        log = AuditLog.objects.create(
            user=player_user, action='payment',
            description='Payment processed',
            details={'amount': 99.99, 'currency': 'USD'},
        )
        assert log.details['amount'] == 99.99


class TestSecurityEventModel:
    def test_create_security_event(self):
        event = SecurityEvent.objects.create(
            event_type='failed_login',
            description='Failed login from unknown IP',
        )
        assert not event.resolved
        assert event.event_type == 'failed_login'

    def test_security_event_str(self):
        event = SecurityEvent.objects.create(
            event_type='suspicious_activity',
            description='Multiple rapid requests',
        )
        expected = f'suspicious_activity - {event.created_at}'
        assert str(event) == expected

    def test_resolve_event(self, player_user):
        event = SecurityEvent.objects.create(
            event_type='account_locked', description='Manual lock',
            user=player_user,
        )
        event.resolved = True
        event.resolved_at = timezone.now()
        event.resolved_by = player_user
        event.save()
        db_event = SecurityEvent.objects.get(pk=event.pk)
        assert db_event.resolved
        assert db_event.resolved_by == player_user

    def test_event_with_ip(self):
        event = SecurityEvent.objects.create(
            event_type='rate_limit_exceeded',
            description='Rate limit hit',
            ip_address='192.168.1.1',
        )
        assert str(event.ip_address) == '192.168.1.1'


class TestGetClientIP:
    def test_x_forwarded_for(self):
        request = HttpRequest()
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1, 10.0.0.1'
        assert get_client_ip(request) == '203.0.113.1'

    def test_remote_addr(self):
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        assert get_client_ip(request) == '192.168.1.100'

    def test_no_ip(self):
        request = HttpRequest()
        assert get_client_ip(request) == '0.0.0.0'


class TestGetUserAgent:
    def test_with_agent(self):
        request = HttpRequest()
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 Test'
        assert get_user_agent(request) == 'Mozilla/5.0 Test'

    def test_no_agent(self):
        request = HttpRequest()
        assert get_user_agent(request) == ''


class TestLogAuditAction:
    @pytest.mark.django_db
    def test_logs_audit_entry(self, player_user):
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'TestAgent'
        request.path = '/test/'
        request.method = 'POST'

        result = log_audit_action(
            user=player_user, action='create',
            description='Created a test entry',
            request=request,
        )
        assert result is not None
        assert result.user == player_user
        assert result.ip_address == '10.0.0.1'

    @pytest.mark.django_db
    def test_logs_without_request(self, player_user):
        result = log_audit_action(
            user=player_user, action='export',
            description='Data export',
            severity='medium',
        )
        assert result is not None
        assert result.user == player_user

    @pytest.mark.django_db
    def test_logs_with_content_object(self, player_user):
        result = log_audit_action(
            user=player_user, action='update',
            description='Updated profile',
            content_object=player_user,
        )
        assert result is not None
        assert result.model_name == 'user'


class TestLogSecurityEvent:
    @pytest.mark.django_db
    def test_logs_event(self, player_user):
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '10.0.0.5'

        result = log_security_event(
            event_type='failed_login',
            description='Login attempt failed',
            user=player_user, request=request,
        )
        assert result is not None
        assert result.user == player_user
        assert str(result.ip_address) == '10.0.0.5'

    @pytest.mark.django_db
    def test_logs_with_metadata(self):
        result = log_security_event(
            event_type='suspicious_activity',
            description='Unusual pattern detected',
            metadata={'attempt_count': 5, 'window_minutes': 10},
        )
        assert result is not None
        assert result.metadata['attempt_count'] == 5


class TestCheckSuspiciousActivity:
    @pytest.mark.django_db
    def test_no_prior_activity(self):
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        result = check_suspicious_activity(request)
        assert not result

    @pytest.mark.django_db
    def test_multiple_security_events_triggers(self, player_user):
        for i in range(6):
            SecurityEvent.objects.create(
                event_type='failed_login',
                description=f'Attempt {i}',
                user=player_user,
                ip_address='10.0.0.1',
                created_at=timezone.now() - timedelta(minutes=i),
            )
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        result = check_suspicious_activity(request)
        assert result


class TestIsIPBlocked:
    def test_non_blocked_ip(self):
        assert not is_ip_blocked('10.0.0.1')

    def test_blocked_ip(self):
        SecurityEvent.objects.create(
            event_type='unauthorized_access',
            description='Blocked IP test',
            ip_address='203.0.113.99',
            resolved=False,
        )
        assert is_ip_blocked('203.0.113.99')

    def test_resolved_ip_no_longer_blocked(self, player_user):
        event = SecurityEvent.objects.create(
            event_type='unauthorized_access',
            description='Was blocked',
            ip_address='203.0.113.50',
        )
        event.resolved = True
        event.resolved_at = timezone.now()
        event.resolved_by = player_user
        event.save()
        assert not is_ip_blocked('203.0.113.50')


class TestSanitizeInput:
    def test_removes_html_tags(self):
        assert sanitize_input('<script>alert("xss")</script>') == 'alert("xss")'

    def test_preserves_safe_text(self):
        assert sanitize_input('Hello, World!') == 'Hello, World!'

    def test_handles_empty_string(self):
        assert sanitize_input('') == ''

    def test_removes_multiple_tags(self):
        result = sanitize_input('<p>Hello</p><b>World</b>')
        assert 'Hello' in result
        assert 'World' in result
        assert '<p>' not in result
        assert '<b>' not in result


class TestSecurityDecorator:
    def test_audit_action_decorator(self):
        @audit_action(action='test_action', severity='low')
        def my_view(request):
            return 'done'
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '1.2.3.4'
        result = my_view(request)
        assert result == 'done'

    @pytest.mark.django_db
    def test_log_view_access_decorator(self, player_user):
        @log_view_access
        def my_view(request):
            return 'accessed'
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '1.2.3.4'
        request.META['REQUEST_METHOD'] = 'GET'
        request.user = player_user
        result = my_view(request)
        assert result == 'accessed'

    @pytest.mark.django_db
    def test_log_data_modification_decorator(self, player_user):
        @log_data_modification
        def my_view(request):
            return 'modified'
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '1.2.3.4'
        request.META['REQUEST_METHOD'] = 'POST'
        request.user = player_user
        result = my_view(request)
        assert result == 'modified'


class TestSecurityMiddleware:
    def test_security_headers_middleware(self):
        middleware = SecurityHeadersMiddleware(get_response=lambda r: None)
        request = HttpRequest()
        assert middleware is not None

    def test_audit_log_middleware(self):
        middleware = AuditLogMiddleware(get_response=lambda r: None)
        request = HttpRequest()
        assert middleware is not None

    @pytest.mark.django_db
    def test_audit_log_middleware_logs_post(self, player_user):
        called = []
        def get_response(request):
            called.append(True)
            from django.http import HttpResponse
            return HttpResponse('ok')

        middleware = AuditLogMiddleware(get_response=get_response)
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        request.META['REQUEST_METHOD'] = 'POST'
        request.META['PATH_INFO'] = '/test/'
        request.user = player_user
        from django.http import HttpResponse
        response = middleware(request)
        assert response.status_code == 200
