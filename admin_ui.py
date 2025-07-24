#!/usr/bin/env python3
"""
Admin UI components for SAO Contact Manager
"""

import streamlit as st
import pandas as pd
from auth_system import AuthSystem
from datetime import datetime

def show_admin_panel():
    """Display admin management panel"""
    auth = AuthSystem()
    
    if not auth.is_admin():
        st.error("⚠️ Admin access required")
        return
    
    st.header("👑 Admin Panel")
    st.markdown("---")
    
    # Create admin tabs
    tab1, tab2 = st.tabs(["👥 User Management", "📊 System Stats"])
    
    with tab1:
        show_user_management()
    
    with tab2:
        show_system_stats()

def show_user_management():
    """Show user management interface"""
    auth = AuthSystem()
    
    st.subheader("User Management")
    
    # Get all users
    success, users = auth.list_users()
    
    if not success:
        st.error(f"Failed to load users: {users}")
        return
    
    if not users:
        st.info("No users found")
        return
    
    # Display users in a table
    df_users = pd.DataFrame(users)
    df_users['created_at'] = pd.to_datetime(df_users['created_at']).dt.strftime('%Y-%m-%d %H:%M')
    df_users['last_login'] = pd.to_datetime(df_users['last_login'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
    df_users['last_login'] = df_users['last_login'].fillna('Never')
    
    st.dataframe(
        df_users,
        column_config={
            "username": "Username",
            "email": "Email",
            "is_verified": st.column_config.CheckboxColumn("Verified"),
            "is_admin": st.column_config.CheckboxColumn("Admin"),
            "created_at": "Created",
            "last_login": "Last Login"
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.markdown("---")
    
    # Admin actions
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Make Admin")
        with st.form("make_admin_form"):
            email_to_promote = st.selectbox(
                "Select user to promote",
                options=[u['email'] for u in users if not u['is_admin']],
                help="Select a user to give admin privileges"
            )
            
            if st.form_submit_button("Make Admin", type="primary"):
                if email_to_promote:
                    success, message = auth.make_admin(email_to_promote)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    with col2:
        st.subheader("Remove Admin")
        admin_users = [u['email'] for u in users if u['is_admin']]
        current_user_email = auth.get_current_user().get('email', '')
        
        # Don't allow removing own admin privileges
        removable_admins = [email for email in admin_users if email != current_user_email]
        
        with st.form("remove_admin_form"):
            email_to_demote = st.selectbox(
                "Select admin to demote",
                options=removable_admins,
                help="Select an admin to remove privileges (cannot remove yourself)"
            )
            
            if st.form_submit_button("Remove Admin", type="secondary"):
                if email_to_demote:
                    success, message = auth.remove_admin(email_to_demote)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    # Danger zone
    st.markdown("---")
    st.subheader("⚠️ Danger Zone")
    
    with st.expander("Delete User", expanded=False):
        st.warning("**Warning:** This action cannot be undone!")
        
        with st.form("delete_user_form"):
            current_user_email = auth.get_current_user().get('email', '')
            deletable_users = [u['email'] for u in users if u['email'] != current_user_email]
            
            email_to_delete = st.selectbox(
                "Select user to delete",
                options=deletable_users,
                help="Select a user to permanently delete (cannot delete yourself)"
            )
            
            confirm_delete = st.checkbox("I understand this action is permanent")
            
            if st.form_submit_button("Delete User", type="secondary"):
                if email_to_delete and confirm_delete:
                    success, message = auth.delete_user(email_to_delete)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                elif not confirm_delete:
                    st.error("Please confirm you understand this action is permanent")

def show_system_stats():
    """Show system statistics"""
    auth = AuthSystem()
    
    st.subheader("System Statistics")
    
    # Get user stats
    success, users = auth.list_users()
    
    if success:
        total_users = len(users)
        verified_users = len([u for u in users if u['is_verified']])
        admin_users = len([u for u in users if u['is_admin']])
        recent_logins = len([u for u in users if u['last_login'] and 
                           (datetime.now() - datetime.fromisoformat(u['last_login'])).days <= 7])
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", total_users)
        
        with col2:
            st.metric("Verified Users", verified_users)
        
        with col3:
            st.metric("Admin Users", admin_users)
        
        with col4:
            st.metric("Active (7 days)", recent_logins)
        
        # User registration over time
        if users:
            df_users = pd.DataFrame(users)
            df_users['created_date'] = pd.to_datetime(df_users['created_at']).dt.date
            
            registrations = df_users.groupby('created_date').size().reset_index(name='registrations')
            
            st.subheader("User Registrations Over Time")
            st.line_chart(registrations.set_index('created_date'))
    
    else:
        st.error(f"Failed to load system stats: {users}")

def require_admin():
    """Require admin privileges"""
    auth = AuthSystem()
    
    if not auth.is_user_authenticated():
        st.error("Authentication required")
        return False
    
    if not auth.is_admin():
        st.error("Admin privileges required")
        return False
    
    return True