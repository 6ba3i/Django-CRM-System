#!/usr/bin/env python
"""
Complete setup script for CRM database and initial data
Run this after installing requirements.txt
"""
import os
import sys
import django
from datetime import datetime, timedelta
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.contrib.auth.models import User, Group
from django.db import connection

def run_migrations():
    """Run database migrations"""
    print("🔄 Running migrations...")
    try:
        execute_from_command_line(['manage.py', 'makemigrations'])
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migrations completed successfully!")
    except Exception as e:
        print(f"❌ Migration error: {e}")
        sys.exit(1)

def create_superuser():
    """Create admin superuser"""
    from django.contrib.auth.models import User
    
    if User.objects.filter(username='admin').exists():
        print("ℹ️  Admin user already exists")
        return
    
    print("👤 Creating admin superuser...")
    User.objects.create_superuser(
        username='admin',
        email='admin@crm.local',
        password='admin123'
    )
    print("✅ Admin user created (username: admin, password: admin123)")

def create_groups():
    """Create user groups"""
    print("👥 Creating user groups...")
    groups = ['Sales', 'Manager', 'Admin']
    
    for group_name in groups:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f"  ✅ Created group: {group_name}")
        else:
            print(f"  ℹ️  Group already exists: {group_name}")

def create_sample_users():
    """Create sample sales users"""
    from django.contrib.auth.models import User, Group
    
    print("👥 Creating sample users...")
    
    sales_group = Group.objects.get_or_create(name='Sales')[0]
    
    sample_users = [
        {'username': 'john.smith', 'first_name': 'John', 'last_name': 'Smith', 'email': 'john@crm.local'},
        {'username': 'jane.doe', 'first_name': 'Jane', 'last_name': 'Doe', 'email': 'jane@crm.local'},
        {'username': 'mike.wilson', 'first_name': 'Mike', 'last_name': 'Wilson', 'email': 'mike@crm.local'},
    ]
    
    for user_data in sample_users:
        if not User.objects.filter(username=user_data['username']).exists():
            user = User.objects.create_user(
                username=user_data['username'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=user_data['email'],
                password='password123'
            )
            user.groups.add(sales_group)
            print(f"  ✅ Created user: {user_data['username']} (password: password123)")
        else:
            print(f"  ℹ️  User already exists: {user_data['username']}")

def create_sample_data():
    """Create sample customers and deals"""
    from customers.models import Customer, Interaction
    from sales.models import Deal, PipelineHistory, SalesActivity
    from django.contrib.auth.models import User
    
    print("📊 Creating sample data...")
    
    # Get users for assignment
    users = list(User.objects.filter(is_active=True))
    if not users:
        print("❌ No users found. Create users first.")
        return
    
    # Create sample customers
    sample_customers = [
        {'name': 'Acme Corporation', 'email': 'contact@acme.com', 'phone': '+1-555-0100', 'company': 'Acme Corp', 'status': 'Active'},
        {'name': 'TechStart Inc', 'email': 'info@techstart.com', 'phone': '+1-555-0101', 'company': 'TechStart', 'status': 'Lead'},
        {'name': 'Global Solutions', 'email': 'sales@globalsolutions.com', 'phone': '+1-555-0102', 'company': 'Global Solutions', 'status': 'Active'},
        {'name': 'Innovation Labs', 'email': 'hello@innovationlabs.com', 'phone': '+1-555-0103', 'company': 'Innovation Labs', 'status': 'Prospect'},
        {'name': 'Future Systems', 'email': 'contact@futuresystems.com', 'phone': '+1-555-0104', 'company': 'Future Systems', 'status': 'Active'},
        {'name': 'Digital Dynamics', 'email': 'info@digitaldynamics.com', 'phone': '+1-555-0105', 'company': 'Digital Dynamics', 'status': 'Lead'},
        {'name': 'CloudFirst', 'email': 'sales@cloudfirst.com', 'phone': '+1-555-0106', 'company': 'CloudFirst', 'status': 'Active'},
        {'name': 'DataTech Solutions', 'email': 'contact@datatech.com', 'phone': '+1-555-0107', 'company': 'DataTech', 'status': 'Prospect'},
        {'name': 'AI Innovations', 'email': 'hello@aiinnovations.com', 'phone': '+1-555-0108', 'company': 'AI Innovations', 'status': 'Active'},
        {'name': 'Quantum Computing Co', 'email': 'info@quantumco.com', 'phone': '+1-555-0109', 'company': 'Quantum Computing', 'status': 'Lead'},
    ]
    
    created_customers = []
    for customer_data in sample_customers:
        if not Customer.objects.filter(email=customer_data['email']).exists():
            customer_data['assigned_to'] = random.choice(users)
            customer_data['created_date'] = datetime.now() - timedelta(days=random.randint(1, 90))
            customer = Customer.objects.create(**customer_data)
            created_customers.append(customer)
            print(f"  ✅ Created customer: {customer.name}")
    
    # Create sample deals
    stages = ['Lead', 'Qualified', 'Proposal', 'Negotiation', 'Won', 'Lost']
    
    sample_deals = [
        {'title': 'Enterprise Software License', 'value': 150000},
        {'title': 'Cloud Migration Project', 'value': 85000},
        {'title': 'Annual Support Contract', 'value': 45000},
        {'title': 'Custom Development', 'value': 120000},
        {'title': 'Security Audit Services', 'value': 35000},
        {'title': 'Data Analytics Platform', 'value': 95000},
        {'title': 'Mobile App Development', 'value': 65000},
        {'title': 'Infrastructure Upgrade', 'value': 180000},
        {'title': 'Consulting Services', 'value': 55000},
        {'title': 'API Integration Project', 'value': 40000},
        {'title': 'Training Program', 'value': 25000},
        {'title': 'Database Optimization', 'value': 30000},
        {'title': 'Cybersecurity Package', 'value': 75000},
        {'title': 'AI Implementation', 'value': 200000},
        {'title': 'Automation Suite', 'value': 110000},
    ]
    
    customers = Customer.objects.all()
    if customers:
        for deal_data in sample_deals:
            deal_data['customer'] = random.choice(customers)
            deal_data['stage'] = random.choice(stages)
            deal_data['assigned_to'] = random.choice(users)
            deal_data['expected_close'] = datetime.now().date() + timedelta(days=random.randint(7, 90))
            deal_data['created_date'] = datetime.now() - timedelta(days=random.randint(1, 60))
            
            # Set probability based on stage
            stage_probability = {
                'Lead': 10,
                'Qualified': 25,
                'Proposal': 50,
                'Negotiation': 75,
                'Won': 100,
                'Lost': 0
            }
            deal_data['probability'] = stage_probability.get(deal_data['stage'], 25)
            
            # Set status based on stage
            if deal_data['stage'] == 'Won':
                deal_data['status'] = 'Won'
            elif deal_data['stage'] == 'Lost':
                deal_data['status'] = 'Lost'
            else:
                deal_data['status'] = 'Active'
            
            deal_data['notes'] = f"Initial discussion about {deal_data['title']}"
            
            deal = Deal.objects.create(**deal_data)
            print(f"  ✅ Created deal: {deal.title} - ${deal.value:,.0f}")
            
            # Create pipeline history
            PipelineHistory.objects.create(
                deal=deal,
                from_stage='New',
                to_stage=deal.stage,
                changed_by=deal.assigned_to,
                notes='Deal created'
            )
        
        # Create sample interactions
        interaction_types = ['Email', 'Call', 'Meeting', 'Demo']
        outcomes = ['Positive', 'Neutral', 'Negative']
        
        for customer in customers[:5]:  # Create interactions for first 5 customers
            for i in range(random.randint(1, 3)):
                Interaction.objects.create(
                    customer=customer,
                    type=random.choice(interaction_types),
                    description=f"Discussed product features and pricing options",
                    date=datetime.now() - timedelta(days=random.randint(1, 30)),
                    created_by=customer.assigned_to,
                    outcome=random.choice(outcomes)
                )
            print(f"  ✅ Created interactions for: {customer.name}")
    
    print("✅ Sample data created successfully!")

def collect_static():
    """Collect static files"""
    print("📁 Collecting static files...")
    try:
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("✅ Static files collected!")
    except Exception as e:
        print(f"⚠️  Static files warning: {e}")

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 CRM SETUP SCRIPT")
    print("=" * 60)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("\n⚠️  Warning: .env file not found!")
        print("Creating default .env file...")
        with open('.env', 'w') as f:
            f.write("""SECRET_KEY=django-insecure-dev-key-change-this-later
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
FIREBASE_CREDENTIALS_PATH=core/serviceAccountKey.json
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
""")
        print("✅ Created .env file - Please update Firebase settings if needed\n")
    
    # Run setup steps
    run_migrations()
    print()
    
    create_superuser()
    print()
    
    create_groups()
    print()
    
    create_sample_users()
    print()
    
    create_sample_data()
    print()
    
    collect_static()
    
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("\n📝 You can now login with:")
    print("  Admin: username='admin', password='admin123'")
    print("  Sales: username='john.smith', password='password123'")
    print("\n🌐 Run the server with:")
    print("  python manage.py runserver")
    print("\n🔗 Then visit: http://localhost:8000/")
    print("=" * 60)

if __name__ == "__main__":
    main()