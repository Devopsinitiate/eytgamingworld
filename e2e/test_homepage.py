"""
Playwright E2E tests for the EYTGaming homepage and core navigation.

Run with: pytest e2e/ --base-url http://localhost:8000
"""
import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_homepage_loads(page: Page, base_url: str):
    page.goto(base_url)
    expect(page).to_have_title(re.compile(r'EYTGaming', re.IGNORECASE))
    expect(page.locator('h1')).to_be_visible()


@pytest.mark.e2e
def test_homepage_navigation_links(page: Page, base_url: str):
    page.goto(base_url)
    nav = page.locator('nav, header, .navbar')
    expect(nav).to_be_visible()
    links = nav.locator('a')
    link_count = links.count()
    assert link_count > 0


@pytest.mark.e2e
def test_login_page_accessible(page: Page, base_url: str):
    page.goto(f'{base_url}/accounts/login/')
    expect(page.locator('form')).to_be_visible()
    expect(page.locator('input[type="email"], input[name="login"]')).to_be_visible()
    expect(page.locator('input[type="password"]')).to_be_visible()


@pytest.mark.e2e
def test_coach_list_page(page: Page, base_url: str):
    page.goto(f'{base_url}/coaching/')
    expect(page).to_have_title(re.compile(r'Coach', re.IGNORECASE))


@pytest.mark.e2e
def test_tournament_list_page(page: Page, base_url: str):
    page.goto(f'{base_url}/tournaments/')
    expect(page.locator('body')).to_be_visible()


@pytest.mark.e2e
def test_not_found_page(page: Page, base_url: str):
    response = page.goto(f'{base_url}/nonexistent-page-xyz/', wait_until='networkidle')
    assert response.status == 404


@pytest.mark.e2e
def test_security_txt(page: Page, base_url: str):
    response = page.goto(f'{base_url}/.well-known/security.txt', wait_until='networkidle')
    assert response.status == 200
    content = page.content()
    assert 'Contact' in content or 'contact' in content


@pytest.mark.e2e
@pytest.mark.skip(reason='Requires live server with Stripe keys configured')
def test_payment_checkout_flow(page: Page, base_url: str, auth_user):
    """End-to-end payment flow: login -> add method -> checkout."""
    page.goto(f'{base_url}/accounts/login/')
    page.fill('input[name="login"]', 'test@example.com')
    page.fill('input[type="password"]', 'testpass123')
    page.click('button[type="submit"]')
    expect(page).to_have_url(re.compile(r'dashboard|profile|/'))

    page.goto(f'{base_url}/payments/methods/')
    expect(page.locator('body')).to_be_visible()
