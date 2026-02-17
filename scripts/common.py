#!/usr/bin/env python3
"""
Common utilities for Sam integrations.
Handles .env loading and shared config.
"""

import os
import sys
from pathlib import Path

def load_env():
    """Load environment variables from .env file."""
    # Look for .env in script directory or parent
    script_dir = Path(__file__).parent
    env_paths = [
        script_dir.parent / '.env',
        script_dir / '.env',
        Path.cwd() / '.env'
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            return True
    return False

def get_env(key, required=True):
    """Get environment variable, optionally required."""
    value = os.environ.get(key)
    if required and not value:
        print(f"Error: {key} not set in .env", file=sys.stderr)
        sys.exit(1)
    return value

def get_gmail_config():
    """Get Gmail IMAP configuration."""
    return {
        'email': get_env('GMAIL_EMAIL'),
        'password': get_env('GMAIL_APP_PASSWORD'),
        'imap_server': get_env('GMAIL_IMAP_SERVER', required=False) or 'imap.gmail.com',
        'smtp_server': get_env('GMAIL_SMTP_SERVER', required=False) or 'smtp.gmail.com'
    }

def get_google_service_account():
    """Get path to Google service account JSON."""
    return get_env('GOOGLE_SERVICE_ACCOUNT_PATH')

def get_lds_credentials():
    """Get LDS Church account credentials."""
    return {
        'username': get_env('LDS_USERNAME'),
        'password': get_env('LDS_PASSWORD')
    }

# Auto-load .env on import
load_env()
