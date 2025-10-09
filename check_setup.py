#!/usr/bin/env python
"""
Check if the Firebase CRM is properly configured
"""

import os
import sys
from pathlib import Path

def check_setup():
    """Verify all components are properly configured"""
    print("\n🔍 Firebase CRM Setup Checker")
    print("=" * 50)
    
    errors = []
    warnings = []
    success = []
    
    # 1. Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        success.append(f"✅ Python {python_version.major}.{python_version.minor} (OK)")
    else:
        errors.append(f"❌ Python {python_version.major}.{python_version.minor} (Need 3.8+)")
    
    # 2. Check .env file
    env_file = Path('.env')
    if env_file.exists():
        success.append("✅ .env file found")
        
        # Check for required variables
        try:
            from decouple import config
            
            # Check SECRET_KEY
            secret_key = config('SECRET_KEY', default='')
            if secret_key and secret_key != 'your-secret-key-here':
                success.append("✅ SECRET_KEY configured")
            else:
                warnings.append("⚠️ SECRET_KEY not properly set (run: python generate_secret_key.py)")
            
            # Check Firebase path
            firebase_path = config('FIREBASE_CREDENTIALS_PATH', default='')
            if firebase_path:
                if os.path.exists(firebase_path):
                    success.append(f"✅ Firebase credentials found at: {firebase_path}")
                else:
                    errors.append(f"❌ Firebase credentials not found at: {firebase_path}")
            else:
                errors.append("❌ FIREBASE_CREDENTIALS_PATH not set in .env")
            
            # Check Firebase project ID
            project_id = config('FIREBASE_PROJECT_ID', default='')
            if project_id and project_id != 'your-project-id':
                success.append(f"✅ Firebase Project ID: {project_id}")
            else:
                warnings.append("⚠️ FIREBASE_PROJECT_ID not set (optional but recommended)")
            
        except ImportError:
            errors.append("❌ python-decouple not installed (run: pip install python-decouple)")
    else:
        errors.append("❌ .env file not found (copy .env.template to .env)")
    
    # 3. Check required packages
    required_packages = [
        'django',
        'firebase_admin',
        'djangorestframework',
        'whitenoise',
        'decouple',
        'matplotlib',
        'pandas',
        'numpy'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            success.append(f"✅ {package} installed")
        except ImportError:
            errors.append(f"❌ {package} not installed")
    
    # 4. Check directory structure
    required_dirs = [
        'core',
        'customers', 
        'sales',
        'analytics',
        'templates',
        'static'
    ]
    
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            success.append(f"✅ Directory: {dir_name}/")
        else:
            warnings.append(f"⚠️ Missing directory: {dir_name}/")
    
    # 5. Check .gitignore
    gitignore = Path('.gitignore')
    if gitignore.exists():
        content = gitignore.read_text()
        if '.env' in content and 'serviceAccountKey.json' in content:
            success.append("✅ .gitignore properly configured")
        else:
            warnings.append("⚠️ .gitignore missing security entries")
    else:
        warnings.append("⚠️ No .gitignore file")
    
    # Print results
    print("\n📋 Setup Check Results:")
    print("-" * 50)
    
    if success:
        print("\n✅ Working:")
        for item in success:
            print(f"   {item}")
    
    if warnings:
        print("\n⚠️ Warnings:")
        for item in warnings:
            print(f"   {item}")
    
    if errors:
        print("\n❌ Errors (must fix):")
        for item in errors:
            print(f"   {item}")
    
    # Summary
    print("\n" + "=" * 50)
    if errors:
        print("❌ Setup INCOMPLETE - Fix errors above")
        print("\n📝 Next steps:")
        if '.env file not found' in str(errors):
            print("1. Copy .env.template to .env")
            print("2. Run: python generate_secret_key.py")
            print("3. Add your Firebase credentials")
        elif 'not installed' in str(errors):
            print("1. Run: pip install -r requirements.txt")
        elif 'Firebase credentials not found' in str(errors):
            print("1. Download Firebase service account key")
            print("2. Save to location specified in .env")
        print("4. Run this script again")
    elif warnings:
        print("✅ Setup READY (with warnings)")
        print("   You can run: python run_firebase_crm.py")
    else:
        print("✅ Setup PERFECT!")
        print("   Run: python run_firebase_crm.py")
    
    return len(errors) == 0

if __name__ == '__main__':
    if check_setup():
        sys.exit(0)
    else:
        sys.exit(1)