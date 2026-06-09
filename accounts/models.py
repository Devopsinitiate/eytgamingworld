from django.db import models
from django.conf import settings


class OrganizerApplication(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organizer_applications',
    )
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=30)
    country = models.CharField(max_length=100)
    reason = models.TextField(help_text="Why do you want to become an organizer?")
    experience = models.TextField(blank=True, help_text="Previous tournament or event organization experience")
    agreed_to_terms = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_applications',
    )
    admin_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True, help_text="Reason shown to the user if rejected")

    class Meta:
        db_table = 'organizer_applications'
        verbose_name = 'Organizer Application'
        verbose_name_plural = 'Organizer Applications'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.get_status_display()})"
