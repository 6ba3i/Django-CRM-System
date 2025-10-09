#!/usr/bin/env python
"""
Firebase initialization script for CRM system
Run this to set up Firebase collections and initial data
"""

import os
import sys
import django
from datetime import datetime
from decouple import config

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from core.firebase_config import FirebaseDB, FirebaseAuth, db

# Read configuration from .env
FIREBASE_CREDENTIALS_PATH = config('FIREBASE_CREDENTIALS_PATH', default='core/serviceAccountKey.json')
DEMO_EMAIL = config('DEMO_USER_EMAIL', default='admin@crm.com')
DEMO_PASSWORD = config('DEMO_USER_PASSWORD', default='admin123')
DEMO_NAME = config('DEMO_USER_NAME', default='Admin User')

def initialize_firebase():
    """Initialize Firebase with required collections and sample data"""
    
    print("🚀 Initializing Firebase CRM System...")
    
    if not db:
        print("❌ Firebase not connected. Please check your configuration.")
        print(f"   Expected credentials at: {FIREBASE_CREDENTIALS_PATH}")
        print("\n📝 Setup instructions:")
        print("1. Create a .env file from .env.template")
        print("2. Add your Firebase credentials path to .env")
        print("3. Ensure the credentials file exists")
        return False
    
    print("✅ Firebase connected successfully!")
    
    # Create sample data
    print("\n📝 Creating sample data...")
    
    # Sample customers
    sample_customers = [
        {
            'name': 'John Smith',
            'email': 'john.smith@techcorp.com',
            'phone': '+1 555-0101',
            'company': 'Tech Corp',
            'status': 'Active',
            'notes': 'Key client, interested in enterprise solutions',
            'industry': 'Technology',
            'lead_source': 'Website'
        },
        {
            'name': 'Jane Doe',
            'email': 'jane.doe@designstudio.com',
            'phone': '+1 555-0102',
            'company': 'Design Studio Inc',
            'status': 'Lead',
            'notes': 'Potential client for UI/UX services',
            'industry': 'Design',
            'lead_source': 'Referral'
        },
        {
            'name': 'Mike Johnson',
            'email': 'mike@startup.io',
            'phone': '+1 555-0103',
            'company': 'StartUp.io',
            'status': 'Prospect',
            'notes': 'Early-stage startup, budget conscious',
            'industry': 'SaaS',
            'lead_source': 'Cold Outreach'
        }
    ]
    
    print("Adding sample customers...")
    for customer in sample_customers:
        doc_id = FirebaseDB.add_record('customers', customer)
        if doc_id:
            print(f"  ✓ Added customer: {customer['name']}")
    
    # Sample deals
    sample_deals = [
        {
            'title': 'Enterprise Software License',
            'customer': 'Tech Corp',
            'value': 150000,
            'stage': 'Proposal',
            'probability': 75,
            'expected_close': '2025-02-28',
            'notes': 'Waiting for final approval from CFO',
            'status': 'Active'
        },
        {
            'title': 'Website Redesign Project',
            'customer': 'Design Studio Inc',
            'value': 25000,
            'stage': 'Qualified',
            'probability': 50,
            'expected_close': '2025-03-15',
            'notes': 'Initial discussions completed',
            'status': 'Active'
        },
        {
            'title': 'Cloud Migration Services',
            'customer': 'StartUp.io',
            'value': 35000,
            'stage': 'Negotiation',
            'probability': 85,
            'expected_close': '2025-01-31',
            'notes': 'Contract review in progress',
            'status': 'Active'
        }
    ]
    
    print("\nAdding sample deals...")
    for deal in sample_deals:
        doc_id = FirebaseDB.add_record('deals', deal)
        if doc_id:
            print(f"  ✓ Added deal: {deal['title']}")
    
    # Sample tasks
    sample_tasks = [
        {
            'title': 'Follow up with Tech Corp',
            'description': 'Check on proposal status',
            'assigned_to': 'admin@crm.com',
            'due_date': '2025-01-15',
            'priority': 'High',
            'status': 'Pending'
        },
        {
            'title': 'Prepare demo for Design Studio',
            'description': 'Create customized demo showing UI capabilities',
            'assigned_to': 'admin@crm.com',
            'due_date': '2025-01-20',
            'priority': 'Medium',
            'status': 'In Progress'
        }
    ]
    
    print("\nAdding sample tasks...")
    for task in sample_tasks:
        doc_id = FirebaseDB.add_record('tasks', task)
        if doc_id:
            print(f"  ✓ Added task: {task['title']}")
    
    # Create demo user
    print("\n👤 Creating demo user account...")
    result = FirebaseAuth.sign_up(DEMO_EMAIL, DEMO_PASSWORD, DEMO_NAME)
    if result['success']:
        print(f"  ✓ Demo user created: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    else:
        print("  ℹ️ Demo user may already exist")
    
    print("\n✨ Firebase initialization complete!")
    print("\n📋 Next steps:")
    print("1. Run: python manage.py migrate")
    print("   (This creates session tables only, not CRM data)")
    print("2. Run: python manage.py runserver")
    print("3. Visit: http://127.0.0.1:8000")
    print(f"4. Login with: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    
    return True

def check_firebase_connection():
    """Check if Firebase is properly configured"""
    print("\n🔍 Checking Firebase configuration...")
    
    if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
        print("\n❌ Firebase service account key not found!")
        print(f"   Expected at: {FIREBASE_CREDENTIALS_PATH}")
        print("\n📝 To set up Firebase:")
        print("1. Copy .env.template to .env")
        print("2. Go to https://console.firebase.google.com")
        print("3. Create a new project or select existing")
        print("4. Go to Project Settings > Service Accounts")
        print("5. Click 'Generate new private key'")
        print(f"6. Save the file as: {FIREBASE_CREDENTIALS_PATH}")
        print("7. Update your .env file with the correct path")
        print("8. Run this script again")
        return False
    
    if db:
        print("✅ Firebase is properly configured!")
        
        # Test by getting collections
        try:
            customers = FirebaseDB.get_records('customers')
            deals = FirebaseDB.get_records('deals')
            print(f"\n📊 Current data:")
            print(f"  • Customers: {len(customers)}")
            print(f"  • Deals: {len(deals)}")
        except Exception as e:
            print(f"⚠️ Could not read data: {e}")
        
        return True
    else:
        print("❌ Could not connect to Firebase")
        print("   Check your serviceAccountKey.json file")
        return False

def clear_all_data():
    """Clear all Firebase data (use with caution!)"""
    response = input("\n⚠️ This will DELETE all data! Are you sure? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    print("\n🗑️ Clearing all data...")
    
    collections = ['customers', 'deals', 'tasks', 'employees', 'interactions',
                  'sales_activities', 'pipeline_history']
    
    for collection in collections:
        try:
            records = FirebaseDB.get_records(collection)
            for record in records:
                if 'id' in record:
                    FirebaseDB.delete_record(collection, record['id'])
            print(f"  ✓ Cleared {collection}: {len(records)} records")
        except Exception as e:
            print(f"  ⚠️ Could not clear {collection}: {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Firebase CRM Setup')
    parser.add_argument('--clear', action='store_true', help='Clear all data')
    parser.add_argument('--check', action='store_true', help='Check connection only')
    args = parser.parse_args()
    
    if args.clear:
        clear_all_data()
    elif args.check:
        check_firebase_connection()
    else:
        if check_firebase_connection():
            response = input("\n📦 Initialize with sample data? (yes/no): ")
            if response.lower() == 'yes':
                initialize_firebase()