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
    Get Supabase client with authenticated session.
    Auto-refreshes token if expired.
    
    Returns:
        Supabase client or None if not configured
    """
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        
        if not url or not key:
            logger.error("Supabase credentials not configured in secrets")
            return None
        
        client = create_client(url, key)
        
        # ✅ FIX: Set the auth session if user is logged in
        access_token = st.session_state.get("access_token")
        refresh_token = st.session_state.get("refresh_token")
        
        if access_token and refresh_token:
            try:
                # Try to set the session
                client.postgrest.auth(access_token)
                
                # ✅ NEW: Check if token is expired and refresh if needed
                # Try a simple query to test if token is valid
                try:
                    client.table("user_preferences").select("user_id").limit(1).execute()
                except Exception as e:
                    # If JWT expired, refresh the token
                    if "JWT expired" in str(e) or "PGRST303" in str(e):
                        logger.warning("🔄 JWT expired, refreshing token...")
                        
                        # Refresh the session
                        refresh_response = client.auth.refresh_session(refresh_token)
                        
                        if refresh_response.session:
                            # Update session state with new tokens
                            st.session_state.access_token = refresh_response.session.access_token
                            st.session_state.refresh_token = refresh_response.session.refresh_token
                            
                            # Set the new token
                            client.postgrest.auth(refresh_response.session.access_token)
                            logger.info("✅ Token refreshed successfully")
                        else:
                            logger.error("❌ Token refresh failed - user needs to re-login")
                            # Clear invalid session
                            sign_out()
                            return None
                    else:
                        # Some other error, re-raise it
                        raise e
                        
            except Exception as e:
                logger.error(f"Error setting auth session: {e}")
                # If anything fails, clear session and require re-login
                if "JWT expired" in str(e) or "PGRST303" in str(e):
                    logger.warning("⚠️ Session expired, user needs to re-login")
                    sign_out()
                    return None
        
        return client
        
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
    """Log in an existing user."""
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
            # CRITICAL: Store ALL session data
            st.session_state.user_id = res.user.id
            st.session_state.user_email = res.user.email
            st.session_state.logged_in = True
            st.session_state.access_token = res.session.access_token  # ← This is key
            st.session_state.refresh_token = res.session.refresh_token  # ← And this
            
            logger.info(f"✅ User logged in: {email} (ID: {res.user.id})")
            return True, res.user.id
        else:
            logger.warning(f"Login returned no session for {email}")
            return False, "Invalid email or password."
            
    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Login error for {email}: {e}", exc_info=True)
        
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
                     "refresh_token",  # ✅ ADD THIS
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
    if is_logged_in():
        return True
    
    # Show login required message
    st.warning("🔐 Please log in to access this page")
    
    # Show login form
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", use_container_width=True):
            if email and password:
                success, result = sign_in(email, password)
                if success:
                    st.success("✅ Logged in!")
                    st.rerun()
                else:
                    st.error(f"❌ {result}")
            else:
                st.error("Please enter email and password")
    
    with col2:
        st.subheader("Sign Up")
        st.caption("Create a new account")
        
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        
        if st.button("Sign Up", use_container_width=True):
            if new_email and new_password:
                success, result = sign_up(new_email, new_password)
                if success:
                    st.success("✅ Account created! Please log in.")
                else:
                    st.error(f"❌ {result}")
            else:
                st.error("Please enter email and password")
    
    return False

