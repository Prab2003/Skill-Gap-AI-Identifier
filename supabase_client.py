"""Tiny Supabase REST helper for Streamlit.

Relies only on httpx and st.secrets. Expected schema:
  table: user_state
  columns: profile_name (text, primary key), data (jsonb)
  
  table: users
  columns: id (uuid), email (text), password_hash (text), username (text), 
           created_at (timestamp), last_login (timestamp), is_active (boolean)

Configure in .streamlit/secrets.toml:
[supabase]
url = "https://YOUR_PROJECT_ID.supabase.co"
key = "YOUR_SERVICE_ROLE_OR_ANON_KEY"
"""

from __future__ import annotations

import json
import hashlib
import secrets
from typing import Any, Dict, Optional, Tuple

import httpx
import streamlit as st


@st.cache_resource(show_spinner=False)
def _client() -> httpx.Client | None:
    try:
        cfg = st.secrets.get("supabase", {})
    except Exception:
        # No secrets configured; treat Supabase as disabled
        return None
    url = cfg.get("url")
    key = cfg.get("key")
    if not url or not key:
        return None
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    return httpx.Client(base_url=url.rstrip("/"), headers=headers, timeout=10.0)


def supabase_enabled() -> bool:
    return _client() is not None


def load_user_state(profile_key: str) -> Dict[str, Any]:
    client = _client()
    if not client or not profile_key:
        return {}
    try:
        resp = client.get(
            "/rest/v1/user_state",
            params={"profile_name": f"eq.{profile_key}", "select": "data"},
        )
        if resp.status_code == 200:
            rows = resp.json()
            if rows:
                return rows[0].get("data", {}) or {}
    except Exception:
        # Fail silent; UI will remain local-only
        return {}
    return {}


def save_user_state(profile_key: str, data: Dict[str, Any]) -> bool:
    client = _client()
    if not client or not profile_key:
        return False
    payload = {"profile_name": profile_key, "data": data}
    try:
        resp = client.post(
            "/rest/v1/user_state",
            params={"on_conflict": "profile_name"},
            headers={"Prefer": "return=representation"},
            content=json.dumps([payload]),
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


# ──────────────────────────────────────────────
#  Authentication Functions
# ──────────────────────────────────────────────

def _hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """Hash a password with PBKDF2-HMAC-SHA256."""
    if salt is None:
        salt = secrets.token_hex(32)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return pwd_hash.hex(), salt


def _verify_password(stored_hash: str, password: str) -> bool:
    """Verify a password against its stored hash."""
    try:
        # Format: salt$hash
        parts = stored_hash.split('$')
        if len(parts) != 2:
            return False
        salt, hash_part = parts
        computed_hash, _ = _hash_password(password, salt)
        return computed_hash == hash_part
    except Exception:
        return False


def signup_user(email: str, username: str, password: str) -> Tuple[bool, str]:
    """
    Create a new user account.
    Returns: (success: bool, message: str)
    """
    client = _client()
    if not client:
        return False, "Database connection not available"
    
    # Basic validation
    if not email or not username or not password:
        return False, "All fields are required"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    # Hash the password
    pwd_hash, salt = _hash_password(password)
    stored_hash = f"{salt}${pwd_hash}"
    
    # Try to create the user
    payload = {
        "email": email.lower().strip(),
        "username": username.strip(),
        "password_hash": stored_hash,
        "is_active": True
    }
    
    try:
        resp = client.post(
            "/rest/v1/users",
            headers={"Prefer": "return=representation"},
            content=json.dumps([payload]),
        )
        
        if resp.status_code in (200, 201):
            return True, "Account created successfully! Please log in."
        elif resp.status_code == 409:
            error_text = resp.text.lower()
            if 'email' in error_text:
                return False, "Email already exists"
            elif 'username' in error_text:
                return False, "Username already exists"
            return False, "Account already exists"
        else:
            return False, f"Signup failed: {resp.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def login_user(identifier: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Authenticate a user by email/username and password.
    Returns: (success: bool, user_data: dict or None, message: str)
    """
    client = _client()
    if not client:
        return False, None, "Database connection not available"
    
    if not identifier or not password:
        return False, None, "Email/username and password are required"
    
    identifier = identifier.lower().strip()
    
    try:
        # Try to find user by email or username
        resp = client.get(
            "/rest/v1/users",
            params={
                "or": f"(email.eq.{identifier},username.eq.{identifier})",
                "select": "id,email,username,password_hash,is_active,last_login"
            }
        )
        
        if resp.status_code != 200:
            return False, None, "Login failed"
        
        users = resp.json()
        if not users:
            return False, None, "Invalid email/username or password"
        
        user = users[0]
        
        # Check if account is active
        if not user.get('is_active', True):
            return False, None, "Account is deactivated"
        
        # Verify password
        if not _verify_password(user['password_hash'], password):
            return False, None, "Invalid email/username or password"
        
        # Update last login
        try:
            client.patch(
                "/rest/v1/users",
                params={"id": f"eq.{user['id']}"},
                content=json.dumps({"last_login": "now()"}),
            )
        except:
            pass  # Non-critical if this fails
        
        # Return user data (without password hash)
        user_data = {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
            "last_login": user.get("last_login")
        }
        
        return True, user_data, "Login successful!"
        
    except Exception as e:
        return False, None, f"Error: {str(e)}"


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user information by ID."""
    client = _client()
    if not client or not user_id:
        return None
    
    try:
        resp = client.get(
            "/rest/v1/users",
            params={
                "id": f"eq.{user_id}",
                "select": "id,email,username,created_at,last_login,is_active"
            }
        )
        
        if resp.status_code == 200:
            users = resp.json()
            return users[0] if users else None
    except Exception:
        return None
    
    return None
