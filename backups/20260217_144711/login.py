"""
Login & Sign Up Page
Dedicated authentication page for MITR chatbot.
"""

import streamlit as st
from services.auth import sign_in, sign_up, is_logged_in
from services.logger import get_logger
from services.theme import apply_theme

logger = get_logger(__name__)

# Page config
st.set_page_config(
    page_title="Login - MITR",
    page_icon="🔐",
    layout="centered"
)
apply_theme("Auto")
# Redirect if already logged in
if is_logged_in():
    st.success("✅ You're already logged in!")
    if st.button("Go to Chat →", use_container_width=True, type="primary"):
        st.switch_page("webapp.py")
    st.stop()

# ============================================================================
# HEADER
# ============================================================================

# Logo and title
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(
        "https://raw.githubusercontent.com/Taruni05/mitrchatbot/master/mitr_avatar.png",
        width=150
    )

st.title("🔐 Welcome to MITR")
st.markdown(
    "Your personal assistant for exploring Hyderabad\n\n"
    "Login or create an account to get started"
)

st.markdown("---")

# ============================================================================
# TAB SELECTION
# ============================================================================

tab1, tab2 = st.tabs(["🔑 Login", "✨ Sign Up"])

# ============================================================================
# LOGIN TAB
# ============================================================================

with tab1:
    st.subheader("Login to Your Account")
    
    with st.form("login_form"):
        email = st.text_input(
            "Email",
            placeholder="your.email@example.com",
            help="Enter your registered email"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            help="Your password"
        )
        
        remember_me = st.checkbox("Remember me", value=True)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submitted = st.form_submit_button(
                "🔓 Login",
                use_container_width=True,
                type="primary"
            )
        
        with col2:
            forgot = st.form_submit_button(
                "Forgot?",
                use_container_width=True
            )
        
        if submitted:
            if not email or not password:
                st.error("❌ Please enter both email and password")
            else:
                with st.spinner("Logging in..."):
                    success, result = sign_in(email, password)
                    
                    if success:
                        st.success("✅ Login successful!")
                        logger.info(f"User logged in: {email}")
                        
                        # Small delay for user to see success message
                        import time
                        time.sleep(0.5)
                        
                        # Redirect to chat
                        st.switch_page("webapp.py")
                    else:
                        st.error(f"❌ Login failed: {result}")
                        logger.warning(f"Login failed for {email}: {result}")
        
        if forgot:
            st.info("🔄 Password reset feature coming soon! Contact support for now.")
    
    # Demo credentials
    st.markdown("---")
    with st.expander("🎮 Try Demo Account"):
        st.markdown(
            "**Demo Credentials:**\n\n"
            "Email: `demo@mitr.app`\n\n"
            "Password: `demo123`\n\n"
            "*(Note: This is just an example - create your own account!)*"
        )

# ============================================================================
# SIGN UP TAB
# ============================================================================

with tab2:
    st.subheader("Create New Account")
    
    with st.form("signup_form"):
        new_email = st.text_input(
            "Email",
            placeholder="your.email@example.com",
            help="We'll never share your email"
        )
        
        new_password = st.text_input(
            "Password",
            type="password",
            placeholder="Create a strong password",
            help="Min 6 characters"
        )
        
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Re-enter your password"
        )
        
        agree_terms = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy",
            value=False
        )
        
        submitted = st.form_submit_button(
            "✨ Create Account",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            # Validation
            if not new_email or not new_password or not confirm_password:
                st.error("❌ Please fill in all fields")
            elif len(new_password) < 6:
                st.error("❌ Password must be at least 6 characters")
            elif new_password != confirm_password:
                st.error("❌ Passwords don't match")
            elif not agree_terms:
                st.error("❌ Please agree to the Terms of Service")
            else:
                with st.spinner("Creating account..."):
                    success, result = sign_up(new_email, new_password)
                    
                    if success:
                        st.success(
                            "✅ Account created successfully!\n\n"
                            "Please check your email to verify your account, "
                            "then login using the Login tab."
                        )
                        logger.info(f"New user signed up: {new_email}")
                    else:
                        st.error(f"❌ Sign up failed: {result}")
                        logger.warning(f"Sign up failed for {new_email}: {result}")
    
    # Password requirements
    st.markdown("---")
    with st.expander("🔒 Password Requirements"):
        st.markdown(
            "- Minimum 6 characters\n"
            "- Mix of letters and numbers recommended\n"
            "- Avoid common passwords\n"
            "- Don't reuse passwords from other sites"
        )

# ============================================================================
# FEATURES PREVIEW
# ============================================================================

st.markdown("---")
st.subheader("🌟 What You'll Get")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        "**🗣️ Voice Chat**\n\n"
        "Talk to MITR in English, Telugu, Hindi, or Urdu"
    )

with col2:
    st.markdown(
        "**🎯 Smart Suggestions**\n\n"
        "Get personalized recommendations based on your preferences"
    )

with col3:
    st.markdown(
        "**📊 Analytics**\n\n"
        "Track your exploration journey and favorites"
    )

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown(
        "**🗺️ Itinerary Planning**\n\n"
        "Create custom tours and routes"
    )

with col5:
    st.markdown(
        "**🍛 Food Discovery**\n\n"
        "Find the best biryani, cafes, and restaurants"
    )

with col6:
    st.markdown(
        "**🚇 Live Updates**\n\n"
        "Metro, bus, traffic, and weather info"
    )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🔒 Secure & Private**")
    st.caption("Your data is encrypted")

with col2:
    st.markdown("**⚡ Fast & Reliable**")
    st.caption("Instant responses")

with col3:
    st.markdown("**🆓 Free to Use**")
    st.caption("No hidden charges")

# Guest mode option
st.markdown("---")
st.info("💡 **Want to try without signing up?** Use Guest Mode (limited features)")

if st.button("👤 Continue as Guest", use_container_width=True):
    # Set guest session
    st.session_state.guest_mode = True
    st.session_state.logged_in = False
    st.switch_page("webapp.py")