from django.db import models
from django.conf import settings
import uuid


class Sponsor(models.Model):
    """Company or brand that sponsors celebrities."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    logo = models.ImageField(upload_to='sponsors/logos/', null=True, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sponsors'
        ordering = ['name']
        verbose_name = 'Sponsor'
        verbose_name_plural = 'Sponsors'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class SponsorshipDeal(models.Model):
    """A sponsorship agreement between a sponsor and a celebrity."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sponsor = models.ForeignKey(Sponsor, on_delete=models.CASCADE, related_name='deals')
    celebrity = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='sponsorship_deals',
        limit_choices_to={'is_verified_personality': True},
    )

    title = models.CharField(max_length=200, help_text="Deal name/title")
    description = models.TextField(blank=True)

    budget = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total deal value in USD")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    terms = models.TextField(blank=True, help_text="Specific terms and deliverables")
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sponsorship_deals'
        ordering = ['-created_at']
        verbose_name = 'Sponsorship Deal'
        verbose_name_plural = 'Sponsorship Deals'
        indexes = [
            models.Index(fields=['celebrity', 'status']),
            models.Index(fields=['sponsor', 'status']),
        ]

    def __str__(self):
        return f"{self.sponsor.name} × {self.celebrity.get_display_name()} — {self.get_status_display()}"
