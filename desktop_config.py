#!/usr/bin/env python3
"""
Desktop Configuration for SAO Contact Manager
Optimized for local, secure desktop use
"""

import os
import sys
import socket
from pathlib import Path

class DesktopConfig:
    def __init__(self):
        self.app_dir = Path(__file__).parent
        self.data_dir = self.app_dir / "data"
        self.logs_dir = self.app_dir / "logs"
        self.setup_directories()
    
    def setup_directories(self):
        """Create necessary directories for desktop use"""
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Set restrictive permissions on Windows
        if sys.platform == "win32":
            try:
                import stat
                os.chmod(self.data_dir, stat.S_IRWXU)  # Owner only
                os.chmod(self.logs_dir, stat.S_IRWXU)  # Owner only
            except:
                pass
    
    def get_available_port(self, start_port=8501):
        """Find an available port for the application"""
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        return start_port  # Fallback
    
    def set_security_env_vars(self):
        """Set environment variables for enhanced security"""
        security_vars = {
            'STREAMLIT_SERVER_HEADLESS': 'true',
            'STREAMLIT_BROWSER_GATHER_USAGE_STATS': 'false',
            'STREAMLIT_SERVER_ADDRESS': 'localhost',
            'STREAMLIT_SERVER_ENABLE_CORS': 'false',
            'STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION': 'true',
            'STREAMLIT_GLOBAL_DEVELOPMENT_MODE': 'false',
            'STREAMLIT_LOGGER_LEVEL': 'WARNING'
        }
        
        for key, value in security_vars.items():
            os.environ[key] = value
    
    def create_desktop_shortcut(self):
        """Create a desktop shortcut (Windows only)"""
        if sys.platform != "win32":
            return False
        
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "SAO Contact Manager.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = str(self.app_dir / "run_sao_manager.bat")
            shortcut.WorkingDirectory = str(self.app_dir)
            shortcut.IconLocation = str(self.app_dir / "sao_contact_manager.py")
            shortcut.Description = "SAO Contact Manager - Secure Desktop Version"
            shortcut.save()
            
            return True
        except ImportError:
            print("winshell not available - skipping shortcut creation")
            return False
        except Exception as e:
            print(f"Failed to create shortcut: {e}")
            return False
    
    def check_system_requirements(self):
        """Check if system meets requirements"""
        requirements = {
            'python_version': (3, 8),
            'memory_gb': 2,
            'disk_space_mb': 100
        }
        
        issues = []
        
        # Check Python version
        if sys.version_info < requirements['python_version']:
            issues.append(f"Python {requirements['python_version'][0]}.{requirements['python_version'][1]}+ required")
        
        # Check available memory (approximate)
        try:
            import psutil
            available_memory = psutil.virtual_memory().available / (1024**3)
            if available_memory < requirements['memory_gb']:
                issues.append(f"At least {requirements['memory_gb']}GB RAM recommended")
        except ImportError:
            pass  # psutil not available, skip memory check
        
        # Check disk space
        try:
            disk_usage = os.statvfs(self.app_dir) if hasattr(os, 'statvfs') else None
            if disk_usage:
                available_mb = (disk_usage.f_bavail * disk_usage.f_frsize) / (1024**2)
                if available_mb < requirements['disk_space_mb']:
                    issues.append(f"At least {requirements['disk_space_mb']}MB disk space required")
        except:
            pass
        
        return issues
    
    def setup_desktop_mode(self):
        """Configure the application for desktop mode"""
        print("Setting up SAO Contact Manager for desktop use...")
        
        # Check system requirements
        issues = self.check_system_requirements()
        if issues:
            print("System requirement warnings:")
            for issue in issues:
                print(f"  - {issue}")
            print()
        
        # Set security environment variables
        self.set_security_env_vars()
        
        # Get available port
        port = self.get_available_port()
        os.environ['STREAMLIT_SERVER_PORT'] = str(port)
        
        print(f"Configuration complete!")
        print(f"Application will run on: http://localhost:{port}")
        print(f"Data directory: {self.data_dir}")
        print(f"Logs directory: {self.logs_dir}")
        
        return port

if __name__ == "__main__":
    config = DesktopConfig()
    port = config.setup_desktop_mode()
    
    # Optional: Create desktop shortcut
    if "--create-shortcut" in sys.argv:
        if config.create_desktop_shortcut():
            print("Desktop shortcut created successfully!")
        else:
            print("Could not create desktop shortcut")
    
    print(f"\nTo start the application, run:")
    print(f"  streamlit run sao_contact_manager.py --server.port {port}")