"""
Session management views: list active sessions, force logout.
"""
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone


@login_required
def session_list(request):
    """List all active sessions for the current user."""
    sessions = []
    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(request.user.pk):
            sessions.append({
                'session_key': session.session_key[-12:],
                'created': data.get('_session_created', ''),
                'last_activity': data.get('_last_activity', ''),
                'ip_address': data.get('ip_address', 'Unknown'),
                'user_agent': data.get('user_agent', 'Unknown'),
                'expires_at': session.expire_date.isoformat(),
            })
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'sessions': sessions})
    from django.shortcuts import render
    return render(request, 'accounts/session_list.html', {'sessions': sessions})


@login_required
def logout_all_sessions(request):
    """Force logout from all sessions except current."""
    current_key = request.session.session_key
    count = 0
    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(request.user.pk) and session.session_key != current_key:
            session.delete()
            count += 1
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'deleted': count})
    return redirect('accounts:session_list')


@login_required
def logout_session(request, session_key):
    """Force logout a specific session."""
    try:
        session = Session.objects.get(session_key=session_key, expire_date__gte=timezone.now())
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(request.user.pk):
            session.delete()
    except Session.DoesNotExist:
        pass
    return redirect('accounts:session_list')
