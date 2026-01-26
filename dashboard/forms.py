"""
Forms for dashboard and profile management
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from core.models import UserGameProfile, Game
from dashboard.models import UserReport
from notifications.models import NotificationPreference
from datetime import date

User = get_user_model()


# ============================================================================
# Profile Forms (Task 25.1)
# ============================================================================

class ProfileEditForm(forms.ModelForm):
    """
    Form for editing user profile information
    Requirements: 2.2, 2.3, 4.1
    """
    
    # Define timezone choices
    TIMEZONE_CHOICES = [
        ('UTC', 'UTC'),
        ('US/Eastern', 'Eastern Time (US & Canada)'),
        ('US/Central', 'Central Time (US & Canada)'),
        ('US/Mountain', 'Mountain Time (US & Canada)'),
        ('US/Pacific', 'Pacific Time (US & Canada)'),
        ('Europe/London', 'London'),
        ('Europe/Paris', 'Paris'),
        ('Europe/Berlin', 'Berlin'),
        ('Europe/Rome', 'Rome'),
        ('Europe/Madrid', 'Madrid'),
        ('Asia/Tokyo', 'Tokyo'),
        ('Asia/Shanghai', 'Shanghai'),
        ('Asia/Seoul', 'Seoul'),
        ('Asia/Kolkata', 'Mumbai'),
        ('Australia/Sydney', 'Sydney'),
        ('Australia/Melbourne', 'Melbourne'),
    ]
    
    # Define country choices
    COUNTRY_CHOICES = [
        ('', 'Select Country'),
        ('US', 'United States'),
        ('CA', 'Canada'),
        ('GB', 'United Kingdom'),
        ('DE', 'Germany'),
        ('FR', 'France'),
        ('IT', 'Italy'),
        ('ES', 'Spain'),
        ('NL', 'Netherlands'),
        ('SE', 'Sweden'),
        ('NO', 'Norway'),
        ('DK', 'Denmark'),
        ('FI', 'Finland'),
        ('AU', 'Australia'),
        ('NZ', 'New Zealand'),
        ('JP', 'Japan'),
        ('KR', 'South Korea'),
        ('CN', 'China'),
        ('IN', 'India'),
        ('BR', 'Brazil'),
        ('MX', 'Mexico'),
        ('AR', 'Argentina'),
        ('CL', 'Chile'),
        ('ZA', 'South Africa'),
        ('NG', 'Nigeria'),
        ('EG', 'Egypt'),
        ('RU', 'Russia'),
        ('PL', 'Poland'),
        ('CZ', 'Czech Republic'),
        ('HU', 'Hungary'),
        ('GR', 'Greece'),
        ('TR', 'Turkey'),
        ('IL', 'Israel'),
        ('AE', 'United Arab Emirates'),
        ('SA', 'Saudi Arabia'),
        ('SG', 'Singapore'),
        ('MY', 'Malaysia'),
        ('TH', 'Thailand'),
        ('PH', 'Philippines'),
        ('ID', 'Indonesia'),
        ('VN', 'Vietnam'),
    ]
    
    # Override timezone and country fields to be choice fields
    timezone = forms.ChoiceField(
        choices=TIMEZONE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all'
        })
    )
    
    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all'
        })
    )
    
    class Meta:
        model = User
        fields = [
            'avatar',
            'first_name',
            'last_name',
            'display_name',
            'bio',
            'date_of_birth',
            'timezone',
            'country',
            'city',
            'phone_number',
            'discord_username',
            'steam_id',
            'twitch_username',
        ]
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all',
                'accept': 'image/jpeg,image/png,image/gif'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all',
                'placeholder': 'Last Name'
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all',
                'placeholder': 'Display Name'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all',
                'placeholder': 'Tell us about yourself...',
                'rows': 4,
                'maxlength': 500
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all',
                'type': 'date'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all',
                'placeholder': 'City'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all',
                'placeholder': '+1234567890'
            }),
            'discord_username': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all',
                'placeholder': 'username#1234'
            }),
            'steam_id': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all',
                'placeholder': 'Steam ID'
            }),
            'twitch_username': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all',
                'placeholder': 'Twitch Username'
            }),
        }
    
    def clean_bio(self):
        """Validate bio length"""
        bio = self.cleaned_data.get('bio', '')
        if len(bio) > 500:
            raise ValidationError('Bio must be 500 characters or less.')
        return bio
    
    def clean_date_of_birth(self):
        """Validate date of birth"""
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            if dob >= today:
                raise ValidationError('Date of birth must be in the past.')
            
            # Calculate age
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 13:
                raise ValidationError('You must be at least 13 years old to use this platform.')
        
        return dob
    
    def clean_display_name(self):
        """Validate display name"""
        display_name = self.cleaned_data.get('display_name', '')
        if display_name and len(display_name) < 3:
            raise ValidationError('Display name must be at least 3 characters.')
        return display_name


class AvatarUploadForm(forms.Form):
    """
    Form for uploading avatar images
    Requirements: 2.3
    """
    avatar = forms.ImageField(
        required=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/gif'
        })
    )
    
    def clean_avatar(self):
        """Validate avatar file size and type"""
        avatar = self.cleaned_data.get('avatar')
        
        if avatar:
            # Check file size (2MB limit)
            if avatar.size > 2 * 1024 * 1024:
                raise ValidationError('Avatar must be under 2MB.')
            
            # Check file type
            if not avatar.content_type.startswith('image/'):
                raise ValidationError('File must be an image.')
            
            # Check specific image types
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if avatar.content_type not in allowed_types:
                raise ValidationError('Image must be JPG, PNG, or GIF.')
        
        return avatar


class BannerUploadForm(forms.Form):
    """
    Form for uploading banner images
    Requirements: 2.3
    """
    banner = forms.ImageField(
        required=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/gif'
        })
    )
    
    def clean_banner(self):
        """Validate banner file size and type"""
        banner = self.cleaned_data.get('banner')
        
        if banner:
            # Check file size (5MB limit)
            if banner.size > 5 * 1024 * 1024:
                raise ValidationError('Banner must be under 5MB.')
            
            # Check file type
            if not banner.content_type.startswith('image/'):
                raise ValidationError('File must be an image.')
            
            # Check specific image types
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if banner.content_type not in allowed_types:
                raise ValidationError('Image must be JPG, PNG, or GIF.')
        
        return banner


class GameProfileForm(forms.ModelForm):
    """
    Form for creating/editing game profiles
    Requirements: 4.1
    """
    
    class Meta:
        model = UserGameProfile
        fields = [
            'game',
            'in_game_name',
            'skill_rating',
            'rank',
            'preferred_role',
            'is_main_game',
        ]
        widgets = {
            'game': forms.Select(attrs={
                'class': 'form-control'
            }),
            'in_game_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your in-game name'
            }),
            'skill_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1000',
                'min': 0,
                'max': 5000
            }),
            'rank': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Gold, Diamond, etc.'
            }),
            'preferred_role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Support, Tank, DPS'
            }),
            'is_main_game': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show active games
        self.fields['game'].queryset = Game.objects.filter(is_active=True)
    
    def clean_skill_rating(self):
        """Validate skill rating"""
        skill_rating = self.cleaned_data.get('skill_rating')
        if skill_rating is not None:
            if skill_rating < 0:
                raise ValidationError('Skill rating cannot be negative.')
            if skill_rating > 5000:
                raise ValidationError('Skill rating cannot exceed 5000.')
        return skill_rating
    
    def clean(self):
        """Validate game profile"""
        cleaned_data = super().clean()
        game = cleaned_data.get('game')
        
        # Check for duplicate game profile
        if self.user and game:
            existing = UserGameProfile.objects.filter(
                user=self.user,
                game=game
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise ValidationError('You already have a profile for this game.')
        
        return cleaned_data


# ============================================================================
# Settings Forms (Task 25.2)
# ============================================================================

class PrivacySettingsForm(forms.Form):
    """
    Form for managing privacy settings
    Requirements: 9.2
    """
    private_profile = forms.BooleanField(
        required=False,
        label='Private Profile',
        help_text='Hide your profile from non-friends',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    online_status_visible = forms.BooleanField(
        required=False,
        label='Show Online Status',
        help_text='Let others see when you are online',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    activity_visible = forms.BooleanField(
        required=False,
        label='Show Activity Feed',
        help_text='Let others see your recent activity',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    statistics_visible = forms.BooleanField(
        required=False,
        label='Show Statistics',
        help_text='Let others see your gaming statistics',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-populate with current user settings
        if self.user:
            self.fields['private_profile'].initial = self.user.private_profile
            self.fields['online_status_visible'].initial = self.user.online_status_visible
            self.fields['activity_visible'].initial = self.user.activity_visible
            self.fields['statistics_visible'].initial = self.user.statistics_visible


class NotificationPreferencesForm(forms.ModelForm):
    """
    Form for managing notification preferences
    Integrates with notifications.models.NotificationPreference
    Requirements: 9.3
    """
    
    class Meta:
        model = NotificationPreference
        fields = [
            'in_app_enabled',
            'email_enabled',
            'email_tournament_updates',
            'email_coaching_reminders',
            'email_team_activity',
            'email_payment_receipts',
            'email_security_alerts',
            'email_marketing',
            'push_enabled',
            'push_tournament_updates',
            'push_coaching_reminders',
            'push_team_activity',
            'push_match_updates',
            'quiet_hours_enabled',
            'quiet_hours_start',
            'quiet_hours_end',
        ]
        widgets = {
            'in_app_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_tournament_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_coaching_reminders': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_team_activity': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_payment_receipts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_security_alerts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_marketing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_tournament_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_coaching_reminders': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_team_activity': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_match_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'quiet_hours_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'quiet_hours_start': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'quiet_hours_end': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
        }
        labels = {
            'in_app_enabled': 'Enable In-App Notifications',
            'email_enabled': 'Enable Email Notifications',
            'email_tournament_updates': 'Tournament Updates',
            'email_coaching_reminders': 'Coaching Reminders',
            'email_team_activity': 'Team Activity',
            'email_payment_receipts': 'Payment Receipts',
            'email_security_alerts': 'Security Alerts',
            'email_marketing': 'Marketing & Promotions',
            'push_enabled': 'Enable Push Notifications',
            'push_tournament_updates': 'Tournament Updates',
            'push_coaching_reminders': 'Coaching Reminders',
            'push_team_activity': 'Team Activity',
            'push_match_updates': 'Match Updates',
            'quiet_hours_enabled': 'Enable Quiet Hours',
            'quiet_hours_start': 'Quiet Hours Start',
            'quiet_hours_end': 'Quiet Hours End',
        }
    
    def clean(self):
        """Validate quiet hours"""
        cleaned_data = super().clean()
        quiet_hours_enabled = cleaned_data.get('quiet_hours_enabled')
        quiet_hours_start = cleaned_data.get('quiet_hours_start')
        quiet_hours_end = cleaned_data.get('quiet_hours_end')
        
        if quiet_hours_enabled:
            if not quiet_hours_start or not quiet_hours_end:
                raise ValidationError(
                    'Both start and end times are required when quiet hours are enabled.'
                )
        
        return cleaned_data


class ConnectedAccountsForm(forms.Form):
    """
    Form for displaying connected accounts (display only, no inputs)
    Requirements: 9.5
    """
    # This form is display-only and doesn't have any input fields
    # It's used to structure the template display of connected accounts
    pass


class AccountDeleteForm(forms.Form):
    """
    Form for account deletion with password confirmation
    Requirements: 18.2
    """
    password = forms.CharField(
        required=True,
        label='Confirm Password',
        help_text='Enter your password to confirm account deletion',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    
    confirm_text = forms.CharField(
        required=True,
        label='Type "DELETE" to confirm',
        help_text='Type DELETE in all caps to confirm account deletion',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Type DELETE to confirm'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_password(self):
        """Verify password is correct"""
        password = self.cleaned_data.get('password')
        
        if self.user and not self.user.check_password(password):
            raise ValidationError('Incorrect password.')
        
        return password
    
    def clean_confirm_text(self):
        """Verify confirmation text is exactly 'DELETE'"""
        confirm_text = self.cleaned_data.get('confirm_text')
        
        if confirm_text != 'DELETE':
            raise ValidationError('You must type "DELETE" exactly to confirm account deletion.')
        
        return confirm_text


# ============================================================================
# Social Interaction Forms (Task 25.3)
# ============================================================================

class UserReportForm(forms.ModelForm):
    """
    Form for reporting users
    Requirements: 10.3
    """
    
    class Meta:
        model = UserReport
        fields = ['category', 'description']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Please provide details about why you are reporting this user...',
                'rows': 5,
                'maxlength': 1000
            }),
        }
        labels = {
            'category': 'Report Category',
            'description': 'Description',
        }
    
    def __init__(self, *args, **kwargs):
        self.reporter = kwargs.pop('reporter', None)
        self.reported_user = kwargs.pop('reported_user', None)
        super().__init__(*args, **kwargs)
    
    def clean_description(self):
        """Validate description"""
        description = self.cleaned_data.get('description', '')
        
        if not description or len(description.strip()) == 0:
            raise ValidationError('Description cannot be empty.')
        
        if len(description) > 1000:
            raise ValidationError('Description must be 1000 characters or less.')
        
        return description
    
    def clean(self):
        """Validate report submission"""
        cleaned_data = super().clean()
        
        # Ensure reporter and reported_user are different
        if self.reporter and self.reported_user:
            if self.reporter.id == self.reported_user.id:
                raise ValidationError('You cannot report yourself.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save report with reporter and reported_user"""
        instance = super().save(commit=False)
        
        if self.reporter:
            instance.reporter = self.reporter
        if self.reported_user:
            instance.reported_user = self.reported_user
        
        if commit:
            instance.save()
        
        return instance
