"""Service layer for the accounts app."""
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


def send_organizer_application_confirmation(user, application):
    """Send confirmation email when an organizer application is submitted."""
    subject = 'Organizer Application Received — EYTGaming'
    message = (
        f"Hi {application.full_name},\n\n"
        f"Thank you for applying to become a tournament organizer on EYTGaming!\n\n"
        f"We've received your application and it's now under review. "
        f"Our team typically responds within 2 business days.\n\n"
        f"You can check your application status anytime:\n"
        f"{settings.SITE_URL}{reverse('accounts:organizer_status')}\n\n"
        f"Application Details:\n"
        f"- Full Name: {application.full_name}\n"
        f"- Country: {application.country}\n"
        f"- Submitted: {application.submitted_at.strftime('%B %d, %Y')}\n\n"
        f"If you have any questions, reply to this email.\n\n"
        f"Best,\n"
        f"The EYTGaming Team"
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception as e:
        logger.error(f"Failed to send organizer application confirmation: {e}")


def send_organizer_approved(user, application):
    """Send notification when an organizer application is approved."""
    subject = 'You\'re Now an Organizer — EYTGaming'
    message = (
        f"Hi {application.full_name},\n\n"
        f"Great news! Your organizer application has been approved.\n\n"
        f"You can now create and manage tournaments on EYTGaming.\n\n"
        f"Get started:\n"
        f"- Create your first tournament: {settings.SITE_URL}{reverse('tournaments:create')}\n"
        f"- Set up two-factor auth: {settings.SITE_URL}{reverse('accounts:two_factor_setup')}\n\n"
        f"Please make sure to:\n"
        f"1. Complete your profile\n"
        f"2. Set up two-factor authentication for account security\n"
        f"3. Review the organizer guidelines\n\n"
        f"Welcome to the team!\n"
        f"The EYTGaming Team"
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception as e:
        logger.error(f"Failed to send organizer approved email: {e}")


def send_organizer_rejected(user, application):
    """Send notification when an organizer application is rejected."""
    reason = application.rejection_reason or "Your application did not meet our requirements at this time."
    subject = 'Organizer Application Update — EYTGaming'
    message = (
        f"Hi {application.full_name},\n\n"
        f"Thank you for your interest in becoming an EYTGaming organizer.\n\n"
        f"After reviewing your application, we're unable to approve it at this time.\n\n"
        f"Reason: {reason}\n\n"
        f"You may submit a new application after 30 days. "
        f"In the meantime, feel free to participate in the community as a player.\n\n"
        f"Best,\n"
        f"The EYTGaming Team"
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception as e:
        logger.error(f"Failed to send organizer rejected email: {e}")


def notify_admins_new_application(application):
    """Notify site admins about a new organizer application (log-based)."""
    logger.info(
        f"New organizer application from {application.full_name} "
        f"({application.user.email}) — review at admin panel"
    )
