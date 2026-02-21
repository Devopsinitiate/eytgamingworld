#!/usr/bin/env python
"""
Pre-Deployment Checklist for EYTGaming
Run this script before deploying to check if everything is ready.
"""

import os
import sys
from pathlib import Path

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def check_mark(passed):
    return f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== EYTGaming Pre-Deployment Checklist ==={Colors.END}\n")
    
    issues = []
    warnings = []
    
    # Check 1: .env file exists
    env_exists = Path('.env').exists()
    print(f"{check_mark(env_exists)} .env file exists")
    if not env_exists:
        issues.append(".env file is missing. Create one from .env.production.template")
    
    # Check 2: Required environment variables
    if env_exists:
        from decouple import config
        required_vars = ['SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
        missing_vars = []
        
        for var in required_vars:
            try:
                value = config(var, default='__NOT_SET__')
                has_value = value != '__NOT_SET__' and value != ''
                print(f"{check_mark(has_value)} {var} is set")
                if not has_value:
                    missing_vars.append(var)
            except:
                print(f"{check_mark(False)} {var} is not set")
                missing_vars.append(var)
        
        if missing_vars:
            issues.append(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Check 3: DEBUG is False for production
    try:
        from decouple import config
        debug = config('DEBUG', default=True, cast=bool)
        is_production_ready = not debug
        print(f"{check_mark(is_production_ready)} DEBUG is False")
        if debug:
            warnings.append("DEBUG is True. Set DEBUG=False for production")
    except:
        print(f"{check_mark(False)} Unable to check DEBUG setting")
    
    # Check 4: requirements.txt exists
    req_exists = Path('requirements.txt').exists()
    print(f"{check_mark(req_exists)} requirements.txt exists")
    if not req_exists:
        issues.append("requirements.txt is missing")
    
    # Check 5: Static files configuration
    staticfiles_dir = Path('staticfiles')
    static_exists = Path('static').exists()
    print(f"{check_mark(static_exists)} static directory exists")
    if not static_exists:
        warnings.append("static directory not found.  Will be created by collectstatic")
    
    # Check 6: Media directory
    media_exists = Path('media').exists()
    print(f"{check_mark(media_exists)} media directory exists")
    if not media_exists:
        warnings.append("media directory not found. Create with: mkdir media")
    
    # Check 7: migrations directory exists for core apps
    core_apps = ['core', 'accounts', 'tournaments', 'teams', 'coaching', 
                 'venues', 'payments', 'notifications', 'dashboard', 'store']
    migrations_ok = True
    for app in core_apps:
        migrations_dir = Path(app) / 'migrations'
        if not migrations_dir.exists():
            print(f"{check_mark(False)} {app}/migrations directory missing")
            migrations_ok = False
            issues.append(f"{app}/migrations directory is missing")
    if migrations_ok:
        print(f"{check_mark(True)} All app migrations directories exist")
    
    # Check 8: WSGI file
    wsgi_exists = Path('config/wsgi.py').exists()
    print(f"{check_mark(wsgi_exists)} WSGI configuration exists")
    if not wsgi_exists:
        issues.append("config/wsgi.py is missing")
    
    # Check 9: .gitignore includes .env
    gitignore_path = Path('.gitignore')
    gitignore_ok = False
    if gitignore_path.exists():
        with open(gitignore_path) as f:
            content = f.read()
            gitignore_ok = '.env' in content
    print(f"{check_mark(gitignore_ok)} .env is in .gitignore")
    if not gitignore_ok:
        warnings.append(".env should be added to .gitignore to avoid committing secrets")
    
    # Check 10: MySQL client in requirements (for PythonAnywhere)
    mysql_client_ok = False
    if req_exists:
        with open('requirements.txt') as f:
            content = f.read()
            mysql_client_ok = 'mysqlclient' in content
    print(f"{check_mark(mysql_client_ok)} mysqlclient in requirements.txt")
    if not mysql_client_ok:
        warnings.append("mysqlclient not in requirements.txt. Add for MySQL support")
    
    # Summary
    print(f"\n{Colors.BOLD}Summary:{Colors.END}")
    
    if not issues and not warnings:
        print(f"{Colors.GREEN}✓ All checks passed! Ready for deployment.{Colors.END}")
        return 0
    
    if issues:
        print(f"\n{Colors.RED}{Colors.BOLD}Critical Issues ({len(issues)}):{Colors.END}")
        for issue in issues:
            print(f"  • {issue}")
    
    if warnings:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}Warnings ({len(warnings)}):{Colors.END}")
        for warning in warnings:
            print(f"  • {warning}")
    
    if issues:
        print(f"\n{Colors.RED}Please fix critical issues before deploying.{Colors.END}")
        return 1
    else:
        print(f"\n{Colors.YELLOW}You may proceed with caution.{Colors.END}")
        return 0

if __name__ == '__main__':
    sys.exit(main())
