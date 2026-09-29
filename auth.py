"""
auth.py
--------
Handles password hashing and the signup/login logic.
This file doesn't know anything about Streamlit or the UI —
it just answers the questions "can this user sign up?" and
"is this the correct password for this user?"
Keeping it separate means we could later swap Streamlit for
a different UI without touching this file at all.
"""

import bcrypt
from db import create_user, get_user_by_username


def hash_password(plain_password):
    """
    Converts a plain-text password into a secure hash.
    bcrypt automatically adds a random 'salt' so that even if
    two users pick the same password, their stored hashes differ.
    We NEVER store the plain password anywhere.
    """
    password_bytes = plain_password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")  # store as a string in PostgreSQL (TEXT column)


def verify_password(plain_password, stored_hash):
    """
    Checks a plain-text password (typed at login) against the
    stored hash (saved at signup time). Returns True/False.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        stored_hash.encode("utf-8")
    )


def signup_user(username, password):
    """
    Attempts to create a new account.
    Returns a tuple: (success: bool, message: str)
    """
    if not username or not password:
        return False, "Username and password cannot be empty."

    if len(password) < 4:
        return False, "Password must be at least 4 characters."

    hashed = hash_password(password)
    success = create_user(username, hashed)

    if success:
        return True, "Account created successfully! Please log in."
    else:
        return False, "That username is already taken."


def login_user(username, password):
    """
    Attempts to log in a user.
    Returns a tuple: (success: bool, user_dict_or_None, message: str)
    """
    user = get_user_by_username(username)

    if user is None:
        return False, None, "No account found with that username."

    if verify_password(password, user["password_hash"]):
        return True, user, "Login successful!"
    else:
        return False, None, "Incorrect password."