from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit
from .models import (CoachProfile, CoachAvailability, CoachingSession,
                     SessionReview, CoachingPackage, CoachGameExpertise)
from core.models import Game


class CoachProfileForm(forms.ModelForm):
    """Form for creating/editing coach profile"""
    
    class Meta:
        model = CoachProfile
        fields = [
            'bio', 'specializations', 'experience_level', 'years_experience',
            'achievements', 'hourly_rate', 'status', 'accepting_students',
            'max_students_per_week', 'min_session_duration', 'max_session_duration',
            'session_increment', 'offers_individual', 'offers_group', 'max_group_size',
            'preferred_platform', 'platform_username', 'profile_video'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 5}),
            'achievements': forms.Textarea(attrs={'rows': 4}),
            'specializations': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': '["Strategy", "Mechanics", "Game Sense"]'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'About You',
                'bio',
                'specializations',
                Row(
                    Column('experience_level', css_class='col-md-6'),
                    Column('years_experience', css_class='col-md-6'),
                ),
                'achievements',
            ),
            Fieldset(
                'Pricing & Availability',
                Row(
                    Column('hourly_rate', css_class='col-md-4'),
                    Column('status', css_class='col-md-4'),
                    Column('accepting_students', css_class='col-md-4'),
                ),
                'max_students_per_week',
            ),
            Fieldset(
                'Session Settings',
                Row(
                    Column('min_session_duration', css_class='col-md-4'),
                    Column('max_session_duration', css_class='col-md-4'),
                    Column('session_increment', css_class='col-md-4'),
                ),
                Row(
                    Column('offers_individual', css_class='col-md-4'),
                    Column('offers_group', css_class='col-md-4'),
                    Column('max_group_size', css_class='col-md-4'),
                ),
            ),
            Fieldset(
                'Video Platform',
                Row(
                    Column('preferred_platform', css_class='col-md-6'),
                    Column('platform_username', css_class='col-md-6'),
                ),
                'profile_video',
            ),
            Submit('submit', 'Save Profile', css_class='btn btn-primary mt-3')
        )


class CoachGameExpertiseForm(forms.ModelForm):
    """Form for adding game expertise"""
    
    class Meta:
        model = CoachGameExpertise
        fields = ['game', 'rank', 'rank_proof', 'specialization_notes',
                  'custom_hourly_rate', 'is_primary']
        widgets = {
            'specialization_notes': forms.Textarea(attrs={'rows': 3}),
        }


class CoachAvailabilityForm(forms.ModelForm):
    """Form for setting availability"""
    
    class Meta:
        model = CoachAvailability
        fields = ['weekday', 'start_time', 'end_time', 'is_active']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


# Formset for managing multiple availability slots
AvailabilityFormSet = inlineformset_factory(
    CoachProfile,
    CoachAvailability,
    form=CoachAvailabilityForm,
    extra=3,
    can_delete=True
)


class BookingForm(forms.ModelForm):
    """Form for booking a coaching session"""
    
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text='Select a date for your session'
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text='Select a time'
    )
    
    class Meta:
        model = CoachingSession
        fields = ['game', 'session_type', 'duration_minutes', 'topics', 'student_notes']
        widgets = {
            'topics': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': '["Positioning", "Combos", "Match-ups"]'
            }),
            'student_notes': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'What would you like to work on?'
            }),
        }
    
    def __init__(self, *args, coach=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.coach = coach
        
        if coach:
            # Limit game choices to coach's expertise
            self.fields['game'].queryset = Game.objects.filter(
                id__in=coach.game_expertise.values_list('game_id', flat=True)
            )
            
            # Set duration limits
            self.fields['duration_minutes'].widget = forms.Select(
                choices=self._get_duration_choices(),
                attrs={'class': 'form-control'}
            )
            
            # Adjust session type based on coach settings
            if not coach.offers_group:
                self.fields['session_type'].widget = forms.HiddenInput()
                self.fields['session_type'].initial = 'individual'
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
    
    def _get_duration_choices(self):
        """Generate duration choices based on coach settings"""
        if not self.coach:
            return []
        
        choices = []
        duration = self.coach.min_session_duration
        while duration <= self.coach.max_session_duration:
            hours = duration / 60
            if duration < 60:
                label = f"{duration} minutes"
            else:
                label = f"{hours:.1f} hours" if duration % 60 else f"{int(hours)} hour{'s' if hours > 1 else ''}"
            choices.append((duration, label))
            duration += self.coach.session_increment
        
        return choices
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        
        if date and time:
            # Combine date and time
            scheduled_start = timezone.make_aware(
                timezone.datetime.combine(date, time)
            )
            
            # Check if in the past
            if scheduled_start <= timezone.now():
                raise forms.ValidationError('Cannot book sessions in the past')
            
            # Check if coach is available
            weekday = date.weekday()
            is_available = self.coach.availability.filter(
                weekday=weekday,
                start_time__lte=time,
                end_time__gte=time,
                is_active=True
            ).exists()
            
            if not is_available:
                raise forms.ValidationError('Coach is not available at this time')
            
            # Set scheduled times
            duration = cleaned_data.get('duration_minutes', 60)
            cleaned_data['scheduled_start'] = scheduled_start
            cleaned_data['scheduled_end'] = scheduled_start + timezone.timedelta(
                minutes=duration
            )
        
        return cleaned_data


class SessionReviewForm(forms.ModelForm):
    """Form for reviewing a coaching session"""
    
    class Meta:
        model = SessionReview
        fields = [
            'rating', 'communication_rating', 'knowledge_rating',
            'patience_rating', 'title', 'review', 'would_recommend',
            'improvement_seen'
        ]
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f'{i} ★') for i in range(1, 6)]),
            'review': forms.Textarea(attrs={'rows': 6}),
        }
        help_texts = {
            'rating': 'Overall rating',
            'communication_rating': 'How well did the coach communicate?',
            'knowledge_rating': 'How knowledgeable was the coach?',
            'patience_rating': 'How patient was the coach?',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Overall Rating',
                'rating',
            ),
            Fieldset(
                'Detailed Ratings',
                Row(
                    Column('communication_rating', css_class='col-md-4'),
                    Column('knowledge_rating', css_class='col-md-4'),
                    Column('patience_rating', css_class='col-md-4'),
                ),
            ),
            Fieldset(
                'Your Review',
                'title',
                'review',
            ),
            Fieldset(
                'Recommendation',
                Row(
                    Column('would_recommend', css_class='col-md-6'),
                    Column('improvement_seen', css_class='col-md-6'),
                ),
            ),
            Submit('submit', 'Submit Review', css_class='btn btn-primary mt-3')
        )


class CoachResponseForm(forms.ModelForm):
    """Form for coach to respond to review"""
    
    class Meta:
        model = SessionReview
        fields = ['coach_response']
        widgets = {
            'coach_response': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Thank your student and address any feedback...'
            }),
        }


class PackageForm(forms.ModelForm):
    """Form for creating coaching packages"""
    
    class Meta:
        model = CoachingPackage
        fields = [
            'name', 'description', 'number_of_sessions', 'session_duration',
            'game', 'total_price', 'discount_percentage', 'valid_for_days',
            'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, coach=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if coach:
            # Limit games to coach's expertise
            self.fields['game'].queryset = Game.objects.filter(
                id__in=coach.game_expertise.values_list('game_id', flat=True)
            )
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Package Details',
                'name',
                'description',
                'game',
            ),
            Fieldset(
                'Sessions',
                Row(
                    Column('number_of_sessions', css_class='col-md-6'),
                    Column('session_duration', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                'Pricing',
                Row(
                    Column('total_price', css_class='col-md-6'),
                    Column('discount_percentage', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                'Validity',
                Row(
                    Column('valid_for_days', css_class='col-md-6'),
                    Column('is_active', css_class='col-md-6'),
                ),
            ),
            Submit('submit', 'Create Package', css_class='btn btn-primary mt-3')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        total_price = cleaned_data.get('total_price')
        discount = cleaned_data.get('discount_percentage', 0)
        
        if discount > 50:
            self.add_error('discount_percentage',
                          'Discount cannot exceed 50%')
        
        return cleaned_data


class SessionFilterForm(forms.Form):
    """Form for filtering coaching sessions"""
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    TYPE_CHOICES = [
        ('', 'All Types'),
        ('coaching', 'As Coach'),
        ('learning', 'As Student'),
    ]
    
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    type = forms.ChoiceField(choices=TYPE_CHOICES, required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))