from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth import get_user_model
import re

User = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom adapter to handle username generation from email"""
    
    def save_user(self, request, user, form, commit=True):
        """
        Save user with auto-generated username from email
        """
        user = super().save_user(request, user, form, commit=False)
        
        # Generate username from email if not provided
        if not user.username:
            user.username = self.generate_unique_username(user.email)
        
        if commit:
            user.save()
        
        return user
    
    def generate_unique_username(self, txts):
        """
        Generate a unique username from a list of text options or a single email
        This method is called by django-allauth with a list of potential username sources
        """
        # Handle both list and string inputs
        if isinstance(txts, list):
            # Try to find an email in the list
            email = None
            for txt in txts:
                if txt and '@' in str(txt):
                    email = str(txt)
                    break
            
            # If no email found, use the first non-empty value
            if not email:
                for txt in txts:
                    if txt:
                        email = str(txt)
                        break
            
            # If still no value, use 'user'
            if not email:
                email = 'user@example.com'
        else:
            email = str(txts) if txts else 'user@example.com'
        
        # Extract base username from email (part before @)
        if '@' in email:
            base_username = email.split('@')[0]
        else:
            base_username = email
        
        # Clean username: remove special characters, keep only alphanumeric and underscores
        base_username = re.sub(r'[^\w]', '_', base_username).lower()
        
        # Ensure we have at least some characters
        if not base_username or base_username == '_':
            base_username = 'user'
        
        # Ensure username is not too long (max 30 chars)
        base_username = base_username[:25]
        
        # Check if username exists (including empty string), if so, append numbers
        username = base_username
        counter = 1
        
        # Also check for empty username to avoid the duplicate key error
        while User.objects.filter(username=username).exists() or username == '':
            # Append counter to make it unique
            username = f"{base_username}_{counter}"
            counter += 1
            
            # Ensure we don't exceed max length
            if len(username) > 30:
                base_username = base_username[:20]
                username = f"{base_username}_{counter}"
        
        return username
