# SAO Contact Manager - Desktop Version

**Secure, Isolated Desktop Application for State Attorney's Office**

## 🖥️ Desktop Features

- **Complete Offline Operation** - No internet required after installation
- **Enhanced Security** - Local-only access, no external network exposure
- **Data Protection** - Restricted folder permissions and encrypted storage
- **Random Port Assignment** - Different port each run for added security
- **No Telemetry** - All usage tracking disabled

## 🚀 Quick Start

### Option 1: Automated Installation (Recommended)
1. **Run the installer**: Double-click `install_desktop.bat`
2. **Start the application**: Double-click `run_sao_manager.bat`
3. **Access in browser**: Opens automatically at `http://localhost:[random-port]`

### Option 2: PowerShell (Enhanced Security)
1. **Right-click on `run_sao_manager.ps1`**
2. **Select "Run with PowerShell"**
3. **If prompted, allow execution**

### Option 3: Manual Setup
```bash
pip install streamlit pandas PyMuPDF
streamlit run sao_contact_manager.py --server.address localhost
```

## 🔒 Security Features

### Network Isolation
- **Localhost Only**: Application only accepts connections from your computer
- **No External Access**: Cannot be accessed from network or internet
- **Random Ports**: Different port used each session
- **CORS Disabled**: No cross-origin requests allowed

### Data Protection
- **Restricted Permissions**: Database and logs accessible only to your user account
- **Local Storage**: All data stays on your computer
- **No Cloud Sync**: No automatic uploading or syncing
- **Encrypted Sessions**: Secure session management

### Privacy
- **No Telemetry**: Usage statistics collection disabled
- **No Analytics**: No tracking or monitoring
- **Minimal Logging**: Only security-relevant events logged
- **Private by Default**: All settings optimized for privacy

## 📁 File Structure

```
SAO_Contact_Manager/
├── sao_contact_manager.py      # Main application
├── auth_system.py              # Authentication system
├── auth_ui.py                  # Authentication interface
├── admin_ui.py                 # Admin panel
├── desktop_config.py           # Desktop configuration
├── run_sao_manager.bat         # Windows launcher
├── run_sao_manager.ps1         # PowerShell launcher
├── install_desktop.bat         # Desktop installer
├── data/                       # Application data (created on first run)
│   └── sao_contacts.db        # Contact database
├── logs/                       # Application logs
├── .streamlit/                 # Streamlit configuration
│   └── config.toml            # Desktop-optimized settings
└── PDFs/                      # PDF imports (optional)
```

## 🛠️ System Requirements

### Minimum Requirements
- **OS**: Windows 10+ (PowerShell support recommended)
- **Python**: 3.8 or higher
- **RAM**: 2GB available memory
- **Storage**: 100MB free disk space
- **Browser**: Any modern web browser (Chrome, Firefox, Edge)

### Recommended Setup
- **OS**: Windows 11 with PowerShell 7+
- **Python**: 3.11+ (latest stable)
- **RAM**: 4GB+ available memory  
- **Storage**: 500MB+ free disk space
- **Browser**: Chrome or Edge (best Streamlit compatibility)

## 🔧 Configuration

### Desktop Mode Settings
The application automatically configures these security settings:

```toml
[server]
address = "localhost"          # Local access only
enableCORS = false            # No cross-origin requests
enableXsrfProtection = true   # CSRF protection enabled
maxUploadSize = 10            # Limit file uploads

[browser]
gatherUsageStats = false      # No telemetry

[global]  
developmentMode = false       # Production security mode
logLevel = "warning"          # Minimal logging
```

### Custom Configuration
To modify settings, edit `.streamlit/config.toml` or set environment variables:

```bash
set STREAMLIT_SERVER_PORT=8502
set STREAMLIT_SERVER_ADDRESS=localhost
```

## 📋 Usage Instructions

### First Time Setup
1. **Install** using `install_desktop.bat`
2. **Register** your @pd15.org or @pd15.state.fl.us account
3. **Verify** your email address
4. **Import** contact data via CSV or PDF upload

### Daily Usage
1. **Launch** using desktop shortcut or batch file
2. **Login** with email address
3. **Request PIN** sent to your email
4. **Enter PIN** to access the system
5. **Search, manage, and export** contact data

### Admin Tasks (Admins Only)
1. **Access Admin Tab** (👑 icon)
2. **Manage Users** - promote, demote, delete
3. **View Statistics** - registration trends, activity
4. **Monitor System** - user verification status

## 🔍 Troubleshooting

### Common Issues

**"Python not found"**
- Install Python from https://python.org
- Ensure "Add to PATH" was checked during installation
- Restart command prompt/PowerShell

**"Port already in use"**
- Application uses random ports automatically
- If issues persist, restart the launcher

**"Permission denied"**
- Run installer as Administrator
- Check folder permissions on data/ directory

**Browser doesn't open**
- Manually navigate to displayed URL
- Try different browser (Chrome recommended)

**Database locked**  
- Close any other instances of the application
- Restart your computer if needed

### Performance Optimization

**Slow startup**
- Close unnecessary programs
- Ensure adequate free disk space
- Consider SSD storage for better performance

**High memory usage**
- Limit concurrent browser tabs
- Close application when not in use
- Monitor system resources

## 🛡️ Security Best Practices

### For Administrators
- **Run as Administrator** for enhanced security features
- **Regular Backups** of the database file
- **Monitor User Activity** through admin panel
- **Review Logs** periodically for issues

### For Users
- **Keep Application Updated** with latest version
- **Use Strong Passwords** for initial account setup
- **Log Out** when finished using the system
- **Report Issues** to IT department immediately

### For IT Departments
- **Firewall Rules** - Ensure localhost-only access
- **Antivirus Exclusions** - Add application folder if needed
- **Network Monitoring** - Monitor for any external connections
- **Regular Audits** - Review user access and admin privileges

## 📞 Support

**Technical Issues**: Contact your IT department
**Account Problems**: Contact your system administrator
**Bug Reports**: Document and report to development team

---

**Internal Use Only - State Attorney's Office, 15th Judicial Circuit**
**Confidential and Privileged Information**