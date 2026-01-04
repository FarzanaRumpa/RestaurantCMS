"""
Hardcoded Super Admin Configuration
This file contains credentials for a permanent super admin account
that works even without database setup.

⚠️ IMPORTANT: This account has 100% ACCESS to EVERYTHING in the system:
- All restaurants and their data
- All users and permissions
- All orders and financial data
- All system settings and configurations
- API keys and integrations
- Registration requests
- User management
- Complete system control

This is the CORE MAIN ADMIN USER of this SaaS platform.

SECURITY NOTE: Change these credentials in production!
"""

# Hardcoded Super Admin Credentials
# This admin bypasses ALL permission checks and has FULL ACCESS
SUPER_ADMIN = {
    'email': 'cbssohel@gmail.com',
    'password': '9191Sqq',  # Plain text - will be checked directly
    'username': 'superadmin',
    'role': 'superadmin',
    'id': 0,  # Special ID to distinguish from database users
    'is_active': True
}

def check_hardcoded_admin(email_or_username, password):
    """
    Check if credentials match the hardcoded super admin

    Args:
        email_or_username: Email or username to check
        password: Password to verify

    Returns:
        dict: Admin info if credentials match, None otherwise
    """
    if (email_or_username == SUPER_ADMIN['email'] or
        email_or_username == SUPER_ADMIN['username']) and \
       password == SUPER_ADMIN['password']:
        return SUPER_ADMIN
    return None

