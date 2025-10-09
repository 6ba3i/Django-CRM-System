#!/usr/bin/env python
"""
Simple run script for Firebase-only CRM
No database migrations needed for CRM data!
"""

import os
import sys
import subprocess
from pathlib import Path
from decouple import config

def check_env_setup():
    """Check if .env file exists and is configured"""
    env_file = Path('.env')
    env_template = Path('.env.template')
    
    if not env_file.exists():
        print("\n⚠️ No .env file found!")
        
        if env_template.exists():
            print("\n📝 Creating .env from template...")
            import shutil
            shutil.copy(env_template, env_file)
            print("✅ Created .env file")
            print("\n⚠️ IMPORTANT: Edit .env file with your settings:")
            print("   1. Generate a new SECRET_KEY")
            print("   2. Add your Firebase credentials path")
            print("   3. Update other settings as needed")
            print("\n🔧 After editing .env, run this script again.")
            return False
        else:
            print("\n❌ No .env.template found!")
            print("   Please create a .env file with required settings")
            return False
    
    # Check for Firebase credentials
    firebase_path = config('FIREBASE_CREDENTIALS_PATH', default='core/serviceAccountKey.json')
    if not os.path.exists(firebase_path):
        print(f"\n❌ Firebase credentials not found at: {firebase_path}")
        print("\n📝 Setup instructions:")
        print("1. Go to https://console.firebase.google.com")
        print("2. Create/select a project")
        print("3. Go to Project Settings > Service Accounts")
        print("4. Generate and download private key")
        print(f"5. Save as: {firebase_path}")
        print("6. Run this script again")
        return False
    
    return True

def run_crm():
    print("\n🚀 Starting Firebase CRM System...")
    print("=" * 50)
    
    # Check environment setup
    if not check_env_setup():
        return
    
    print("✅ Environment configured")
    print(f"✅ Firebase credentials found at: {config('FIREBASE_CREDENTIALS_PATH')}")
    
    # Create session database if needed (minimal SQLite just for sessions)
    db_name = config('DATABASE_NAME', default='db_sessions_only.sqlite3')
    if not os.path.exists(db_name):
        print("\n📦 Setting up session storage...")
        subprocess.run([sys.executable, 'manage.py', 'migrate', '--run-syncdb'])
        print("✅ Session storage ready")
    
    # Check if sample data exists
    print("\n🔍 Checking Firebase data...")
    subprocess.run([sys.executable, 'initialize_firebase.py', '--check'])
    
    # Ask to initialize if needed
    response = input("\n💾 Initialize sample data? (y/n): ")
    if response.lower() == 'y':
        subprocess.run([sys.executable, 'initialize_firebase.py'])
    
    # Start the server
    print("\n🌐 Starting development server...")
    print("=" * 50)
    print("\n📍 Access your CRM at: http://127.0.0.1:8000")
    
    # Get demo credentials from env
    demo_email = config('DEMO_USER_EMAIL', default='admin@crm.com')
    demo_password = config('DEMO_USER_PASSWORD', default='admin123')
    print(f"👤 Login with: {demo_email} / {demo_password}")
    print("\n✨ Press CTRL+C to stop the server\n")
    
    try:
        subprocess.run([sys.executable, 'manage.py', 'runserver'])
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")

if __name__ == '__main__':
    run_crm()