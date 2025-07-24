#!/usr/bin/env python3
"""
Authentication system for SAO Contact Manager
Handles user registration, email verification, and PIN-based login
"""

import sqlite3
import hashlib
import secrets
import re
from datetime import datetime, timedelta
import streamlit as st

# Allowed email domains
ALLOWED_DOMAINS = ['@pd15.org', '@pd15.state.fl.us']

class AuthSystem:
    def __init__(self, db_path='sao_contacts.db'):
        self.db_path = db_path
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
        
    def validate_email_domain(self, email):
        """Validate that email belongs to authorized domains"""
        email = email.lower().strip()
        return any(email.endswith(domain) for domain in ALLOWED_DOMAINS)
    
    def validate_email_format(self, email):
        """Validate email format using regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def hash_password(self, password):
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password, hash_string):
        """Verify password against stored hash"""
        try:
            salt, stored_hash = hash_string.split(':')
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return password_hash == stored_hash
        except:
            return False
    
    def generate_verification_code(self):
        """Generate 6-digit verification code"""
        return f"{secrets.randbelow(900000) + 100000:06d}"
    
    def generate_pin(self):
        """Generate 6-digit PIN"""
        return f"{secrets.randbelow(900000) + 100000:06d}"
    
    def hash_pin(self, pin):
        """Hash PIN for storage"""
        salt = secrets.token_hex(8)
        pin_hash = hashlib.sha256((pin + salt).encode()).hexdigest()
        return f"{salt}:{pin_hash}"
    
    def verify_pin(self, pin, hash_string):
        """Verify PIN against stored hash"""
        try:
            salt, stored_hash = hash_string.split(':')
            pin_hash = hashlib.sha256((pin + salt).encode()).hexdigest()
            return pin_hash == stored_hash
        except:
            return False
    
    def send_verification_email(self, email, verification_code, email_type="registration"):
        """Send verification email (placeholder - needs SMTP configuration)"""
        # This is a placeholder function. In production, you'll need to configure SMTP
        # For now, we'll just display the code in the Streamlit interface
        
        if email_type == "registration":
            subject = "SAO Contact Manager - Email Verification"
            message = f"""
            Welcome to the SAO Contact Manager!
            
            Your verification code is: {verification_code}
            
            This code will expire in 24 hours. Please enter it in the application to complete your registration.
            
            If you did not request this verification, please ignore this email.
            """
        elif email_type == "pin":
            subject = "SAO Contact Manager - Login PIN"
            message = f"""
            Your login PIN is: {verification_code}
            
            This PIN will expire in 15 minutes. Use it to access the SAO Contact Manager.
            
            If you did not request this PIN, please secure your account immediately.
            """
        
        # For development/testing - display in Streamlit
        st.info(f"📧 **EMAIL SENT TO {email}**\\n\\n**Subject:** {subject}\\n\\n**Message:**\\n{message}")
        
        return True  # Return success for now
    
    def register_user(self, username, email, password):
        """Register a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Validate email domain
            if not self.validate_email_domain(email):
                return False, "Email must be from @pd15.org or @pd15.state.fl.us domain"
            
            # Validate email format
            if not self.validate_email_format(email):
                return False, "Invalid email format"
            
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = ? OR username = ?", (email, username))
            if cursor.fetchone():
                return False, "User with this email or username already exists"
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Generate verification token
            verification_token = secrets.token_urlsafe(32)
            verification_code = self.generate_verification_code()
            
            # Insert user
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, verification_token)
                VALUES (?, ?, ?, ?)
            """, (username, email, password_hash, verification_token))
            
            user_id = cursor.lastrowid
            
            # Insert verification code
            expires_at = datetime.now() + timedelta(hours=24)
            cursor.execute("""
                INSERT INTO email_verification (user_id, verification_code, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, verification_code, expires_at))
            
            conn.commit()
            
            # Send verification email
            self.send_verification_email(email, verification_code, "registration")
            
            return True, "Registration successful! Please check your email for verification code."
            
        except Exception as e:
            conn.rollback()
            return False, f"Registration failed: {str(e)}"
        finally:
            conn.close()
    
    def verify_email(self, email, verification_code):
        """Verify user email with verification code"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Find verification record
            cursor.execute("""
                SELECT ev.id, ev.user_id, ev.expires_at, u.email
                FROM email_verification ev
                JOIN users u ON ev.user_id = u.id
                WHERE u.email = ? AND ev.verification_code = ? AND ev.used = 0
            """, (email, verification_code))
            
            result = cursor.fetchone()
            if not result:
                return False, "Invalid verification code"
            
            ev_id, user_id, expires_at, _ = result
            
            # Check if expired
            if datetime.now() > datetime.fromisoformat(expires_at):
                return False, "Verification code has expired"
            
            # Mark as used and verify user
            cursor.execute("UPDATE email_verification SET used = 1 WHERE id = ?", (ev_id,))
            cursor.execute("UPDATE users SET is_verified = 1 WHERE id = ?", (user_id,))
            
            conn.commit()
            return True, "Email verified successfully! You can now log in."
            
        except Exception as e:
            conn.rollback()
            return False, f"Verification failed: {str(e)}"
        finally:
            conn.close()
    
    def generate_login_pin(self, email):
        """Generate and send login PIN"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Find verified user
            cursor.execute("SELECT id FROM users WHERE email = ? AND is_verified = 1", (email,))
            result = cursor.fetchone()
            
            if not result:
                return False, "User not found or not verified"
            
            user_id = result[0]
            
            # Generate PIN
            pin = self.generate_pin()
            pin_hash = self.hash_pin(pin)
            
            # Store PIN (expires in 15 minutes)
            expires_at = datetime.now() + timedelta(minutes=15)
            cursor.execute("""
                INSERT INTO login_pins (user_id, pin_hash, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, pin_hash, expires_at))
            
            conn.commit()
            
            # Send PIN via email
            self.send_verification_email(email, pin, "pin")
            
            return True, "Login PIN sent to your email"
            
        except Exception as e:
            conn.rollback()
            return False, f"Failed to generate PIN: {str(e)}"
        finally:
            conn.close()
    
    def is_account_locked(self, email):
        """Check if account is locked due to failed attempts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT failed_login_attempts, locked_until
                FROM users
                WHERE email = ?
            """, (email,))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            failed_attempts, locked_until = result
            
            # Check if account is currently locked
            if locked_until and datetime.now() < datetime.fromisoformat(locked_until):
                return True
            
            # Reset lock if time has passed
            if locked_until and datetime.now() >= datetime.fromisoformat(locked_until):
                cursor.execute("""
                    UPDATE users 
                    SET failed_login_attempts = 0, locked_until = NULL 
                    WHERE email = ?
                """, (email,))
                conn.commit()
                return False
            
            return failed_attempts >= self.max_failed_attempts
            
        except Exception:
            return False
        finally:
            conn.close()
    
    def record_failed_login(self, email):
        """Record failed login attempt and lock account if necessary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE users 
                SET failed_login_attempts = failed_login_attempts + 1
                WHERE email = ?
            """, (email,))
            
            # Check if account should be locked
            cursor.execute("SELECT failed_login_attempts FROM users WHERE email = ?", (email,))
            result = cursor.fetchone()
            
            if result and result[0] >= self.max_failed_attempts:
                locked_until = datetime.now() + timedelta(minutes=self.lockout_duration_minutes)
                cursor.execute("""
                    UPDATE users 
                    SET locked_until = ?
                    WHERE email = ?
                """, (locked_until, email))
            
            conn.commit()
        except Exception:
            conn.rollback()
        finally:
            conn.close()
    
    def reset_failed_attempts(self, email):
        """Reset failed login attempts on successful login"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE users 
                SET failed_login_attempts = 0, locked_until = NULL
                WHERE email = ?
            """, (email,))
            conn.commit()
        except Exception:
            conn.rollback()
        finally:
            conn.close()
    
    def verify_login_pin(self, email, pin):
        """Verify login PIN and authenticate user"""
        # Check if account is locked
        if self.is_account_locked(email):
            return False, f"Account is locked due to too many failed attempts. Try again in {self.lockout_duration_minutes} minutes.", None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Find user and valid PIN
            cursor.execute("""
                SELECT u.id, u.username, lp.id, lp.pin_hash, lp.expires_at
                FROM users u
                JOIN login_pins lp ON u.id = lp.user_id
                WHERE u.email = ? AND u.is_verified = 1 AND lp.used = 0
                ORDER BY lp.created_at DESC
                LIMIT 1
            """, (email,))
            
            result = cursor.fetchone()
            if not result:
                self.record_failed_login(email)
                return False, "Invalid email or no active PIN", None
            
            user_id, username, pin_id, pin_hash, expires_at = result
            
            # Check if expired
            if datetime.now() > datetime.fromisoformat(expires_at):
                self.record_failed_login(email)
                return False, "PIN has expired", None
            
            # Verify PIN
            if not self.verify_pin(pin, pin_hash):
                self.record_failed_login(email)
                return False, "Invalid PIN", None
            
            # Successful login - reset failed attempts
            self.reset_failed_attempts(email)
            
            # Mark PIN as used and update last login
            cursor.execute("UPDATE login_pins SET used = 1 WHERE id = ?", (pin_id,))
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now(), user_id))
            
            conn.commit()
            
            # Get admin status
            cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
            admin_result = cursor.fetchone()
            is_admin = admin_result[0] if admin_result else 0
            
            # Return user info for session
            return True, "Login successful", {
                'user_id': user_id,
                'username': username,
                'email': email,
                'is_admin': bool(is_admin)
            }
            
        except Exception as e:
            conn.rollback()
            return False, f"Login failed: {str(e)}", None
        finally:
            conn.close()
    
    def is_user_authenticated(self):
        """Check if user is authenticated in current session"""
        return 'authenticated' in st.session_state and st.session_state.authenticated
    
    def get_current_user(self):
        """Get current authenticated user info"""
        if self.is_user_authenticated():
            return st.session_state.get('user_info', {})
        return None
    
    def logout(self):
        """Logout current user"""
        for key in ['authenticated', 'user_info']:
            if key in st.session_state:
                del st.session_state[key]
    
    def request_password_reset(self, email):
        """Request password reset via email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if user exists and is verified
            cursor.execute("SELECT id FROM users WHERE email = ? AND is_verified = 1", (email,))
            result = cursor.fetchone()
            
            if not result:
                # Don't reveal if email exists or not for security
                return True, "If this email is registered, you will receive a reset code."
            
            user_id = result[0]
            
            # Generate reset code
            reset_code = self.generate_verification_code()
            
            # Store reset code (expires in 1 hour)
            expires_at = datetime.now() + timedelta(hours=1)
            cursor.execute("""
                INSERT INTO email_verification (user_id, verification_code, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, reset_code, expires_at))
            
            conn.commit()
            
            # Send reset email
            subject = "SAO Contact Manager - Password Reset"
            message = f"""
            A password reset was requested for your account.
            
            Your reset code is: {reset_code}
            
            This code will expire in 1 hour. Use it to reset your password.
            
            If you did not request this reset, please ignore this email.
            """
            
            st.info(f"📧 **EMAIL SENT TO {email}**\\n\\n**Subject:** {subject}\\n\\n**Message:**\\n{message}")
            
            return True, "If this email is registered, you will receive a reset code."
            
        except Exception as e:
            conn.rollback()
            return False, f"Failed to send reset code: {str(e)}"
        finally:
            conn.close()
    
    def reset_password(self, email, reset_code, new_password):
        """Reset password using reset code"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Find valid reset code
            cursor.execute("""
                SELECT ev.id, ev.user_id, ev.expires_at
                FROM email_verification ev
                JOIN users u ON ev.user_id = u.id
                WHERE u.email = ? AND ev.verification_code = ? AND ev.used = 0
                ORDER BY ev.created_at DESC
                LIMIT 1
            """, (email, reset_code))
            
            result = cursor.fetchone()
            if not result:
                return False, "Invalid reset code"
            
            ev_id, user_id, expires_at = result
            
            # Check if expired
            if datetime.now() > datetime.fromisoformat(expires_at):
                return False, "Reset code has expired"
            
            # Hash new password
            password_hash = self.hash_password(new_password)
            
            # Update password and mark reset code as used
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
            cursor.execute("UPDATE email_verification SET used = 1 WHERE id = ?", (ev_id,))
            
            conn.commit()
            return True, "Password reset successfully"
            
        except Exception as e:
            conn.rollback()
            return False, f"Password reset failed: {str(e)}"
        finally:
            conn.close()
    
    def is_admin(self, user_info=None):
        """Check if current user is an admin"""
        if user_info is None:
            user_info = self.get_current_user()
        return user_info and user_info.get('is_admin', False)
    
    def make_admin(self, email):
        """Make a user an admin (admin only function)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email,))
            if cursor.rowcount > 0:
                conn.commit()
                return True, f"User {email} is now an admin"
            else:
                return False, f"User {email} not found"
        except Exception as e:
            conn.rollback()
            return False, f"Failed to make admin: {str(e)}"
        finally:
            conn.close()
    
    def remove_admin(self, email):
        """Remove admin privileges from a user (admin only function)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE users SET is_admin = 0 WHERE email = ?", (email,))
            if cursor.rowcount > 0:
                conn.commit()
                return True, f"Admin privileges removed from {email}"
            else:
                return False, f"User {email} not found"
        except Exception as e:
            conn.rollback()
            return False, f"Failed to remove admin: {str(e)}"
        finally:
            conn.close()
    
    def list_users(self):
        """List all users (admin only function)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT username, email, is_verified, is_admin, created_at, last_login 
                FROM users 
                ORDER BY created_at DESC
            """)
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'username': row[0],
                    'email': row[1],
                    'is_verified': bool(row[2]),
                    'is_admin': bool(row[3]),
                    'created_at': row[4],
                    'last_login': row[5]
                })
            
            return True, users
            
        except Exception as e:
            return False, f"Failed to list users: {str(e)}"
        finally:
            conn.close()
    
    def delete_user(self, email):
        """Delete a user (admin only function)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get user ID first
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            result = cursor.fetchone()
            
            if not result:
                return False, f"User {email} not found"
            
            user_id = result[0]
            
            # Delete related records first
            cursor.execute("DELETE FROM login_pins WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM email_verification WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            return True, f"User {email} deleted successfully"
            
        except Exception as e:
            conn.rollback()
            return False, f"Failed to delete user: {str(e)}"
        finally:
            conn.close()