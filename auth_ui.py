"""Authentication UI components for login and signup."""

import re
import json
import os
import base64
import streamlit as st
from supabase_client import signup_user, login_user, supabase_enabled

# Path to store saved credentials (encrypted)
_CREDENTIALS_FILE = ".streamlit/saved_login.json"


def is_valid_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_username(username: str) -> bool:
    """Validate username format (alphanumeric and underscore, 3-20 chars)."""
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return bool(re.match(pattern, username))


def _simple_encrypt(text: str) -> str:
    """Simple base64 encoding (not cryptographically secure, but obscures data)."""
    return base64.b64encode(text.encode()).decode()


def _simple_decrypt(text: str) -> str:
    """Simple base64 decoding."""
    try:
        return base64.b64decode(text.encode()).decode()
    except:
        return ""


def save_credentials_to_storage(username: str, password: str):
    """Save credentials to a local file (base64 encoded)."""
    try:
        os.makedirs(os.path.dirname(_CREDENTIALS_FILE), exist_ok=True)
        data = {
            "username": _simple_encrypt(username),
            "password": _simple_encrypt(password)
        }
        with open(_CREDENTIALS_FILE, 'w') as f:
            json.dump(data, f)
    except Exception:
        pass  # Fail silently


def load_credentials_from_storage():
    """Load saved credentials from file."""
    try:
        if os.path.exists(_CREDENTIALS_FILE):
            with open(_CREDENTIALS_FILE, 'r') as f:
                data = json.load(f)
            return {
                "username": _simple_decrypt(data.get("username", "")),
                "password": _simple_decrypt(data.get("password", ""))
            }
    except Exception:
        pass
    return None


def clear_credentials_from_storage():
    """Clear saved credentials file."""
    try:
        if os.path.exists(_CREDENTIALS_FILE):
            os.remove(_CREDENTIALS_FILE)
    except Exception:
        pass


def render_auth_page():
    """Render the authentication page with login and signup tabs."""
    
    # Check if Supabase is enabled - if not, allow guest access
    if not supabase_enabled():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("# 🚀 SkillForge AI")
            st.markdown("### AI-Powered Skill Gap Identifier & Career Accelerator")
            st.markdown("---")
            st.info("🌐 Running in **Guest Mode** — your progress is saved for this session only.")
            
            guest_username = st.text_input("Your Name (optional)", placeholder="e.g. Alex", key="guest_name_input")
            
            if st.button("▶ Continue as Guest", use_container_width=True, type="primary"):
                username = guest_username.strip() if guest_username.strip() else "Guest"
                st.session_state.authenticated = True
                st.session_state.user = {
                    "id": "guest",
                    "email": "guest@local",
                    "username": username,
                }
                st.session_state.profile_name = username
                st.rerun()
            
            st.markdown("---")
            st.caption("To enable full account features, configure Supabase credentials in deployment settings.")
        st.stop()
        return
    
    # Center the auth form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Header
        st.markdown("# 🚀 SkillForge AI")
        st.markdown("### AI-Powered Skill Gap Identifier & Career Accelerator")
        st.markdown("---")
        
        # Tabs for login and signup
        tab1, tab2 = st.tabs(["🔐 Login", "✨ Sign Up"])
        
        # ─────────────────────────
        # LOGIN TAB
        # ─────────────────────────
        with tab1:
            st.markdown("#### Welcome Back!")
            
            with st.form("login_form", clear_on_submit=False):
                login_identifier = st.text_input(
                    "Email or Username",
                    placeholder="Enter your email or username",
                    key="login_identifier"
                )
                
                login_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password"
                )
                
                remember_me = st.checkbox("💾 Remember Me", value=True, 
                                         help="Keep me logged in on this browser")
                
                col_a, col_b, col_c = st.columns([1, 1, 1])
                with col_b:
                    submit_login = st.form_submit_button("🔐 Login", use_container_width=True)
                
                if submit_login:
                    if not login_identifier or not login_password:
                        st.error("Please enter both email/username and password")
                    else:
                        with st.spinner("Logging in..."):
                            success, user_data, message = login_user(login_identifier, login_password)
                            
                            if success:
                                st.success(message)
                                # Store user data in session state
                                st.session_state.authenticated = True
                                st.session_state.user = user_data
                                st.session_state.profile_name = user_data["username"]
                                
                                # Save credentials if Remember Me is checked
                                if remember_me:
                                    save_credentials_to_storage(login_identifier, login_password)
                                
                                st.rerun()
                            else:
                                st.error(message)
        
        # ─────────────────────────
        # SIGNUP TAB
        # ─────────────────────────
        with tab2:
            st.markdown("#### Create Your Account")
            
            with st.form("signup_form", clear_on_submit=True):
                signup_email = st.text_input(
                    "Email",
                    placeholder="your.email@example.com",
                    key="signup_email"
                )
                
                signup_username = st.text_input(
                    "Username",
                    placeholder="Choose a unique username (3-20 characters)",
                    key="signup_username",
                    help="Only letters, numbers, and underscores allowed"
                )
                
                signup_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="At least 6 characters",
                    key="signup_password"
                )
                
                signup_password_confirm = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter your password",
                    key="signup_password_confirm"
                )
                
                col_a, col_b, col_c = st.columns([1, 1, 1])
                with col_b:
                    submit_signup = st.form_submit_button("✨ Sign Up", use_container_width=True)
                
                if submit_signup:
                    # Validation
                    errors = []
                    
                    if not signup_email or not signup_username or not signup_password:
                        errors.append("All fields are required")
                    
                    if signup_email and not is_valid_email(signup_email):
                        errors.append("Invalid email format")
                    
                    if signup_username and not is_valid_username(signup_username):
                        errors.append("Username must be 3-20 characters (letters, numbers, underscore only)")
                    
                    if signup_password and len(signup_password) < 6:
                        errors.append("Password must be at least 6 characters")
                    
                    if signup_password != signup_password_confirm:
                        errors.append("Passwords do not match")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        with st.spinner("Creating account..."):
                            success, message = signup_user(signup_email, signup_username, signup_password)
                            
                            if success:
                                st.success(message)
                                st.info("👈 Please switch to the **Login** tab to sign in")
                            else:
                                st.error(message)
        
        # Footer
        st.markdown("---")
        st.markdown(
            "<p style='text-align: center; color: #888;'>Secure authentication powered by Supabase</p>",
            unsafe_allow_html=True
        )


def render_logout_button():
    """Render a logout button in the sidebar."""
    if st.session_state.get("authenticated", False):
        st.markdown("---")
        user = st.session_state.get("user", {})
        st.markdown(f"👤 **{user.get('username', 'User')}**")
        st.caption(f"📧 {user.get('email', '')}")
        
        if st.button("🚪 Logout", use_container_width=True):
            # Clear authentication state
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.profile_name = ""
            # Clear saved credentials
            clear_credentials_from_storage()
            st.rerun()


def require_auth():
    """
    Check if user is authenticated. If not, show auth page and stop execution.
    Attempts auto-login if credentials are saved.
    Call this at the beginning of your app.
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # Try auto-login if not authenticated
    if not st.session_state.authenticated:
        saved_creds = load_credentials_from_storage()
        if saved_creds and saved_creds.get("username") and saved_creds.get("password"):
            # Attempt auto-login with saved credentials
            success, user_data, message = login_user(saved_creds["username"], saved_creds["password"])
            if success:
                st.session_state.authenticated = True
                st.session_state.user = user_data
                st.session_state.profile_name = user_data["username"]
                # Successfully auto-logged in, continue to app
                return
            else:
                # Credentials invalid, clear them
                clear_credentials_from_storage()
    
    if not st.session_state.authenticated:
        render_auth_page()
        st.stop()
