from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML
from .models import Tournament, Match, MatchDispute
from .security import TournamentSecurityValidator, sanitize_tournament_data


class TournamentForm(forms.ModelForm):
    """Form for creating/editing tournaments"""
    
    class Meta:
        model = Tournament
        fields = [
            'name', 'slug', 'description', 'rules', 'game', 'format',
            'tournament_type', 'is_team_based', 'min_participants',
            'max_participants', 'team_size', 'registration_start',
            'registration_end', 'requires_approval', 'registration_fee',
            'check_in_start', 'start_datetime', 'estimated_end',
            'prize_pool', 'prize_distribution', 'seeding_method',
            'best_of', 'banner', 'thumbnail', 'is_public', 'is_featured',
            'requires_verification', 'skill_requirement', 'stream_url',
            'discord_invite', 'venue'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'rules': forms.Textarea(attrs={'rows': 6}),
            'registration_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'registration_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'check_in_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'estimated_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'prize_distribution': forms.Textarea(attrs={'rows': 3, 
                'placeholder': '{"1st": 50, "2nd": 30, "3rd": 20}'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Basic Information',
                Row(
                    Column('name', css_class='col-md-8'),
                    Column('slug', css_class='col-md-4'),
                ),
                'description',
                'rules',
                Row(
                    Column('game', css_class='col-md-6'),
                    Column('format', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                'Configuration',
                Row(
                    Column('tournament_type', css_class='col-md-4'),
                    Column('is_team_based', css_class='col-md-4'),
                    Column('team_size', css_class='col-md-4'),
                ),
                Row(
                    Column('min_participants', css_class='col-md-6'),
                    Column('max_participants', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                'Registration',
                Row(
                    Column('registration_start', css_class='col-md-6'),
                    Column('registration_end', css_class='col-md-6'),
                ),
                Row(
                    Column('requires_approval', css_class='col-md-6'),
                    Column('registration_fee', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                'Schedule',
                Row(
                    Column('check_in_start', css_class='col-md-4'),
                    Column('start_datetime', css_class='col-md-4'),
                    Column('estimated_end', css_class='col-md-4'),
                ),
            ),
            Fieldset(
                'Prizes & Settings',
                Row(
                    Column('prize_pool', css_class='col-md-4'),
                    Column('seeding_method', css_class='col-md-4'),
                    Column('best_of', css_class='col-md-4'),
                ),
                'prize_distribution',
            ),
            Fieldset(
                'Media & Links',
                Row(
                    Column('banner', css_class='col-md-6'),
                    Column('thumbnail', css_class='col-md-6'),
                ),
                Row(
                    Column('stream_url', css_class='col-md-6'),
                    Column('discord_invite', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                'Access & Venue',
                Row(
                    Column('is_public', css_class='col-md-3'),
                    Column('is_featured', css_class='col-md-3'),
                    Column('requires_verification', css_class='col-md-6'),
                ),
                Row(
                    Column('skill_requirement', css_class='col-md-6'),
                    Column('venue', css_class='col-md-6'),
                ),
            ),
            Submit('submit', 'Create Tournament', css_class='btn btn-primary mt-3')
        )
    
    def clean_name(self):
        """Validate and sanitize tournament name."""
        name = self.cleaned_data.get('name')
        return TournamentSecurityValidator.validate_tournament_name(name)
    
    def clean_slug(self):
        """Validate tournament slug."""
        slug = self.cleaned_data.get('slug')
        return TournamentSecurityValidator.validate_tournament_slug(slug)
    
    def clean_description(self):
        """Validate and sanitize description."""
        description = self.cleaned_data.get('description')
        return TournamentSecurityValidator.validate_description(description)
    
    def clean_rules(self):
        """Validate and sanitize rules."""
        rules = self.cleaned_data.get('rules')
        return TournamentSecurityValidator.validate_rules(rules)
    
    def clean_stream_url(self):
        """Validate stream URL."""
        url = self.cleaned_data.get('stream_url')
        return TournamentSecurityValidator.validate_url(url, 'Stream URL')
    
    def clean_discord_invite(self):
        """Validate Discord invite URL."""
        url = self.cleaned_data.get('discord_invite')
        return TournamentSecurityValidator.validate_url(url, 'Discord invite')
    
    def clean(self):
        cleaned_data = super().clean()
        registration_start = cleaned_data.get('registration_start')
        registration_end = cleaned_data.get('registration_end')
        check_in_start = cleaned_data.get('check_in_start')
        start_datetime = cleaned_data.get('start_datetime')
        
        # Validate date sequence
        if all([registration_start, registration_end, check_in_start, start_datetime]):
            if registration_start >= registration_end:
                raise forms.ValidationError(
                    'Registration end must be after registration start'
                )
            
            if registration_end >= check_in_start:
                raise forms.ValidationError(
                    'Check-in must start after registration ends'
                )
            
            if check_in_start >= start_datetime:
                raise forms.ValidationError(
                    'Tournament start must be after check-in starts'
                )
            
            # Fix timezone comparison issue
            # datetime-local inputs are naive, but Django converts them to timezone-aware
            # using the server's timezone. We need to compare with current time properly.
            now = timezone.now()
            
            # If registration_start is naive (from datetime-local input), make it timezone-aware
            if registration_start and timezone.is_naive(registration_start):
                # Convert naive datetime to timezone-aware using current timezone
                registration_start_aware = timezone.make_aware(registration_start)
            else:
                registration_start_aware = registration_start
            
            # Compare timezone-aware datetimes with a small buffer to account for form submission delays
            buffer_time = timezone.timedelta(minutes=1)
            if registration_start_aware and registration_start_aware < (now - buffer_time):
                raise forms.ValidationError(
                    'Registration cannot start in the past'
                )
        
        # Validate participants
        min_participants = cleaned_data.get('min_participants')
        max_participants = cleaned_data.get('max_participants')
        
        if min_participants and max_participants:
            if min_participants > max_participants:
                raise forms.ValidationError(
                    'Minimum participants cannot exceed maximum'
                )
        
        return cleaned_data


class MatchReportForm(forms.Form):
    """Form for reporting match scores"""
    
    score_p1 = forms.IntegerField(
        min_value=0,
        label='Player 1 Score',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    score_p2 = forms.IntegerField(
        min_value=0,
        label='Player 2 Score',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        help_text='Optional notes about the match'
    )
    
    def __init__(self, *args, **kwargs):
        match = kwargs.pop('match', None)
        super().__init__(*args, **kwargs)
        
        if match:
            if match.participant1:
                self.fields['score_p1'].label = f'{match.participant1.display_name} Score'
            if match.participant2:
                self.fields['score_p2'].label = f'{match.participant2.display_name} Score'
    
    def clean_notes(self):
        """Validate and sanitize match notes."""
        notes = self.cleaned_data.get('notes')
        if notes:
            return TournamentSecurityValidator.sanitize_html_content(notes)
        return notes
    
    def clean(self):
        cleaned_data = super().clean()
        score_p1 = cleaned_data.get('score_p1')
        score_p2 = cleaned_data.get('score_p2')
        
        if score_p1 == score_p2:
            raise forms.ValidationError('Scores cannot be tied. There must be a winner.')
        
        return cleaned_data


class DisputeForm(forms.ModelForm):
    """Form for filing match disputes"""
    
    class Meta:
        model = MatchDispute
        fields = ['reason', 'evidence']
        widgets = {
            'reason': forms.Textarea(attrs={
                'rows': 5,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
                'placeholder': 'Explain the issue in detail...'
            }),
            'evidence': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm'
            })
        }
        help_texts = {
            'evidence': 'Upload screenshots or other proof (optional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'File Dispute', css_class='btn btn-danger'))
    
    def clean_reason(self):
        """Validate and sanitize dispute reason."""
        reason = self.cleaned_data.get('reason')
        if not reason:
            raise ValidationError("Dispute reason is required")
        
        if len(reason) > 2000:
            raise ValidationError("Dispute reason cannot exceed 2000 characters")
        
        return TournamentSecurityValidator.sanitize_html_content(reason)


class ParticipantApprovalForm(forms.Form):
    """Form for approving/rejecting participants"""
    
    action = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject')],
        widget=forms.RadioSelect
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text='Optional notes (visible to admins only)'
    )
    
    def clean_notes(self):
        """Validate and sanitize admin notes."""
        notes = self.cleaned_data.get('notes')
        if notes:
            return TournamentSecurityValidator.sanitize_html_content(notes)
        return notes