#!/usr/bin/env python3
"""
Authentication UI components for SAO Contact Manager
"""

import streamlit as st
from auth_system import AuthSystem

def show_login_page():
    """Display login/registration page"""
    auth = AuthSystem()
    
    st.title("🔐 SAO Contact Manager - Login")
    st.markdown("---")
    
    # Create tabs for login and registration
    tab1, tab2, tab3, tab4 = st.tabs(["📧 Request PIN", "🆕 Register", "✅ Verify Email", "🔑 Reset Password"])
    
    with tab1:
        st.header("Request Login PIN")
        st.info("Enter your verified email address to receive a 6-digit PIN for secure access")
        
        with st.form("pin_request_form"):
            email = st.text_input("Email Address", placeholder="yourname@pd15.org")
            submit_pin = st.form_submit_button("Send PIN", type="primary")
            
            if submit_pin and email:
                success, message = auth.generate_login_pin(email)
                if success:
                    st.success(message)
                    st.session_state['pin_email'] = email
                else:
                    st.error(message)
        
        # PIN verification form
        if 'pin_email' in st.session_state:
            st.markdown("---")
            st.subheader("Enter Your PIN")
            
            with st.form("pin_verification_form"):
                pin = st.text_input("6-Digit PIN", max_chars=6, placeholder="123456")
                submit_verify = st.form_submit_button("Login", type="primary")
                
                if submit_verify and pin:
                    success, message, user_info = auth.verify_login_pin(st.session_state['pin_email'], pin)
                    if success:
                        st.session_state['authenticated'] = True
                        st.session_state['user_info'] = user_info
                        del st.session_state['pin_email']
                        st.success("Login successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error(message)
    
    with tab2:
        st.header("Register New Account")
        st.info("Only users with @pd15.org or @pd15.state.fl.us email addresses can register")
        
        with st.form("registration_form"):
            username = st.text_input("Username", placeholder="john.doe")
            email = st.text_input("Email Address", placeholder="john.doe@pd15.org")
            password = st.text_input("Password", type="password", placeholder="Create a secure password")
            password_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            
            # Password requirements
            st.caption("Password should be at least 8 characters long and contain a mix of letters, numbers, and symbols")
            
            submit_register = st.form_submit_button("Register", type="primary")
            
            if submit_register:
                # Validate inputs
                if not all([username, email, password, password_confirm]):
                    st.error("Please fill in all fields")
                elif password != password_confirm:
                    st.error("Passwords do not match")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters long")
                else:
                    success, message = auth.register_user(username, email, password)
                    if success:
                        st.success(message)
                        st.session_state['verification_email'] = email
                    else:
                        st.error(message)
    
    with tab3:
        st.header("Verify Email Address")
        st.info("Enter the 6-digit verification code sent to your email")
        
        with st.form("email_verification_form"):
            email = st.text_input("Email Address", 
                                value=st.session_state.get('verification_email', ''),
                                placeholder="yourname@pd15.org")
            verification_code = st.text_input("Verification Code", max_chars=6, placeholder="123456")
            
            submit_verify = st.form_submit_button("Verify Email", type="primary")
            
            if submit_verify and email and verification_code:
                success, message = auth.verify_email(email, verification_code)
                if success:
                    st.success(message)
                    if 'verification_email' in st.session_state:
                        del st.session_state['verification_email']
                else:
                    st.error(message)
    
    with tab4:
        st.header("Reset Password")
        st.info("Enter your email to receive a password reset code")
        
        # Step 1: Request reset code
        with st.form("password_reset_request_form"):
            reset_email = st.text_input("Email Address", placeholder="yourname@pd15.org")
            submit_reset_request = st.form_submit_button("Send Reset Code", type="primary")
            
            if submit_reset_request and reset_email:
                success, message = auth.request_password_reset(reset_email)
                if success:
                    st.success(message)
                    st.session_state['reset_email'] = reset_email
                else:
                    st.error(message)
        
        # Step 2: Reset password with code
        if 'reset_email' in st.session_state:
            st.markdown("---")
            st.subheader("Reset Your Password")
            
            with st.form("password_reset_form"):
                reset_code = st.text_input("Reset Code", max_chars=6, placeholder="123456")
                new_password = st.text_input("New Password", type="password", placeholder="Enter new password")
                confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")
                
                submit_reset = st.form_submit_button("Reset Password", type="primary")
                
                if submit_reset:
                    if not all([reset_code, new_password, confirm_password]):
                        st.error("Please fill in all fields")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters long")
                    else:
                        success, message = auth.reset_password(st.session_state['reset_email'], reset_code, new_password)
                        if success:
                            st.success(message)
                            del st.session_state['reset_email']
                        else:
                            st.error(message)

def show_user_profile():
    """Display user profile and logout option"""
    auth = AuthSystem()
    user = auth.get_current_user()
    
    if user:
        col1, col2 = st.columns([4, 1])
        with col1:
            username = user.get('username', 'User')
            email = user.get('email', '')
            is_admin = user.get('is_admin', False)
            admin_badge = " 👑**ADMIN**" if is_admin else ""
            st.markdown(f"👤 **{username}**{admin_badge} ({email})")
        with col2:
            if st.button("Logout", type="secondary"):
                auth.logout()
                st.rerun()

def require_authentication():
    """Decorator-like function to require authentication"""
    auth = AuthSystem()
    
    if not auth.is_user_authenticated():
        show_login_page()
        return False
    else:
        show_user_profile()
        return True