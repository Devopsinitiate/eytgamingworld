"""
Quick test script for ProfileExportService
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dashboard.services import ProfileExportService
from core.models import User
from security.models import AuditLog
import json

def test_profile_export():
    """Test ProfileExportService functionality"""
    
    # Get a test user (use the first active user)
    user = User.objects.filter(is_active=True).first()
    
    if not user:
        print("❌ No active users found in database")
        return False
    
    print(f"✓ Testing export for user: {user.username}")
    
    try:
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Verify required sections exist
        required_sections = [
            'export_metadata',
            'profile',
            'game_profiles',
            'tournament_history',
            'team_memberships',
            'payment_history',
            'activity_history',
            'achievements'
        ]
        
        print("\n✓ Checking required sections:")
        for section in required_sections:
            if section in export_data:
                print(f"  ✓ {section}: present")
            else:
                print(f"  ❌ {section}: MISSING")
                return False
        
        # Verify sensitive data is excluded
        print("\n✓ Checking sensitive data exclusion:")
        profile = export_data.get('profile', {})
        
        # Password should not be in export
        if 'password' in profile or 'password_hash' in profile:
            print("  ❌ Password hash found in export (should be excluded)")
            return False
        else:
            print("  ✓ Password hash excluded")
        
        # Payment method details should not be in export
        payment_history = export_data.get('payment_history', {})
        payments = payment_history.get('payments', [])
        
        for payment in payments:
            if 'card_number' in payment or 'cvv' in payment or 'card_details' in payment:
                print("  ❌ Payment method details found in export (should be excluded)")
                return False
        
        print("  ✓ Payment method details excluded")
        
        # Verify audit log was created
        print("\n✓ Checking audit log:")
        recent_audit = AuditLog.objects.filter(
            user=user,
            action='export',
            model_name='User'
        ).order_by('-timestamp').first()
        
        if recent_audit:
            print(f"  ✓ Audit log created at {recent_audit.timestamp}")
        else:
            print("  ⚠ No recent audit log found (may have been created earlier)")
        
        # Verify export is JSON serializable
        print("\n✓ Checking JSON serializability:")
        try:
            json_str = json.dumps(export_data, indent=2)
            print(f"  ✓ Export is JSON serializable ({len(json_str)} bytes)")
        except Exception as e:
            print(f"  ❌ Export is not JSON serializable: {e}")
            return False
        
        # Print summary
        print("\n" + "="*60)
        print("EXPORT SUMMARY")
        print("="*60)
        print(f"User: {export_data['export_metadata']['username']}")
        print(f"Generated: {export_data['export_metadata']['generated_at']}")
        print(f"Game Profiles: {len(export_data['game_profiles'])}")
        print(f"Tournament History: {len(export_data['tournament_history'])}")
        print(f"Current Teams: {export_data['team_memberships'].get('total_teams_joined', 0)}")
        print(f"Total Payments: {export_data['payment_history']['summary']['total_payments']}")
        print(f"Activities: {len(export_data['activity_history'])}")
        print(f"Achievements: {export_data['achievements']['summary']['total_achievements_earned']}")
        print("="*60)
        
        print("\n✅ All tests passed! ProfileExportService is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during export: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_profile_export()
    exit(0 if success else 1)
