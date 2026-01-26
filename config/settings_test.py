# config/settings_test.py
"""Test settings for EYTGaming.
This file overrides the default database configuration to use an in‑memory SQLite
database, which allows the test suite to run without requiring a running PostgreSQL
instance. It imports all settings from the main `config.settings` module and then
replaces the `DATABASES` entry.
"""

import os
from .settings import *  # noqa: F403,F401

# Override the default database to use SQLite for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Ensure the test runner uses the in‑memory database
# (Django does this automatically when using SQLite with ':memory:')
