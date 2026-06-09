from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit
from django_otp import devices_for_user as user_devices
from django_otp.plugins.otp_totp.models import TOTPDevice
from .models import OrganizerApplication
from .services import (
    send_organizer_application_confirmation,
    notify_admins_new_application,
)
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64


def _organizer_gate_checks(request):
    """Run gate checks for organizer applications. Returns error dict or None."""
    user = request.user
    if not user.is_authenticated:
        return {'error': 'login_required'}
    if user.can_organize_tournaments():
        return {'error': 'already_organizer'}
    if not user.is_verified:
        return {'error': 'not_verified'}
    if user.is_minor:
        return {'error': 'minor'}
    if user.account_locked:
        return {'error': 'account_locked'}
    if OrganizerApplication.objects.filter(user=user, status='pending').exists():
        return {'error': 'pending_exists'}
    return None
    if user.is_minor:
        return {'error': 'minor'}
    if user.account_locked:
        return {'error': 'account_locked'}
    if OrganizerApplication.objects.filter(user=user, status='pending').exists():
        return {'error': 'pending_exists'}
    return None


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def become_organizer(request):
    """
    Organizer application page with gate checks and admin review.
    Users submit an application which must be approved by an admin.
    Rate-limited: 10 POST requests per minute per IP.
    """
    user = request.user

    # Check if user is already an organizer
    if user.is_authenticated and user.can_organize_tournaments():
        messages.info(request, 'You are already an organizer.')
        return redirect('dashboard:home')

    # Gate checks
    gate_result = _organizer_gate_checks(request)
    if gate_result and gate_result['error'] == 'already_organizer':
        return redirect('dashboard:home')
    if gate_result and gate_result['error'] == 'pending_exists':
        messages.info(request, 'You already have a pending organizer application.')
        return redirect('accounts:organizer_status')

    if request.method == 'POST' and user.is_authenticated:
        gate_result = _organizer_gate_checks(request)
        if gate_result:
            if gate_result['error'] == 'not_verified':
                messages.error(request, 'Please verify your email address before applying.')
            elif gate_result['error'] == 'minor':
                messages.error(request, 'Organizer accounts require you to be 18 or older.')
            elif gate_result['error'] == 'account_locked':
                messages.error(request, 'Your account is locked. Please contact support.')
            return render(request, 'accounts/become_organizer.html', {
                'form_data': request.POST,
            })

        full_name = request.POST.get('full_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        country = request.POST.get('country', '').strip()
        reason = request.POST.get('reason', '').strip()
        experience = request.POST.get('experience', '').strip()
        agreed_to_terms = request.POST.get('agreed_to_terms') == 'on'

        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not phone_number:
            errors.append('Phone number is required.')
        if not country:
            errors.append('Country is required.')
        if not reason:
            errors.append('Please tell us why you want to become an organizer.')
        if not agreed_to_terms:
            errors.append('You must agree to the terms and conditions.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'accounts/become_organizer.html', {
                'form_data': request.POST,
            })

        application = OrganizerApplication.objects.create(
            user=user,
            full_name=full_name,
            phone_number=phone_number,
            country=country,
            reason=reason,
            experience=experience,
            agreed_to_terms=agreed_to_terms,
        )

        send_organizer_application_confirmation(user, application)
        notify_admins_new_application(application)

        from security.utils import log_audit_action
        log_audit_action(
            user=user,
            action='organizer_application',
            description=f'Submitted organizer application',
            severity='low',
            content_object=application,
            request=request,
        )

        messages.success(
            request,
            'Your organizer application has been submitted! Our team will review it within 2 business days.'
        )
        return redirect('accounts:organizer_status')

    # Show gate errors for GET requests too (e.g. not verified)
    gate_errors = {}
    if user.is_authenticated:
        gate_result = _organizer_gate_checks(request)
        if gate_result:
            gate_errors = gate_result

    context = {
        'gate_errors': gate_errors,
    }
    return render(request, 'accounts/become_organizer.html', context)


@login_required
def organizer_status(request):
    """Show the status of the user's organizer application(s)."""
    applications = OrganizerApplication.objects.filter(user=request.user)
    latest = applications.first()

    context = {
        'applications': applications,
        'latest': latest,
    }
    return render(request, 'accounts/organizer_status.html', context)


@login_required
def two_factor_setup(request):
    """Enable or disable TOTP two-factor authentication."""
    existing_device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'disable' and existing_device:
            existing_device.delete()
            messages.success(request, 'Two-factor authentication has been disabled.')
            return redirect('accounts:two_factor_setup')

        if action == 'enable':
            # Create a new TOTP device (confirmed after user verifies)
            device = TOTPDevice.objects.create(
                user=request.user,
                name=f"{request.user.username}@eytgaming",
                confirmed=False,
                tolerance=1,
            )
            return redirect('accounts:two_factor_verify', device_id=str(device.id))

        if action == 'verify':
            device_id = request.POST.get('device_id')
            code = request.POST.get('code', '')
            device = TOTPDevice.objects.filter(id=device_id, user=request.user, confirmed=False).first()

            if device and device.verify_token(code):
                device.confirmed = True
                device.save()
                messages.success(request, 'Two-factor authentication has been enabled successfully!')
                return redirect('accounts:two_factor_setup')
            else:
                messages.error(request, 'Invalid verification code. Please try again.')
                return redirect('accounts:two_factor_verify', device_id=device_id)

    context = {
        'has_2fa': existing_device is not None,
        'device': existing_device,
    }
    return render(request, 'accounts/two_factor_setup.html', context)


@login_required
def two_factor_dismiss(request):
    """Dismiss the 2FA nag banner for the current session."""
    if request.method == 'POST':
        request.session['two_factor_nag_dismissed'] = True
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:home'))


@login_required
def two_factor_verify(request, device_id):
    """Show QR code and verify TOTP setup."""
    device = TOTPDevice.objects.filter(id=device_id, user=request.user).first()

    if not device:
        messages.error(request, 'Device not found.')
        return redirect('accounts:two_factor_setup')

    if device.confirmed:
        messages.info(request, 'This device is already confirmed.')
        return redirect('accounts:two_factor_setup')

    # Generate QR code
    qr_data = device.config_url
    qr_img = qrcode.make(qr_data, image_factory=qrcode.image.svg.SvgImage)
    buf = BytesIO()
    qr_img.save(buf)
    qr_svg = base64.b64encode(buf.getvalue()).decode()

    context = {
        'device': device,
        'qr_svg': qr_svg,
        'qr_data': qr_data,
    }
    return render(request, 'accounts/two_factor_verify.html', context)
