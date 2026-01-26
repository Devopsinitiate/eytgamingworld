from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import re

User = get_user_model()


class Command(BaseCommand):
    help = 'Fix users with empty usernames'

    def handle(self, *args, **options):
        # Find users with empty or None usernames
        empty_username_users = User.objects.filter(username__in=['', None])
        
        count = empty_username_users.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No users with empty usernames found.'))
            return
        
        self.stdout.write(f'Found {count} user(s) with empty usernames. Fixing...')
        
        for user in empty_username_users:
            # Generate username from email
            base_username = user.email.split('@')[0]
            base_username = re.sub(r'[^\w]', '_', base_username).lower()
            
            if not base_username or base_username == '_':
                base_username = 'user'
            
            base_username = base_username[:25]
            
            # Find unique username
            username = base_username
            counter = 1
            
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
                
                if len(username) > 30:
                    base_username = base_username[:20]
                    username = f"{base_username}_{counter}"
            
            # Update user
            user.username = username
            user.save(update_fields=['username'])
            
            self.stdout.write(
                self.style.SUCCESS(f'Fixed user {user.email}: username set to "{username}"')
            )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully fixed {count} user(s).'))
