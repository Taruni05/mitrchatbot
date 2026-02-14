"""
Authentication service using Supabase.
Handles login, signup, logout, and session management.
"""
import streamlit as st
from supabase import create_client, Client
from typing import Tuple, Optional
from services.logger import get_logger

logger = get_logger(__name__)


def get_supabase() -> Optional[Client]:
    """
    Get Supabase client.
    
    Returns:
        Supabase client or None if not configured
    """
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        
        if not url or not key:
            logger.error("Supabase credentials not configured in secrets")
            return None
        
        return create_client(url, key)
    except Exception as e:
        logger.error(f"Error creating Supabase client: {e}", exc_info=True)
        return None


def sign_up(email: str, password: str) -> Tuple[bool, str]:
    """
    Register a new user.
    
    Args:
        email: User's email address
        password: User's password (min 6 characters)
    
    Returns:
        Tuple of (success: bool, message: str)
        - (True, user_id) on success
        - (False, error_message) on failure
    """
    supabase = get_supabase()
    if not supabase:
        return False, "Database not configured. Please contact support."
    
    try:
        logger.info(f"Attempting signup for: {email}")
        
        res = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if res.user:
            logger.info(f"✅ New user registered: {email} (ID: {res.user.id})")
            return True, res.user.id
        else:
            logger.warning(f"Signup returned no user for {email}")
            return False, "Signup failed. Please try again."
            
    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Signup error for {email}: {e}", exc_info=True)
        
        # Provide user-friendly error messages
        if "already registered" in error_msg or "already exists" in error_msg:
            return False, "This email is already registered. Please login instead."
        elif "invalid email" in error_msg:
            return False, "Invalid email format. Please check and try again."
        elif "password" in error_msg:
            return False, "Password must be at least 6 characters long."
        else:
            return False, f"Registration failed: {str(e)}"


def sign_in(email: str, password: str) -> Tuple[bool, str]:
    """
    Log in an existing user.
    
    Args:
        email: User's email address
        password: User's password
    
    Returns:
        Tuple of (success: bool, message: str)
        - (True, user_id) on success
        - (False, error_message) on failure
    """
    supabase = get_supabase()
    if not supabase:
        return False, "Database not configured. Please contact support."
    
    try:
        logger.info(f"Attempting login for: {email}")
        
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if res.session and res.user:
            # Store in Streamlit session state
            st.session_state.user_id = res.user.id
            st.session_state.user_email = res.user.email
            st.session_state.logged_in = True
            st.session_state.access_token = res.session.access_token
            
            logger.info(f"✅ User logged in: {email} (ID: {res.user.id})")
            return True, res.user.id
        else:
            logger.warning(f"Login returned no session for {email}")
            return False, "Invalid email or password."
            
    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Login error for {email}: {e}", exc_info=True)
        
        # Provide user-friendly error messages
        if "invalid" in error_msg or "credentials" in error_msg:
            return False, "Invalid email or password."
        elif "email not confirmed" in error_msg:
            return False, "Please verify your email before logging in."
        else:
            return False, f"Login failed: {str(e)}"


def sign_out():
    """
    Log out the current user.
    Clears session state and signs out from Supabase.
    """
    user_email = st.session_state.get("user_email", "Unknown")
    
    supabase = get_supabase()
    if supabase:
        try:
            supabase.auth.sign_out()
            logger.info(f"✅ User signed out from Supabase: {user_email}")
        except Exception as e:
            logger.warning(f"Error signing out from Supabase: {e}")
    
    # Clear all auth-related session state
    keys_to_clear = ["user_id", "user_email", "logged_in", "access_token", 
                     "user_preferences", "messages"]
    
    for key in keys_to_clear:
        st.session_state.pop(key, None)
    
    logger.info(f"✅ Session cleared for: {user_email}")


def is_logged_in() -> bool:
    """
    Check if a user is currently logged in.
    
    Returns:
        True if logged in, False otherwise
    """
    return st.session_state.get("logged_in", False)


def get_current_user_id() -> Optional[str]:
    """
    Get the current user's ID.
    
    Returns:
        User ID string or None if not logged in
    """
    return st.session_state.get("user_id", None)


def get_current_user_email() -> Optional[str]:
    """
    Get the current user's email.
    
    Returns:
        User email string or None if not logged in
    """
    return st.session_state.get("user_email", None)


def require_login() -> bool:
    """
    Call this at the top of any page that needs authentication.
    Shows login UI if not logged in and stops further execution.
    
    Returns:
        True if logged in, False if not (and shows login page)
    
    Example:
        if not require_login():
            return  # Stop page execution
    """
    if not is_logged_in():
        show_login_page()
        return False
    return True


def show_login_page():
    """
    Render the login/signup UI inline.
    This completely replaces the page content with auth UI.
    """
    # Custom CSS for auth page
    st.markdown("""
    <style>
    .auth-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
    }
    .auth-title {
        text-align: center;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="auth-title">🏙️ Mitr</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center;">Your Hyderabad City Guide</p>', 
                unsafe_allow_html=True)
    st.markdown("---")
    
    # Tabs for Login and Signup
    tab_login, tab_signup = st.tabs(["🔑 Login", "✨ Sign Up"])
    
    # ─── LOGIN TAB ───────────────────────────────────────────────────
    with tab_login:
        st.markdown("### Welcome back!")
        
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Email",
                placeholder="your@email.com",
                key="login_email"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )
            
            submitted = st.form_submit_button(
                "Login",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                if not email or not password:
                    st.error("⚠️ Please enter both email and password")
                else:
                    with st.spinner("Logging in..."):
                        success, result = sign_in(email, password)
                    
                    if success:
                        st.success("✅ Logged in successfully!")
                        st.balloons()
                        # Small delay to show success message
                        import time
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"❌ {result}")
        
        st.markdown("---")
        st.caption("Don't have an account? Use the 'Sign Up' tab above.")
    
    # ─── SIGNUP TAB ──────────────────────────────────────────────────
    with tab_signup:
        st.markdown("### Create your account")
        
        with st.form("signup_form", clear_on_submit=False):
            new_email = st.text_input(
                "Email",
                placeholder="your@email.com",
                key="signup_email"
            )
            new_password = st.text_input(
                "Password",
                type="password",
                placeholder="At least 6 characters",
                key="signup_password",
                help="Minimum 6 characters"
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter password",
                key="signup_confirm"
            )
            
            submitted = st.form_submit_button(
                "Create Account",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                # Validation
                if not new_email or not new_password:
                    st.error("⚠️ Please fill all fields")
                elif len(new_password) < 6:
                    st.error("⚠️ Password must be at least 6 characters")
                elif new_password != confirm_password:
                    st.error("⚠️ Passwords do not match")
                else:
                    with st.spinner("Creating account..."):
                        success, result = sign_up(new_email, new_password)
                    
                    if success:
                        st.success(
                            "✅ Account created successfully!\n\n"
                            "Please check your email to verify your account, "
                            "then log in using the Login tab."
                        )
                        st.info(
                            "💡 **Next steps:**\n"
                            "1. Check your email inbox\n"
                            "2. Click the verification link\n"
                            "3. Return here and login"
                        )
                    else:
                        st.error(f"❌ {result}")
        
        st.markdown("---")
        st.caption("Already have an account? Use the 'Login' tab above.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #666;'>"
        "Made with ❤️ for Hyderabad"
        "</p>",
        unsafe_allow_html=True
    )