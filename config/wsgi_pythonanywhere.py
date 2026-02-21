import os
import sys

# ==========================================
# WSGI Configuration for PythonAnywhere
# ==========================================
# This file should be placed in the WSGI configuration
# section of your PythonAnywhere web app.
#
# IMPORTANT: Replace 'yourusername' with your actual
# PythonAnywhere username throughout this file!
# ==========================================

# Add your project directory to the sys.path
project_home = '/home/yourusername/eytgamingworld'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables from .env file
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(project_home) / '.env'
load_dotenv(dotenv_path=env_path)

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

# Activate virtual environment
# Path should match: /home/yourusername/.virtualenvs/eytgaming
activate_this = '/home/yourusername/.virtualenvs/eytgaming/bin/activate_this.py'
try:
    with open(activate_this) as file_:
        exec(file_.read(), dict(__file__=activate_this))
except FileNotFoundError:
    # Fallback if activate_this.py doesn't exist (for newer virtualenv versions)
    pass

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
