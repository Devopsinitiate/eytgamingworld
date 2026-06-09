"""
Locust load tests for EYTGaming critical endpoints.

Run with: locust -f locustfile.py --host=http://localhost:8000
"""
from locust import HttpUser, task, between


class AnonymousBrowsingUser(HttpUser):
    """Simulates an anonymous visitor browsing public pages."""
    wait_time = between(1, 5)

    @task(3)
    def view_homepage(self):
        self.client.get('/')

    @task(2)
    def view_coach_list(self):
        self.client.get('/coaching/')

    @task(2)
    def view_tournament_list(self):
        self.client.get('/tournaments/')

    @task(1)
    def view_venue_list(self):
        self.client.get('/venues/')

    @task(1)
    def view_about(self):
        self.client.get('/about/')

    @task(1)
    def view_terms(self):
        self.client.get('/terms/')

    @task(1)
    def view_privacy(self):
        self.client.get('/privacy/')

    @task(1)
    def view_news(self):
        self.client.get('/news/')


class AuthenticatedUser(HttpUser):
    """Simulates a logged-in user interacting with the platform."""
    wait_time = between(2, 8)

    def on_start(self):
        """Log in before starting tasks."""
        self.client.post('/accounts/login/', {
            'login': 'loadtest@example.com',
            'password': 'loadtestpass',
        })

    @task(3)
    def view_dashboard(self):
        self.client.get('/dashboard/')

    @task(2)
    def view_notifications(self):
        self.client.get('/notifications/')

    @task(2)
    def view_payment_methods(self):
        self.client.get('/payments/methods/')

    @task(2)
    def view_payment_history(self):
        self.client.get('/payments/history/')

    @task(1)
    def view_profile(self):
        self.client.get('/profile/profile/')

    @task(1)
    def view_session_history(self):
        self.client.get('/coaching/sessions/')

    @task(1)
    def check_unread_notifications(self):
        self.client.get('/notifications/unread-count/')


class SearchAndFilterUser(HttpUser):
    """Simulates a user searching and filtering through lists."""
    wait_time = between(3, 10)

    def on_start(self):
        self.client.post('/accounts/login/', {
            'login': 'searchtest@example.com',
            'password': 'searchtestpass',
        })

    @task(2)
    def search_coaches(self):
        self.client.get('/coaching/?q=valorant&experience=advanced')

    @task(2)
    def filter_tournaments(self):
        self.client.get('/tournaments/?status=open&game=1')

    @task(1)
    def filter_venues(self):
        self.client.get('/venues/?city=New+York&game=1')

    @task(1)
    def search_coaches_by_price(self):
        self.client.get('/coaching/?min_price=20&max_price=100')
