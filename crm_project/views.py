from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import json

from core.firebase_config import FirebaseDB, FirebaseAuth
from analytics.chart_generator import ChartGenerator

# Using different data structures as required
DASHBOARD_CARDS = [  # LIST of dashboard cards
    {'title': 'Total Customers', 'icon': 'users', 'color': '#4a90e2'},
    {'title': 'Active Deals', 'icon': 'briefcase', 'color': '#50c878'},
    {'title': 'Total Revenue', 'icon': 'dollar', 'color': '#ffd700'},
    {'title': 'Employees', 'icon': 'team', 'color': '#8a2be2'}
]

def login_view(request):
    """Firebase login with glassmorphism UI"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        result = FirebaseAuth.sign_in(email, password)
        
        if result['success']:
            # Create/get Django user
            user, created = User.objects.get_or_create(
                username=email.split('@')[0],
                email=email
            )
            login(request, user)
            
            # Store Firebase token in session (STRING)
            request.session['firebase_token'] = result['user']['idToken']
            request.session['firebase_uid'] = result['user']['localId']
            
            messages.success(request, '✅ Welcome back!')
            return redirect('dashboard')
        else:
            messages.error(request, f"❌ {result['error']}")
    
    return render(request, 'login.html')

def signup_view(request):
    """Firebase signup with glassmorphism UI"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name', '')
        
        result = FirebaseAuth.sign_up(email, password, name)
        
        if result['success']:
            user = User.objects.create_user(
                username=email.split('@')[0],
                email=email,
                password=password
            )
            login(request, user)
            
            messages.success(request, '✅ Account created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, f"❌ {result['error']}")
    
    return render(request, 'signup.html')

def dashboard_view(request):
    """Main dashboard with all metrics and charts"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get all data from Firebase (using LISTS and DICTIONARIES)
    customers = FirebaseDB.get_records('customers')
    employees = FirebaseDB.get_records('employees')
    deals = FirebaseDB.get_records('deals')
    tasks = FirebaseDB.get_records('tasks')
    
    # Calculate metrics using DICTIONARY
    metrics = {
        'customers': {
            'total': len(customers),
            'active': len([c for c in customers if c.get('status') == 'Active']),
            'new': len([c for c in customers if c.get('status') == 'Lead']),
        },
        'employees': {
            'total': len(employees),
            'departments': len(set([e.get('department', '') for e in employees])),  # Using SET
        },
        'deals': {
            'total': len(deals),
            'pipeline_value': sum([d.get('value', 0) for d in deals]),
            'won': len([d for d in deals if d.get('stage') == 'Closed Won']),
        },
        'tasks': {
            'total': len(tasks),
            'pending': len([t for t in tasks if t.get('status') != 'Completed']),
            'high_priority': len([t for t in tasks if t.get('priority') == 'High']),
        },
        'revenue': sum([d.get('value', 0) for d in deals if d.get('stage') == 'Closed Won'])
    }
    
    # Generate charts with matplotlib
    charts = {
        'customer_status': ChartGenerator.generate_pie_chart(
            [c.get('status', 'Unknown') for c in customers],
            'Customer Status Distribution'
        ),
        'deal_stages': ChartGenerator.generate_bar_chart(
            deals, 'stage', 'Deal Pipeline Stages'
        ),
        'revenue_timeline': ChartGenerator.generate_line_chart(
            deals, 'Monthly Revenue Trend'
        ),
        'department_distribution': ChartGenerator.generate_donut_chart(
            [e.get('department', 'Unknown') for e in employees],
            'Employees by Department'
        )
    }
    
    # Recent activities (LIST of DICTIONARIES)
    activities = []
    for customer in customers[:3]:
        activities.append({
            'type': 'customer',
            'message': f"New customer: {customer.get('name', 'Unknown')}",
            'time': 'Recently'
        })
    
    context = {
        'metrics': metrics,
        'charts': charts,
        'activities': activities,
        'dashboard_cards': DASHBOARD_CARDS,
    }
    
    return render(request, 'dashboard.html', context)

def customers_view(request):
    """Customer management with full CRUD"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    customers = FirebaseDB.get_records('customers')
    stats = FirebaseDB.get_statistics('customers')
    
    # Filter by status (using SET membership)
    status_filter = request.GET.get('status', '')
    if status_filter and status_filter in FirebaseDB.VALID_STATUSES:
        customers = [c for c in customers if c.get('status') == status_filter]
    
    return render(request, 'customers.html', {
        'customers': customers,
        'stats': stats,
        'statuses': list(FirebaseDB.VALID_STATUSES),  # Convert SET to LIST
        'current_filter': status_filter
    })

def employees_view(request):
    """Employee management"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    employees = FirebaseDB.get_records('employees')
    
    # Calculate department statistics using SET
    departments = set([e.get('department', 'Unknown') for e in employees])
    
    # Skills analysis using SET operations
    all_skills = set()
    for emp in employees:
        skills = emp.get('skills', [])
        if isinstance(skills, list):
            all_skills.update(skills)
    
    return render(request, 'employees.html', {
        'employees': employees,
        'departments': list(departments),
        'all_skills': list(all_skills),
        'total_salary': sum([e.get('salary', 0) for e in employees])
    })

def deals_view(request):
    """Deal/Opportunity management"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    deals = FirebaseDB.get_records('deals')
    customers = FirebaseDB.get_records('customers')
    
    # Calculate pipeline metrics
    pipeline_metrics = {
        'total_value': sum([d.get('value', 0) for d in deals]),
        'weighted_value': sum([d.get('value', 0) * d.get('probability', 0) / 100 for d in deals]),
        'by_stage': {}
    }
    
    # Group by stage using DICTIONARY
    for stage in FirebaseDB.VALID_STAGES:
        stage_deals = [d for d in deals if d.get('stage') == stage]
        pipeline_metrics['by_stage'][stage] = {
            'count': len(stage_deals),
            'value': sum([d.get('value', 0) for d in stage_deals])
        }
    
    return render(request, 'deals.html', {
        'deals': deals,
        'customers': customers,
        'stages': list(FirebaseDB.VALID_STAGES),
        'pipeline_metrics': pipeline_metrics
    })

def tasks_view(request):
    """Task management"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    tasks = FirebaseDB.get_records('tasks')
    employees = FirebaseDB.get_records('employees')
    
    # Sort tasks by priority and due date
    priority_order = {'High': 1, 'Medium': 2, 'Low': 3}
    tasks.sort(key=lambda x: (priority_order.get(x.get('priority', 'Low'), 4), 
                              x.get('due_date', '')))
    
    return render(request, 'tasks.html', {
        'tasks': tasks,
        'employees': employees,
        'priorities': list(FirebaseDB.VALID_PRIORITIES),
        'overdue_count': len([t for t in tasks if t.get('due_date', '') < datetime.now().isoformat()[:10]])
    })

@require_http_methods(["POST"])
def add_customer(request):
    """Add customer to Firebase"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    # Create customer DICTIONARY from form data
    customer_data = {
        'name': request.POST.get('name'),
        'email': request.POST.get('email'),
        'phone': request.POST.get('phone', ''),
        'company': request.POST.get('company', ''),
        'status': request.POST.get('status', 'Lead'),
        'value': float(request.POST.get('value', 0)),
        'notes': request.POST.get('notes', ''),
        'tags': request.POST.getlist('tags'),  # LIST of tags
        'created_by': request.user.email
    }
    
    doc_id = FirebaseDB.add_record('customers', customer_data)
    
    if doc_id:
        messages.success(request, '✅ Customer added successfully!')
        return redirect('customers')
    
    messages.error(request, '❌ Failed to add customer')
    return redirect('customers')

@require_http_methods(["POST"])
def add_employee(request):
    """Add employee to Firebase"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    employee_data = {
        'name': request.POST.get('name'),
        'email': request.POST.get('email'),
        'department': request.POST.get('department'),
        'role': request.POST.get('role'),
        'salary': float(request.POST.get('salary', 0)),
        'skills': request.POST.get('skills', '').split(','),  # Convert STRING to LIST
        'hire_date': request.POST.get('hire_date'),
        'created_by': request.user.email
    }
    
    doc_id = FirebaseDB.add_record('employees', employee_data)
    
    if doc_id:
        messages.success(request, '✅ Employee added successfully!')
        return redirect('employees')
    
    messages.error(request, '❌ Failed to add employee')
    return redirect('employees')

@require_http_methods(["POST"])
def add_deal(request):
    """Add deal to Firebase"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    deal_data = {
        'title': request.POST.get('title'),
        'customer': request.POST.get('customer'),
        'value': float(request.POST.get('value', 0)),
        'stage': request.POST.get('stage', 'New'),
        'probability': int(request.POST.get('probability', 50)),
        'expected_close': request.POST.get('expected_close'),
        'notes': request.POST.get('notes', ''),
        'created_by': request.user.email
    }
    
    doc_id = FirebaseDB.add_record('deals', deal_data)
    
    if doc_id:
        messages.success(request, '✅ Deal added successfully!')
        return redirect('deals')
    
    messages.error(request, '❌ Failed to add deal')
    return redirect('deals')

@require_http_methods(["POST"])
def add_task(request):
    """Add task to Firebase"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    task_data = {
        'title': request.POST.get('title'),
        'description': request.POST.get('description'),
        'assigned_to': request.POST.get('assigned_to'),
        'due_date': request.POST.get('due_date'),
        'priority': request.POST.get('priority', 'Medium'),
        'status': request.POST.get('status', 'Pending'),
        'created_by': request.user.email
    }
    
    doc_id = FirebaseDB.add_record('tasks', task_data)
    
    if doc_id:
        messages.success(request, '✅ Task added successfully!')
        return redirect('tasks')
    
    messages.error(request, '❌ Failed to add task')
    return redirect('tasks')

# Find the update_record function and replace it with:

@require_http_methods(["POST"])
def update_record(request, collection, doc_id):
    """Update any record in Firebase"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    # Get update data from POST (DICTIONARY)
    update_data = {key: value for key, value in request.POST.items() if key != 'csrfmiddlewaretoken'}
    
    success = FirebaseDB.update_record(collection, doc_id, update_data)
    
    if success:
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Failed to update'}, status=500)

@require_http_methods(["POST"])
def delete_record(request, collection, doc_id):
    """Delete any record from Firebase"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    success = FirebaseDB.delete_record(collection, doc_id)
    
    if success:
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Failed to delete'}, status=500)

@require_http_methods(["POST"])
def delete_record(request, collection, doc_id):
    """Delete any record from Firebase"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    success = FirebaseDB.delete_record(collection, doc_id)
    
    if success:
        messages.success(request, '✅ Record deleted successfully!')
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Failed to delete'}, status=500)

def analytics_view(request):
    """Advanced analytics with multiple matplotlib charts"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get all data
    customers = FirebaseDB.get_records('customers')
    employees = FirebaseDB.get_records('employees')
    deals = FirebaseDB.get_records('deals')
    tasks = FirebaseDB.get_records('tasks')
    
    # Generate 6+ different charts
    charts = {
        'customer_growth': ChartGenerator.generate_area_chart(customers, 'Customer Growth'),
        'revenue_by_month': ChartGenerator.generate_line_chart(deals, 'Revenue Trend'),
        'deal_probability': ChartGenerator.generate_scatter_chart(deals, 'Deal Probability vs Value'),
        'employee_salary': ChartGenerator.generate_horizontal_bar(employees, 'Salary Distribution'),
        'task_priority': ChartGenerator.generate_pie_chart([t.get('priority') for t in tasks], 'Task Priorities'),
        'department_performance': ChartGenerator.generate_stacked_bar(employees, deals, 'Department Performance')
    }
    
    # Complex statistics using all data structures
    stats = {
        'customers': FirebaseDB.get_statistics('customers'),
        'employees': FirebaseDB.get_statistics('employees'),
        'deals': FirebaseDB.get_statistics('deals'),
        'tasks': FirebaseDB.get_statistics('tasks')
    }
    
    return render(request, 'analytics.html', {
        'charts': charts,
        'stats': stats
    })

def logout_view(request):
    """Logout user"""
    logout(request)
    messages.success(request, '👋 See you soon!')
    return redirect('login')