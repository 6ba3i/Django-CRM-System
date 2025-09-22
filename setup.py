#!/usr/bin/env python
"""
Quick Setup Script for CRM Pro
Run this once to set up everything: python quick_setup.py
"""
import os
import sys
import subprocess
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def run_command(command, description):
    """Run a command and handle errors"""
    logger.info(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ {description} completed!")
            if result.stdout:
                logger.info(f"   Output: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"❌ {description} failed!")
            logger.error(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"❌ {description} failed with exception: {e}")
        return False

def check_firebase_config():
    """Check if Firebase is configured"""
    firebase_path = "core/serviceAccountkey.json"
    env_path = ".env"
    
    if not os.path.exists(firebase_path):
        logger.warning(f"⚠️  Firebase service account key not found at {firebase_path}")
        logger.info("   Please add your Firebase service account key to enable cloud features")
        return False
    
    if not os.path.exists(env_path):
        logger.warning("⚠️  .env file not found")
        logger.info("   Creating default .env file...")
        create_default_env()
        return False
    
    return True

def create_default_env():
    """Create default .env file"""
    env_content = """# Django Settings
SECRET_KEY=django-insecure-change-this-in-production-please
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Firebase Configuration (Update these with your Firebase project details)
FIREBASE_CREDENTIALS_PATH=core/serviceAccountkey.json
FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com

# Google OAuth (Get these from Google Cloud Console)
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    logger.info("✅ Created default .env file")

def main():
    """Main setup function"""
    logger.info("=" * 60)
    logger.info("🚀 CRM PRO - QUICK SETUP")
    logger.info("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("manage.py"):
        logger.error("❌ manage.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8+ required")
        sys.exit(1)
    
    logger.info(f"🐍 Python version: {sys.version}")
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python packages"):
        logger.error("Failed to install requirements. Please check your environment.")
        sys.exit(1)
    
    # Check Firebase configuration
    firebase_configured = check_firebase_config()
    
    # Run migrations
    if not run_command("python manage.py makemigrations", "Creating migrations"):
        logger.warning("Some migrations might already exist")
    
    if not run_command("python manage.py migrate", "Running database migrations"):
        logger.error("Database migration failed")
        sys.exit(1)
    
    # Create superuser (non-interactive)
    logger.info("👤 Creating admin superuser...")
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
        django.setup()
        
        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@crm.local', 'admin123')
            logger.info("✅ Admin user created (username: admin, password: admin123)")
        else:
            logger.info("ℹ️  Admin user already exists")
    except Exception as e:
        logger.error(f"❌ Failed to create superuser: {e}")
    
    # Create user groups
    try:
        from django.contrib.auth.models import Group
        groups = ['Sales', 'Manager', 'Admin']
        for group_name in groups:
            Group.objects.get_or_create(name=group_name)
        logger.info("✅ User groups created")
    except Exception as e:
        logger.error(f"❌ Failed to create groups: {e}")
    
    # Collect static files
    if not run_command("python manage.py collectstatic --noinput", "Collecting static files"):
        logger.warning("Static files collection had issues")
    
    # Final status
    logger.info("\n" + "=" * 60)
    logger.info("🎉 SETUP COMPLETE!")
    logger.info("=" * 60)
    
    if firebase_configured:
        logger.info("✅ Firebase: Configured")
    else:
        logger.info("⚠️  Firebase: Not configured (add serviceAccountkey.json)")
    
    logger.info("\n📝 Next steps:")
    logger.info("1. 🔧 Configure Google OAuth in Google Cloud Console")
    logger.info("2. 📱 Update .env with your Google OAuth credentials")
    logger.info("3. 🔥 Add your Firebase service account key")
    logger.info("4. 🚀 Run: python manage.py runserver")
    logger.info("5. 🌐 Visit: http://localhost:8000/")
    
    logger.info("\n🔑 Default admin login:")
    logger.info("   Username: admin")
    logger.info("   Password: admin123")
    
    logger.info("\n💡 Tips:")
    logger.info("   • Use the 'Initialize System' button on login page")
    logger.info("   • Login with Google OAuth for best experience")
    logger.info("   • Check Firebase console for cloud data")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()