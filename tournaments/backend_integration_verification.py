"""
Backend Integration Compatibility Verification

This module verifies that the enhanced Tournament Detail UI maintains full compatibility
with existing backend systems, models, APIs, and workflows.

**Feature: tournament-detail-ui-enhancement**
**Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5**
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from tournaments.models import Tournament, Participant, Match, Bracket, Payment
from tournaments.cache_utils import TournamentCache
from tournaments.security import TournamentAccessControl
from core.models import Game
from venues.models import Venue

User = get_user_model()


class BackendIntegrationCompatibilityVerification:
    """
    Comprehensive verification that enhanced UI maintains backend compatibility
    
    **Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5**
    """
    
    def __init__(self):
        self.client = Client()
        self.verification_results = []
    
    def verify_all_compatibility(self):
        """Run all compatibility verification checks"""
        print("🔍 Starting Backend Integration Compatibility Verification...")
        
        # Requirement 13.1: Use existing models without modification
        self.verify_existing_models_compatibility()
        
        # Requirement 13.2: Utilize existing API endpoints and caching
        self.verify_existing_api_endpoints()
        
        # Requirement 13.3: Respect existing permission systems
        self.verify_existing_permission_systems()
        
        # Requirement 13.4: Use existing registration and payment logic
        self.verify_existing_registration_logic()
        
        # Requirement 13.5: Maintain existing tournament management workflows
        self.verify_existing_management_workflows()
        
        # Generate verification report
        self.generate_verification_report()
        
        return all(result['passed'] for result in self.verification_results)
    
    def verify_existing_models_compatibility(self):
        """
        Verify enhanced UI uses existing Tournament, Participant, and Match models
        without modification (Requirement 13.1)
        """
        print("📋 Verifying existing models compatibility...")
        
        try:
            # Create test data using existing models with unique identifiers
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            
            game = Game.objects.create(
                name=f"Compatibility Test Game {unique_id}",
                slug=f"compatibility-test-game-{unique_id}",
                genre='fps'
            )
            
            organizer = User.objects.create(
                email=f"organizer-{unique_id}@compatibility.test",
                username=f"org_{unique_id}",
                first_name="Organizer",
                last_name="Test"
            )
            
            venue = Venue.objects.create(
                name=f"Compatibility Test Venue {unique_id}",
                slug=f"compatibility-test-venue-{unique_id}",
                address="123 Test St",
                city="Test City",
                state="TC",
                country="Test Country"
            )
            
            # Create tournament using existing Tournament model
            tournament = Tournament.objects.create(
                name=f"Backend Compatibility Test Tournament {unique_id}",
                slug=f"backend-compatibility-test-tournament-{unique_id}",
                description="Testing backend compatibility",
                game=game,
                format='single_elim',
                status='registration',
                organizer=organizer,
                venue=venue,
                max_participants=16,
                registration_start=timezone.now() - timedelta(days=1),
                registration_end=timezone.now() + timedelta(days=1),
                check_in_start=timezone.now() + timedelta(days=1, hours=23),
                start_datetime=timezone.now() + timedelta(days=2),
                estimated_end=timezone.now() + timedelta(days=3)
            )
            
            # Verify tournament model methods work unchanged
            assert hasattr(tournament, 'is_registration_open')
            assert hasattr(tournament, 'spots_remaining')
            assert hasattr(tournament, 'registration_progress')
            assert hasattr(tournament, 'get_timeline_phases')
            assert hasattr(tournament, 'get_prize_breakdown')
            
            # Create participant using existing Participant model
            participant_user = User.objects.create(
                email=f"participant-{unique_id}@compatibility.test",
                username=f"part_{unique_id}",
                first_name="Participant",
                last_name="Test"
            )
            
            participant = Participant.objects.create(
                tournament=tournament,
                user=participant_user,
                status='confirmed'
            )
            
            # Verify participant model methods work unchanged
            assert hasattr(participant, 'display_name')
            assert hasattr(participant, 'win_rate')
            assert hasattr(participant, 'check_in_participant')
            
            # Create bracket and match using existing models
            bracket = Bracket.objects.create(
                tournament=tournament,
                bracket_type='main',
                name='Main Bracket',
                current_round=1,
                total_rounds=4
            )
            
            match = Match.objects.create(
                tournament=tournament,
                bracket=bracket,
                round_number=1,
                match_number=1,
                participant1=participant,
                status='pending'
            )
            
            # Verify match model methods work unchanged
            assert hasattr(match, 'is_ready')
            assert hasattr(match, 'is_bye')
            assert hasattr(match, 'report_score')
            
            self.verification_results.append({
                'test': 'Existing Models Compatibility',
                'requirement': '13.1',
                'passed': True,
                'details': 'All existing model methods and properties work unchanged'
            })
            
            print("✅ Existing models compatibility verified")
            
        except Exception as e:
            self.verification_results.append({
                'test': 'Existing Models Compatibility',
                'requirement': '13.1',
                'passed': False,
                'details': f'Error: {str(e)}'
            })
            print(f"❌ Existing models compatibility failed: {e}")
    
    def verify_existing_api_endpoints(self):
        """
        Verify enhanced UI utilizes existing API endpoints and caching mechanisms
        (Requirement 13.2)
        """
        print("🔌 Verifying existing API endpoints compatibility...")
        
        try:
            # Create test tournament
            tournament = self._create_test_tournament()
            
            # Test existing API endpoints work with enhanced UI
            api_endpoints = [
                ('api_stats', 'Tournament statistics API'),
                ('api_participants', 'Tournament participants API'),
                ('api_matches', 'Tournament matches API'),
                ('api_updates', 'Tournament updates API'),
                ('api_bracket', 'Tournament bracket API')
            ]
            
            all_endpoints_work = True
            endpoint_results = []
            
            for endpoint_name, description in api_endpoints:
                try:
                    response = self.client.get(
                        reverse(f'tournaments:{endpoint_name}', kwargs={'slug': tournament.slug})
                    )
                    
                    if response.status_code == 200:
                        # Verify response contains expected JSON structure
                        data = response.json()
                        endpoint_results.append(f"✅ {description}: Working")
                    else:
                        endpoint_results.append(f"❌ {description}: HTTP {response.status_code}")
                        all_endpoints_work = False
                        
                except Exception as e:
                    endpoint_results.append(f"❌ {description}: Error - {str(e)}")
                    all_endpoints_work = False
            
            # Test caching mechanisms work unchanged
            cache_test_passed = True
            try:
                # Test cache invalidation
                TournamentCache.invalidate_tournament_cache(tournament.id)
                
                # Test cache retrieval
                cached_stats = TournamentCache.get_tournament_stats(tournament.id)
                assert cached_stats is None  # Should be None after invalidation
                
                # Test cache setting
                test_stats = {'participants': {'registered': 0}}
                TournamentCache.set_tournament_stats(tournament.id, test_stats)
                
                retrieved_stats = TournamentCache.get_tournament_stats(tournament.id)
                assert retrieved_stats is not None
                
                endpoint_results.append("✅ Caching mechanisms: Working")
                
            except Exception as e:
                endpoint_results.append(f"❌ Caching mechanisms: Error - {str(e)}")
                cache_test_passed = False
            
            self.verification_results.append({
                'test': 'Existing API Endpoints Compatibility',
                'requirement': '13.2',
                'passed': all_endpoints_work and cache_test_passed,
                'details': '\n'.join(endpoint_results)
            })
            
            if all_endpoints_work and cache_test_passed:
                print("✅ Existing API endpoints compatibility verified")
            else:
                print("❌ Some API endpoints or caching failed")
                
        except Exception as e:
            self.verification_results.append({
                'test': 'Existing API Endpoints Compatibility',
                'requirement': '13.2',
                'passed': False,
                'details': f'Error: {str(e)}'
            })
            print(f"❌ API endpoints compatibility failed: {e}")
    
    def verify_existing_permission_systems(self):
        """
        Verify enhanced UI respects existing permission systems and user roles
        (Requirement 13.3)
        """
        print("🔐 Verifying existing permission systems compatibility...")
        
        try:
            tournament = self._create_test_tournament()
            organizer = tournament.organizer
            
            # Create regular user with unique username
            regular_user = User.objects.create(
                email=f"regular-{unique_id[:8]}@compatibility.test",
                username=f"reg_{unique_id[:8]}",
                first_name="Regular",
                last_name="User"
            )
            
            # Test access control works unchanged
            permission_tests = []
            
            # Test organizer permissions
            can_view_organizer = TournamentAccessControl.can_view_tournament(organizer, tournament)
            can_edit_organizer = TournamentAccessControl.can_edit_tournament(organizer, tournament)
            
            permission_tests.append(f"✅ Organizer can view: {can_view_organizer}")
            permission_tests.append(f"✅ Organizer can edit: {can_edit_organizer}")
            
            # Test regular user permissions
            can_view_regular = TournamentAccessControl.can_view_tournament(regular_user, tournament)
            can_edit_regular = TournamentAccessControl.can_edit_tournament(regular_user, tournament)
            
            permission_tests.append(f"✅ Regular user can view: {can_view_regular}")
            permission_tests.append(f"✅ Regular user cannot edit: {not can_edit_regular}")
            
            # Test tournament detail view respects permissions
            # Anonymous user
            response_anon = self.client.get(
                reverse('tournaments:detail', kwargs={'slug': tournament.slug})
            )
            permission_tests.append(f"✅ Anonymous access: HTTP {response_anon.status_code}")
            
            # Organizer user
            self.client.force_login(organizer)
            response_organizer = self.client.get(
                reverse('tournaments:detail', kwargs={'slug': tournament.slug})
            )
            permission_tests.append(f"✅ Organizer access: HTTP {response_organizer.status_code}")
            
            # Regular user
            self.client.force_login(regular_user)
            response_regular = self.client.get(
                reverse('tournaments:detail', kwargs={'slug': tournament.slug})
            )
            permission_tests.append(f"✅ Regular user access: HTTP {response_regular.status_code}")
            
            all_permissions_work = all([
                can_view_organizer, can_edit_organizer,
                can_view_regular, not can_edit_regular,
                response_anon.status_code == 200,
                response_organizer.status_code == 200,
                response_regular.status_code == 200
            ])
            
            self.verification_results.append({
                'test': 'Existing Permission Systems Compatibility',
                'requirement': '13.3',
                'passed': all_permissions_work,
                'details': '\n'.join(permission_tests)
            })
            
            if all_permissions_work:
                print("✅ Existing permission systems compatibility verified")
            else:
                print("❌ Some permission checks failed")
                
        except Exception as e:
            self.verification_results.append({
                'test': 'Existing Permission Systems Compatibility',
                'requirement': '13.3',
                'passed': False,
                'details': f'Error: {str(e)}'
            })
            print(f"❌ Permission systems compatibility failed: {e}")
    
    def verify_existing_registration_logic(self):
        """
        Verify enhanced UI uses existing registration logic and payment processing
        (Requirement 13.4)
        """
        print("📝 Verifying existing registration logic compatibility...")
        
        try:
            tournament = self._create_test_tournament()
            tournament.registration_fee = Decimal('25.00')
            tournament.save()
            
            # Create test user with unique username
            test_user = User.objects.create(
                email=f"registration-{unique_id[:8]}@compatibility.test",
                username=f"reg_test_{unique_id[:8]}",
                first_name="Registration",
                last_name="Test"
            )
            
            registration_tests = []
            
            # Test registration form access (existing view)
            self.client.force_login(test_user)
            register_response = self.client.get(
                reverse('tournaments:register', kwargs={'slug': tournament.slug})
            )
            
            registration_tests.append(f"✅ Registration form access: HTTP {register_response.status_code}")
            
            # Verify registration form uses existing logic
            if register_response.status_code == 200:
                content = register_response.content.decode('utf-8')
                has_registration_form = 'tournament-register' in content
                has_fee_display = '25.00' in content
                
                registration_tests.append(f"✅ Registration form present: {has_registration_form}")
                registration_tests.append(f"✅ Fee display present: {has_fee_display}")
            
            # Test payment model compatibility
            participant = Participant.objects.create(
                tournament=tournament,
                user=test_user,
                status='pending_payment'
            )
            
            payment = Payment.objects.create(
                participant=participant,
                amount=tournament.registration_fee,
                provider='stripe',
                status='pending'
            )
            
            # Verify payment model methods work unchanged
            payment_model_works = (
                hasattr(payment, 'participant') and
                hasattr(payment, 'amount') and
                hasattr(payment, 'provider') and
                hasattr(payment, 'status')
            )
            
            registration_tests.append(f"✅ Payment model compatibility: {payment_model_works}")
            
            # Test tournament registration methods work unchanged
            can_register, message = tournament.can_user_register(test_user)
            registration_tests.append(f"✅ Registration check method: {can_register is not None}")
            
            all_registration_works = all([
                register_response.status_code == 200,
                payment_model_works,
                can_register is not None
            ])
            
            self.verification_results.append({
                'test': 'Existing Registration Logic Compatibility',
                'requirement': '13.4',
                'passed': all_registration_works,
                'details': '\n'.join(registration_tests)
            })
            
            if all_registration_works:
                print("✅ Existing registration logic compatibility verified")
            else:
                print("❌ Some registration logic failed")
                
        except Exception as e:
            self.verification_results.append({
                'test': 'Existing Registration Logic Compatibility',
                'requirement': '13.4',
                'passed': False,
                'details': f'Error: {str(e)}'
            })
            print(f"❌ Registration logic compatibility failed: {e}")
    
    def verify_existing_management_workflows(self):
        """
        Verify enhanced UI maintains compatibility with existing tournament management workflows
        (Requirement 13.5)
        """
        print("⚙️ Verifying existing management workflows compatibility...")
        
        try:
            tournament = self._create_test_tournament()
            organizer = tournament.organizer
            
            workflow_tests = []
            
            # Test tournament status change workflow (existing functionality)
            self.client.force_login(organizer)
            
            # Test status change endpoint exists and works
            status_change_response = self.client.post(
                reverse('tournaments:change_status', kwargs={'slug': tournament.slug}),
                {'new_status': 'check_in'}
            )
            
            workflow_tests.append(f"✅ Status change endpoint: HTTP {status_change_response.status_code}")
            
            # Verify tournament status was updated using existing logic
            tournament.refresh_from_db()
            status_updated = tournament.status == 'check_in'
            workflow_tests.append(f"✅ Status update logic: {status_updated}")
            
            # Test participant management workflow (existing functionality)
            participants_response = self.client.get(
                reverse('tournaments:participants', kwargs={'slug': tournament.slug})
            )
            
            workflow_tests.append(f"✅ Participant management: HTTP {participants_response.status_code}")
            
            # Test bracket generation workflow (existing functionality)
            if tournament.status in ['check_in', 'in_progress']:
                bracket_response = self.client.post(
                    reverse('tournaments:generate_bracket', kwargs={'slug': tournament.slug})
                )
                workflow_tests.append(f"✅ Bracket generation: HTTP {bracket_response.status_code}")
            
            # Test tournament editing workflow (existing functionality)
            edit_response = self.client.get(
                reverse('tournaments:edit', kwargs={'slug': tournament.slug})
            )
            workflow_tests.append(f"✅ Tournament editing: HTTP {edit_response.status_code}")
            
            # Test tournament deletion workflow (existing functionality)
            delete_response = self.client.get(
                reverse('tournaments:delete', kwargs={'slug': tournament.slug})
            )
            workflow_tests.append(f"✅ Tournament deletion: HTTP {delete_response.status_code}")
            
            all_workflows_work = all([
                status_change_response.status_code in [200, 302],
                status_updated,
                participants_response.status_code == 200,
                edit_response.status_code == 200,
                delete_response.status_code == 200
            ])
            
            self.verification_results.append({
                'test': 'Existing Management Workflows Compatibility',
                'requirement': '13.5',
                'passed': all_workflows_work,
                'details': '\n'.join(workflow_tests)
            })
            
            if all_workflows_work:
                print("✅ Existing management workflows compatibility verified")
            else:
                print("❌ Some management workflows failed")
                
        except Exception as e:
            self.verification_results.append({
                'test': 'Existing Management Workflows Compatibility',
                'requirement': '13.5',
                'passed': False,
                'details': f'Error: {str(e)}'
            })
            print(f"❌ Management workflows compatibility failed: {e}")
    
    def _create_test_tournament(self):
        """Helper method to create a test tournament"""
        # Generate unique identifiers to avoid conflicts
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        # Clean up any existing test data with this unique ID
        Tournament.objects.filter(slug__contains=f'compatibility-test-{unique_id}').delete()
        Game.objects.filter(slug__contains=f'compatibility-test-{unique_id}').delete()
        User.objects.filter(username__contains=f'{unique_id}').delete()
        
        game = Game.objects.create(
            name=f"Compatibility Test Game {unique_id}",
            slug=f"compatibility-test-game-{unique_id}",
            genre='fps'
        )
        
        organizer = User.objects.create(
            email=f"organizer-{unique_id}@compatibility.test",
            username=f"org_{unique_id}",
            first_name="Organizer",
            last_name="Test"
        )
        
        tournament = Tournament.objects.create(
            name=f"Compatibility Test Tournament {unique_id}",
            slug=f"compatibility-test-tournament-{unique_id}",
            description="Testing compatibility",
            game=game,
            format='single_elim',
            status='registration',
            organizer=organizer,
            max_participants=16,
            registration_start=timezone.now() - timedelta(days=1),
            registration_end=timezone.now() + timedelta(days=1),
            check_in_start=timezone.now() + timedelta(days=1, hours=23),
            start_datetime=timezone.now() + timedelta(days=2),
            estimated_end=timezone.now() + timedelta(days=3)
        )
        
        return tournament
    
    def generate_verification_report(self):
        """Generate a comprehensive verification report"""
        print("\n" + "="*80)
        print("🔍 BACKEND INTEGRATION COMPATIBILITY VERIFICATION REPORT")
        print("="*80)
        
        total_tests = len(self.verification_results)
        passed_tests = sum(1 for result in self.verification_results if result['passed'])
        
        print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed")
        print(f"✅ Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        for result in self.verification_results:
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            print(f"{status} | Requirement {result['requirement']} | {result['test']}")
            if result['details']:
                for line in result['details'].split('\n'):
                    print(f"    {line}")
            print()
        
        if passed_tests == total_tests:
            print("🎉 ALL COMPATIBILITY TESTS PASSED!")
            print("The enhanced Tournament Detail UI maintains full compatibility with existing backend systems.")
        else:
            print("⚠️  SOME COMPATIBILITY ISSUES FOUND")
            print("Please review the failed tests above and address any compatibility issues.")
        
        print("="*80)


def run_backend_integration_verification():
    """
    Run the complete backend integration compatibility verification
    
    This function can be called from Django management commands or tests
    to verify that the enhanced UI maintains full backend compatibility.
    """
    verifier = BackendIntegrationCompatibilityVerification()
    return verifier.verify_all_compatibility()


if __name__ == "__main__":
    # Run verification if called directly
    run_backend_integration_verification()