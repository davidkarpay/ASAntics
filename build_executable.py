#!/usr/bin/env python3
"""
Build standalone executable for SAO Contact Manager
Creates a single .exe file that includes Python and all dependencies
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def install_pyinstaller():
    """Install PyInstaller"""
    print("Installing PyInstaller...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to install PyInstaller: {result.stderr}")
        return False
    return True

def create_spec_file():
    """Create PyInstaller spec file for the application"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['sao_contact_manager.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('auth_system.py', '.'),
        ('auth_ui.py', '.'),
        ('admin_ui.py', '.'),
        ('enhanced_pdf_parser.py', '.'),
        ('desktop_config.py', '.'),
        ('.streamlit/config.toml', '.streamlit/'),
    ],
    hiddenimports=[
        'streamlit',
        'pandas',
        'fitz',
        'sqlite3',
        'hashlib',
        'secrets',
        'datetime',
        'pathlib',
        'os',
        'sys'
    ],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy.random._pickle',
        'PIL',
        'tkinter'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SAO_Contact_Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='sao_icon.ico' if os.path.exists('sao_icon.ico') else None,
)
'''
    
    with open('sao_manager.spec', 'w') as f:
        f.write(spec_content.strip())
    
    print("Created PyInstaller spec file: sao_manager.spec")

def build_executable():
    """Build the standalone executable"""
    print("Building standalone executable...")
    print("This process may take several minutes...")
    
    # Run PyInstaller
    result = subprocess.run([
        sys.executable, "-m", "PyInstaller", 
        "--clean", 
        "sao_manager.spec"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Build failed: {result.stderr}")
        return False
    
    # Check if executable was created
    exe_path = Path("dist/SAO_Contact_Manager.exe")
    if exe_path.exists():
        print(f"✅ Executable created successfully: {exe_path}")
        print(f"File size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
        return True
    else:
        print("❌ Executable not found after build")
        return False

def create_portable_package():
    """Create a portable package with the executable and necessary files"""
    print("Creating portable package...")
    
    package_dir = Path("SAO_Contact_Manager_Portable")
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    package_dir.mkdir()
    
    # Copy executable
    exe_source = Path("dist/SAO_Contact_Manager.exe")
    if exe_source.exists():
        shutil.copy2(exe_source, package_dir / "SAO_Contact_Manager.exe")
    
    # Copy essential files
    files_to_copy = [
        "DESKTOP_README.md",
        "README.md",
        "requirements.txt",
        "CLAUDE.md"
    ]
    
    for file_name in files_to_copy:
        if Path(file_name).exists():
            shutil.copy2(file_name, package_dir)
    
    # Create launcher batch file
    launcher_content = '''@echo off
title SAO Contact Manager
echo Starting SAO Contact Manager...
echo.
echo Application will open in your default browser
echo To stop the application, close this window
echo.
SAO_Contact_Manager.exe
pause
'''
    
    with open(package_dir / "Start_SAO_Manager.bat", 'w') as f:
        f.write(launcher_content)
    
    # Create directories
    (package_dir / "data").mkdir(exist_ok=True)
    (package_dir / "logs").mkdir(exist_ok=True)
    
    print(f"✅ Portable package created: {package_dir}")
    print("\nPackage contents:")
    for item in sorted(package_dir.rglob("*")):
        if item.is_file():
            size = item.stat().st_size
            print(f"  {item.relative_to(package_dir)} ({size:,} bytes)")

def main():
    """Main build process"""
    print("=" * 50)
    print("   SAO Contact Manager - Executable Builder")
    print("=" * 50)
    print()
    
    # Check PyInstaller
    if not check_pyinstaller():
        if not install_pyinstaller():
            print("❌ Failed to install PyInstaller")
            return False
    
    print("✅ PyInstaller is available")
    
    # Create spec file
    create_spec_file()
    
    # Build executable
    if not build_executable():
        return False
    
    # Create portable package
    create_portable_package()
    
    print()
    print("🎉 Build completed successfully!")
    print()
    print("To distribute the application:")
    print("1. Zip the 'SAO_Contact_Manager_Portable' folder")
    print("2. Users can extract and run 'Start_SAO_Manager.bat'")
    print("3. No Python installation required on target machines")
    print()
    print("Security notes:")
    print("- Executable includes all dependencies")
    print("- No external network access required")
    print("- Database stays local to each installation")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("\nPress Enter to exit...")
        sys.exit(1)
    else:
        input("\nPress Enter to exit...")