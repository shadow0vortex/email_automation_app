"""
Build Script - Create Windows .exe executable
Uses PyInstaller to bundle the application with all dependencies
"""

import os
import sys
import shutil
import subprocess

def clean_build_directories():
    """Remove previous build directories"""
    print("🧹 Cleaning previous builds...")
    
    dirs_to_remove = ['build', 'dist', '__pycache__']
    files_to_remove = ['BulkEmailSender.spec']
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")
    
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"   Removed {file_name}")
    
    print("✓ Cleanup complete\n")

def create_resource_directories():
    """Create necessary resource directories"""
    print("📁 Creating resource directories...")
    
    directories = [
        'resources/icons',
        'resources/templates',
        'resources/sql',
        'config',
        'logs',
        'exports'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   Created {directory}/")
    
    print("✓ Directories created\n")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable with PyInstaller...")
    print("   This may take several minutes...\n")
    
    # PyInstaller command
    command = [
        'pyinstaller',
        '--onefile',                           # Single executable file
        '--windowed',                          # No console window
        '--name=BulkEmailSender',             # Executable name
        '--icon=resources/icons/app.ico',     # Application icon (if exists)
        
        # Add data files
        '--add-data=resources;resources',
        '--add-data=config;config',
        
        # Hidden imports (modules not auto-detected)
        '--hidden-import=psycopg2',
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--hidden-import=xlrd',
        '--hidden-import=jinja2',
        '--hidden-import=email.mime.multipart',
        '--hidden-import=email.mime.text',
        '--hidden-import=PyQt5.QtWebEngineWidgets',
        
        # Exclude unnecessary modules to reduce size
        '--exclude-module=matplotlib',
        '--exclude-module=scipy',
        '--exclude-module=numpy.testing',
        
        # Entry point
        'main.py'
    ]
    
    # Check if icon exists, if not remove icon parameter
    if not os.path.exists('resources/icons/app.ico'):
        command = [c for c in command if not c.startswith('--icon')]
        print("   ⚠️  No app icon found, building without icon")
    
    # Run PyInstaller
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("✓ Build successful\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        print(e.stderr)
        return False

def create_default_icon():
    """Create a simple default icon if none exists"""
    icon_path = 'resources/icons/app.ico'
    
    if not os.path.exists(icon_path):
        print("📷 Creating default application icon...")
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple icon
            img = Image.new('RGB', (256, 256), color='#007bff')
            draw = ImageDraw.Draw(img)
            
            # Draw text
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except:
                font = ImageFont.load_default()
            
            draw.text((128, 128), "📧", fill='white', anchor='mm', font=font)
            
            # Save as ICO
            img.save(icon_path, format='ICO')
            print(f"   ✓ Created {icon_path}\n")
        except Exception as e:
            print(f"   ⚠️  Could not create icon: {e}")
            print("   Building without custom icon\n")

def create_readme():
    """Create README file for the distribution"""
    readme_content = """
# Bulk Email Automation Software

## Quick Start Guide

### First Time Setup:
1. Run `BulkEmailSender.exe`
2. Follow the database setup wizard
3. Configure your Gmail SMTP settings

### Sending Emails:
1. **Upload Excel file** with recipient data (must have 'Email' column)
2. **Compose your email** using the built-in editor or upload HTML template
3. **Preview** your email to verify placeholders
4. **Click Send** and monitor progress in real-time

### Important Notes:

#### Gmail Configuration:
- You MUST use an App-specific password (not your regular Gmail password)
- Enable 2-Factor Authentication first
- Generate App Password at: https://myaccount.google.com/apppasswords

#### Rate Limits:
- Gmail: 500 emails per day (personal accounts)
- Google Workspace: 2,000 emails per day
- Recommended delay: 2-3 seconds between emails

#### Excel File Format:
Required columns:
- Email (required)
- Name (optional but recommended)

Optional columns:
- Company
- Phone
- Address
- Any custom fields

#### Placeholders:
Use {placeholder} format in your email, matching Excel column names:
- {name} - Recipient's name
- {email} - Recipient's email
- {company} - Company name
- {phone} - Phone number
- etc.

### Troubleshooting:

**Database Connection Issues:**
- Ensure PostgreSQL is installed and running
- Check firewall settings
- Verify credentials in database setup

**SMTP Authentication Errors:**
- Verify you're using App-specific password
- Check if "Less secure app access" is enabled (if using old Gmail account)
- Ensure 2FA is enabled

**Emails Not Sending:**
- Check internet connection
- Verify SMTP settings
- Check Gmail sending limits
- Review error logs

### Support:
For issues or questions, check the logs in the `logs/` directory.

### System Requirements:
- Windows 10 or later
- PostgreSQL 12 or later
- Internet connection
- 500MB free disk space

---
Version 1.0
© 2025 Email Automation Software
"""
    
    with open('README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("📝 Created README.txt\n")

def create_sample_excel():
    """Create a sample Excel file for testing"""
    print("📊 Creating sample Excel template...")
    
    try:
        import pandas as pd
        
        sample_data = {
            'Email': ['john.doe@example.com', 'jane.smith@example.com', 'bob.wilson@example.com'],
            'Name': ['John Doe', 'Jane Smith', 'Bob Wilson'],
            'Company': ['Acme Corp', 'Tech Solutions', 'Digital Marketing Inc'],
            'Phone': ['+1-555-0100', '+1-555-0200', '+1-555-0300']
        }
        
        df = pd.DataFrame(sample_data)
        df.to_excel('sample_recipients.xlsx', index=False)
        
        print("   ✓ Created sample_recipients.xlsx\n")
    except Exception as e:
        print(f"   ⚠️  Could not create sample Excel: {e}\n")

def copy_to_dist():
    """Copy additional files to dist directory"""
    print("📦 Copying additional files to distribution...")
    
    if os.path.exists('dist'):
        files_to_copy = [
            'README.txt',
            'sample_recipients.xlsx',
            'requirements.txt'
        ]
        
        for file in files_to_copy:
            if os.path.exists(file):
                shutil.copy(file, 'dist/')
                print(f"   Copied {file}")
        
        # Copy directories
        dirs_to_copy = ['resources']
        for dir in dirs_to_copy:
            if os.path.exists(dir):
                dest = os.path.join('dist', dir)
                if os.path.exists(dest):
                    shutil.rmtree(dest)
                shutil.copytree(dir, dest)
                print(f"   Copied {dir}/")
        
        print("✓ Files copied to dist/\n")

def create_installer_script():
    """Create a simple batch installer script"""
    installer_content = """@echo off
echo =====================================
echo Bulk Email Automation Software
echo Installer
echo =====================================
echo.

echo Checking prerequisites...
echo.

:: Check if PostgreSQL is installed
where psql >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: PostgreSQL not found!
    echo Please install PostgreSQL before running this application.
    echo Download from: https://www.postgresql.org/download/
    echo.
    pause
)

echo Creating directories...
if not exist "config" mkdir config
if not exist "logs" mkdir logs
if not exist "exports" mkdir exports

echo.
echo Installation complete!
echo.
echo To run the application, double-click BulkEmailSender.exe
echo.
pause
"""
    
    with open('dist/install.bat', 'w') as f:
        f.write(installer_content)
    
    print("📜 Created install.bat\n")

def main():
    """Main build process"""
    print("\n" + "="*60)
    print("   Bulk Email Automation Software - Build Script")
    print("="*60 + "\n")
    
    # Step 1: Clean
    clean_build_directories()
    
    # Step 2: Create directories
    create_resource_directories()
    
    # Step 3: Create icon
    create_default_icon()
    
    # Step 4: Create documentation
    create_readme()
    create_sample_excel()
    
    # Step 5: Build executable
    if not build_executable():
        print("\n❌ Build failed! Check errors above.")
        sys.exit(1)
    
    # Step 6: Copy additional files
    copy_to_dist()
    create_installer_script()
    
    # Final message
    print("="*60)
    print("✅ BUILD SUCCESSFUL!")
    print("="*60)
    print(f"\n📦 Your executable is ready:")
    print(f"   Location: {os.path.abspath('dist/BulkEmailSender.exe')}")
    print(f"\n📁 Distribution folder: {os.path.abspath('dist/')}")
    print("\n📝 Next steps:")
    print("   1. Navigate to the dist/ folder")
    print("   2. Run install.bat (optional)")
    print("   3. Double-click BulkEmailSender.exe")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Build error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)