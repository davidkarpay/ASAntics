# SAO Contact Manager

A secure web application for managing State Attorney's Office contact information with authentication and admin features.

## Features

### 🔐 Security & Authentication
- **Email Domain Restriction**: Only @pd15.org and @pd15.state.fl.us emails allowed
- **Email Verification**: Required for all new accounts
- **6-Digit PIN Login**: Secure PIN-based authentication after initial setup
- **Account Lockout**: Protection against brute force attacks
- **Admin Roles**: Designated administrators can manage users

### 📋 Contact Management
- **PDF/CSV Import**: Upload SAO phone lists in PDF or CSV format
- **Smart Search**: Search by name, position, division, or phone extension
- **Favorites System**: Save frequently accessed contacts
- **Division Filtering**: Filter by County Court, Felony Trial, Juvenile, etc.
- **Contact Export**: Download contact data as CSV

### 👑 Admin Features
- **User Management**: View, promote, demote, and delete users
- **System Statistics**: Monitor user registrations and activity
- **Access Control**: Admin-only features and protected operations

## Installation

1. Clone the repository:
```bash
git clone https://github.com/davidkarpay/ASAntics.git
cd ASAntics
```

2. Install dependencies:
```bash
pip install streamlit pandas pymupdf
```

3. Run the application:
```bash
streamlit run sao_contact_manager.py
```

## Usage

1. **First Time Setup**:
   - Register with your @pd15.org or @pd15.state.fl.us email
   - Check your email for verification code
   - Verify your email to activate your account

2. **Login**:
   - Enter your email address
   - Request a 6-digit PIN
   - Enter the PIN sent to your email

3. **Import Contacts**:
   - Use the sidebar to upload PDF or CSV phone lists
   - Click "Parse File" to process the upload
   - Confirm and save to database

4. **Search Contacts**:
   - Use the search bar to find contacts
   - Filter by division using checkboxes
   - Add frequently used contacts to favorites

## Admin Setup

To make a user an admin, use the provided script after they've registered:

```python
from auth_system import AuthSystem
auth = AuthSystem()
auth.make_admin("user@pd15.org")
```

## Security Notes

- All passwords are hashed with unique salts
- Login PINs expire after 15 minutes
- Email verification codes expire after 24 hours
- Failed login attempts trigger account lockout
- Session management through Streamlit's secure session state

## Technologies Used

- **Streamlit**: Web application framework
- **SQLite**: Database for contacts and user management
- **PyMuPDF**: PDF parsing and text extraction
- **Pandas**: Data manipulation and CSV handling

## License

Internal use only - State Attorney's Office, 15th Judicial Circuit