from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import re

from .models import Team
from core.models import Game


class TeamCreateForm(forms.ModelForm):
    """Form for creating a new team"""
    
    class Meta:
        model = Team
        fields = [
            'name', 'tag', 'game', 'description',
            'logo', 'banner',
            'max_members', 'requires_approval', 'is_recruiting', 'is_public',
            'discord_server', 'twitter_url', 'twitch_url'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50',
                'placeholder': 'Enter team name'
            }),
            'tag': forms.TextInput(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50',
                'placeholder': 'e.g., TSM, C9',
                'maxlength': '10'
            }),
            'game': forms.Select(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50',
                'placeholder': 'Describe your team, playstyle, and goals...',
                'rows': 4
            }),
            'logo': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*'
            }),
            'banner': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*'
            }),
            'max_members': forms.NumberInput(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50',
                'min': '2',
                'max': '50'
            }),
            'requires_approval': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary bg-background-dark border-card-border-dark rounded focus:ring-primary focus:ring-2'
            }),
            'is_recruiting': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary bg-background-dark border-card-border-dark rounded focus:ring-primary focus:ring-2'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary bg-background-dark border-card-border-dark rounded focus:ring-primary focus:ring-2'
            }),
            'discord_server': forms.URLInput(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50',
                'placeholder': 'https://discord.gg/...'
            }),
            'twitter_url': forms.URLInput(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50',
                'placeholder': 'https://twitter.com/...'
            }),
            'twitch_url': forms.URLInput(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50',
                'placeholder': 'https://twitch.tv/...'
            }),
        }
        labels = {
            'name': 'Team Name',
            'tag': 'Team Tag',
            'game': 'Game',
            'description': 'Description',
            'logo': 'Team Logo',
            'banner': 'Team Banner',
            'max_members': 'Maximum Members',
            'requires_approval': 'Require approval for new members',
            'is_recruiting': 'Currently recruiting',
            'is_public': 'Public team (visible to everyone)',
            'discord_server': 'Discord Server',
            'twitter_url': 'Twitter',
            'twitch_url': 'Twitch',
        }
        help_texts = {
            'name': 'Choose a unique name for your team',
            'tag': '2-10 characters, letters and numbers only',
            'description': 'Tell potential members about your team',
            'logo': 'Square image recommended (max 5MB)',
            'banner': 'Wide image recommended (max 5MB)',
            'max_members': 'Maximum number of team members (2-50)',
        }
    
    def clean_name(self):
        """Validate team name is unique"""
        name = self.cleaned_data.get('name')
        
        if not name:
            raise ValidationError('Team name is required.')
        
        # Check if name already exists (case-insensitive)
        if Team.objects.filter(name__iexact=name).exists():
            raise ValidationError('A team with this name already exists.')
        
        return name
    
    def clean_tag(self):
        """Validate team tag format and uniqueness"""
        tag = self.cleaned_data.get('tag')
        
        if not tag:
            raise ValidationError('Team tag is required.')
        
        # Check length
        if len(tag) < 2 or len(tag) > 10:
            raise ValidationError('Team tag must be between 2 and 10 characters.')
        
        # Check format (alphanumeric only)
        if not re.match(r'^[A-Za-z0-9]+$', tag):
            raise ValidationError('Team tag can only contain letters and numbers.')
        
        # Check if tag already exists (case-insensitive)
        if Team.objects.filter(tag__iexact=tag).exists():
            raise ValidationError('A team with this tag already exists.')
        
        return tag.upper()  # Store tags in uppercase
    
    def clean_logo(self):
        """Validate logo file size"""
        logo = self.cleaned_data.get('logo')
        
        if logo:
            # Check file size (5MB limit)
            if logo.size > 5 * 1024 * 1024:
                raise ValidationError('Logo file size must be less than 5MB.')
        
        return logo
    
    def clean_banner(self):
        """Validate banner file size"""
        banner = self.cleaned_data.get('banner')
        
        if banner:
            # Check file size (5MB limit)
            if banner.size > 5 * 1024 * 1024:
                raise ValidationError('Banner file size must be less than 5MB.')
        
        return banner
    
    def clean_max_members(self):
        """Validate max members is within acceptable range"""
        max_members = self.cleaned_data.get('max_members')
        
        if max_members is not None:
            if max_members < 2:
                raise ValidationError('Team must allow at least 2 members.')
            if max_members > 50:
                raise ValidationError('Team cannot have more than 50 members.')
        
        return max_members


class TeamSettingsForm(forms.ModelForm):
    """Form for updating team settings"""
    
    class Meta:
        model = Team
        fields = [
            'name', 'tag', 'description',
            'logo', 'banner',
            'max_members', 'requires_approval', 'is_recruiting', 'is_public',
            'discord_server', 'twitter_url', 'twitch_url'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50',
                'placeholder': 'Enter team name'
            }),
            'tag': forms.TextInput(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50',
                'placeholder': 'e.g., TSM, C9',
                'maxlength': '10'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50',
                'placeholder': 'Describe your team, playstyle, and goals...',
                'rows': 4
            }),
            'logo': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*'
            }),
            'banner': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*'
            }),
            'max_members': forms.NumberInput(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50',
                'min': '2',
                'max': '50'
            }),
            'requires_approval': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary bg-background-dark border-card-border-dark rounded focus:ring-primary focus:ring-2'
            }),
            'is_recruiting': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary bg-background-dark border-card-border-dark rounded focus:ring-primary focus:ring-2'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary bg-background-dark border-card-border-dark rounded focus:ring-primary focus:ring-2'
            }),
            'discord_server': forms.URLInput(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50',
                'placeholder': 'https://discord.gg/...'
            }),
            'twitter_url': forms.URLInput(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50',
                'placeholder': 'https://twitter.com/...'
            }),
            'twitch_url': forms.URLInput(attrs={
                'class': 'w-full bg-background-dark text-white border border-card-border-dark rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50',
                'placeholder': 'https://twitch.tv/...'
            }),
        }
        labels = {
            'name': 'Team Name',
            'tag': 'Team Tag',
            'description': 'Description',
            'logo': 'Team Logo',
            'banner': 'Team Banner',
            'max_members': 'Maximum Members',
            'requires_approval': 'Require approval for new members',
            'is_recruiting': 'Currently recruiting',
            'is_public': 'Public team (visible to everyone)',
            'discord_server': 'Discord Server',
            'twitter_url': 'Twitter',
            'twitch_url': 'Twitch',
        }
        help_texts = {
            'name': 'Choose a unique name for your team',
            'tag': '2-10 characters, letters and numbers only',
            'description': 'Tell potential members about your team',
            'logo': 'Square image recommended (max 5MB)',
            'banner': 'Wide image recommended (max 5MB)',
            'max_members': 'Maximum number of team members (2-50)',
        }
    
    def __init__(self, *args, **kwargs):
        self.instance_id = kwargs.get('instance').id if kwargs.get('instance') else None
        super().__init__(*args, **kwargs)
    
    def clean_name(self):
        """Validate team name is unique (excluding current team)"""
        name = self.cleaned_data.get('name')
        
        if not name:
            raise ValidationError('Team name is required.')
        
        # Check if name already exists (case-insensitive), excluding current team
        existing = Team.objects.filter(name__iexact=name)
        if self.instance_id:
            existing = existing.exclude(id=self.instance_id)
        
        if existing.exists():
            raise ValidationError('A team with this name already exists.')
        
        return name
    
    def clean_tag(self):
        """Validate team tag format and uniqueness (excluding current team)"""
        tag = self.cleaned_data.get('tag')
        
        if not tag:
            raise ValidationError('Team tag is required.')
        
        # Check length
        if len(tag) < 2 or len(tag) > 10:
            raise ValidationError('Team tag must be between 2 and 10 characters.')
        
        # Check format (alphanumeric only)
        if not re.match(r'^[A-Za-z0-9]+$', tag):
            raise ValidationError('Team tag can only contain letters and numbers.')
        
        # Check if tag already exists (case-insensitive), excluding current team
        existing = Team.objects.filter(tag__iexact=tag)
        if self.instance_id:
            existing = existing.exclude(id=self.instance_id)
        
        if existing.exists():
            raise ValidationError('A team with this tag already exists.')
        
        return tag.upper()  # Store tags in uppercase
    
    def clean_logo(self):
        """Validate logo file size"""
        logo = self.cleaned_data.get('logo')
        
        if logo and hasattr(logo, 'size'):
            # Check file size (5MB limit)
            if logo.size > 5 * 1024 * 1024:
                raise ValidationError('Logo file size must be less than 5MB.')
        
        return logo
    
    def clean_banner(self):
        """Validate banner file size"""
        banner = self.cleaned_data.get('banner')
        
        if banner and hasattr(banner, 'size'):
            # Check file size (5MB limit)
            if banner.size > 5 * 1024 * 1024:
                raise ValidationError('Banner file size must be less than 5MB.')
        
        return banner
    
    def clean_max_members(self):
        """Validate max members is within acceptable range"""
        max_members = self.cleaned_data.get('max_members')
        
        if max_members is not None:
            if max_members < 2:
                raise ValidationError('Team must allow at least 2 members.')
            if max_members > 50:
                raise ValidationError('Team cannot have more than 50 members.')
        
        return max_members
