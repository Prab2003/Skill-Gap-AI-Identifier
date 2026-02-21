"""Authentication UI components for local session access."""

import streamlit as st


def render_auth_page():
    """Render a local-only session access page."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# 🚀 SkillForge")
        st.markdown("### AI-Powered Skill Gap Identifier & Career Accelerator")
        st.markdown("---")
        st.info("🌐 Running in **Local Mode** — progress is saved for this session only.")

        username_input = st.text_input("Your Name (optional)", placeholder="e.g. Alex", key="local_name_input")

        if st.button("▶ Continue", use_container_width=True, type="primary"):
            username = username_input.strip() if username_input.strip() else "Guest"
            st.session_state.authenticated = True
            st.session_state.user = {
                "id": "local",
                "email": "local@session",
                "username": username,
            }
            st.session_state.profile_name = username
            st.rerun()

        st.markdown("---")
        st.caption("Cloud authentication has been removed from this build.")


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
            st.rerun()


def require_auth():
    """
    Check if user is authenticated. If not, show local access page and stop execution.
    Call this at the beginning of your app.
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        render_auth_page()
        st.stop()
