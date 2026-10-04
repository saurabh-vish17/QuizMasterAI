"""
utils/validators.py
-------------------
Validation utility functions for email, username, name, and password formats.
"""

import re
from typing import Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validates email format using regex.
    Returns (is_valid, error_message).
    """
    if not email or not email.strip():
        return False, "Email address cannot be empty."

    email = email.strip()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        return False, "Please enter a valid email address (e.g. user@domain.com)."

    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validates username format (3-20 characters, alphanumeric and underscores).
    Returns (is_valid, error_message).
    """
    if not username or not username.strip():
        return False, "Username cannot be empty."

    username = username.strip()
    if len(username) < 3 or len(username) > 20:
        return False, "Username must be between 3 and 20 characters."

    pattern = r"^[a-zA-Z0-9_]+$"
    if not re.match(pattern, username):
        return False, "Username can only contain letters, numbers, and underscores."

    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validates password strength (minimum 6 characters).
    Returns (is_valid, error_message).
    """
    if not password:
        return False, "Password cannot be empty."

    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    return True, ""


def validate_name(name: str) -> Tuple[bool, str]:
    """
    Validates full name field.
    Returns (is_valid, error_message).
    """
    if not name or not name.strip():
        return False, "Full name cannot be empty."

    if len(name.strip()) < 2:
        return False, "Full name must be at least 2 characters long."

    return True, ""
