# Customer views and logic
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.contrib import messages
from datetime import datetime, timedelta
import json

from .models import Customer, Interaction, CustomerTag
from .forms import CustomerForm, InteractionForm, CustomerSearchForm
from core.firebase_config import FirebaseManager
from core.decorators import role_required, log_activity, validate_json_request
from core.utils import export_to_csv, export_to_pdf, paginate_results

@login_required
@log_activity('view_customers')
def customer_list(request):
    """Display list of customers with search and filtering"""
    customers = Customer.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(company__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        customers = customers.filter(status=status_filter)
    
    # Filter by assigned user (for sales reps)
    if not request.user.is_staff:
        customers = customers.filter(assigned_to=request.user)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_date')
    customers = customers.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customers': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_count': customers.count(),
    }
    
    return render(request, 'customers/customer_list.html', context)

@login_required
@log_activity('view_customer_detail')
def customer_detail(request, customer_id):
    """Display detailed customer information"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Check permissions
    if not request.user.is_staff and customer.assigned_to != request.user:
        messages.error(request, "You don't have permission to view this customer.")
        return redirect('customer_list')
    
    # Get recent interactions
    interactions = customer.interactions.all()[:10]
    
    # Get deals
    deals = customer.deals.all()
    
    # Calculate metrics
    total_value = sum(deal.value for deal in deals)
    
    context = {
        'customer': customer,
        'interactions': interactions,
        'deals': deals,
        'total_value': total_value,
        'interaction_count': customer.interaction_count,
    }
    
    return render(request, 'customers/customer_detail.html', context)

@login_required
@log_activity('create_customer')
def customer_create(request):
    """Create a new customer"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.assigned_to = request.user
            customer.save()
            
            # Sync with Firebase
            firebase_data = customer.to_firebase_dict()
            firebase_id = FirebaseManager.create_customer(firebase_data)
            customer.firebase_id = firebase_id
            customer.save()
            
            messages.success(request, f"Customer '{customer.name}' created successfully!")
            return redirect('customer_detail', customer_id=customer.id)
    else:
        form = CustomerForm()
    
    return render(request, 'customers/customer_form.html', {'form': form, 'action': 'Create'})

@login_required
@log_activity('update_customer')
def customer_update(request, customer_id):
    """Update customer information"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Check permissions
    if not request.user.is_staff and customer.assigned_to != request.user:
        messages.error(request, "You don't have permission to edit this customer.")
        return redirect('customer_list')
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            
            # Sync with Firebase
            if customer.firebase_id:
                firebase_data = customer.to_firebase_dict()
                FirebaseManager.update_customer(customer.firebase_id, firebase_data)
            
            messages.success(request, f"Customer '{customer.name}' updated successfully!")
            return redirect('customer_detail', customer_id=customer.id)
    else:
        form = CustomerForm(instance=customer)
    
    return render(request, 'customers/customer_form.html', {
        'form': form,
        'action': 'Update',
        'customer': customer
    })

@login_required
@role_required('Admin', 'Manager')
@log_activity('delete_customer')
def customer_delete(request, customer_id):
    """Delete a customer"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    if request.method == 'POST':
        # Delete from Firebase
        if customer.firebase_id:
            FirebaseManager.delete_customer(customer.firebase_id)
        
        customer_name = customer.name
        customer.delete()
        
        messages.success(request, f"Customer '{customer_name}' deleted successfully!")
        return redirect('customer_list')
    
    return render(request, 'customers/customer_confirm_delete.html', {'customer': customer})

@login_required
@log_activity('add_interaction')
def interaction_add(request, customer_id):
    """Add a new interaction for a customer"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Check permissions
    if not request.user.is_staff and customer.assigned_to != request.user:
        messages.error(request, "You don't have permission to add interactions for this customer.")
        return redirect('customer_list')
    
    if request.method == 'POST':
        form = InteractionForm(request.POST)
        if form.is_valid():
            interaction = form.save(commit=False)
            interaction.customer = customer
            interaction.created_by = request.user
            interaction.save()
            
            # Sync with Firebase
            firebase_data = interaction.to_firebase_dict()
            firebase_id = FirebaseManager.create_interaction(firebase_data)
            interaction.firebase_id = firebase_id
            interaction.save()
            
            messages.success(request, "Interaction added successfully!")
            return redirect('customer_detail', customer_id=customer.id)
    else:
        form = InteractionForm()
    
    return render(request, 'customers/interaction_form.html', {
        'form': form,
        'customer': customer
    })

@login_required
@require_http_methods(["GET"])
def customer_search_api(request):
    """API endpoint for customer search"""
    query = request.GET.get('q', '')
    limit = int(request.GET.get('limit', 10))
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    customers = Customer.objects.filter(
        Q(name__icontains=query) |
        Q(email__icontains=query) |
        Q(company__icontains=query)
    )[:limit]
    
    # Filter by assigned user if not staff
    if not request.user.is_staff:
        customers = customers.filter(assigned_to=request.user)
    
    results = [{
        'id': c.id,
        'name': c.name,
        'email': c.email,
        'company': c.company,
        'status': c.status
    } for c in customers]
    
    return JsonResponse({'results': results})

@login_required
@validate_json_request(['name', 'email'])
@require_http_methods(["POST"])
def customer_quick_add_api(request):
    """API endpoint for quick customer addition"""
    data = json.loads(request.body)
    
    # Check if customer already exists
    if Customer.objects.filter(email=data['email']).exists():
        return JsonResponse({'error': 'Customer with this email already exists'}, status=400)
    
    customer = Customer(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone', ''),
        company=data.get('company', ''),
        status='Lead',
        assigned_to=request.user,
        notes=data.get('notes', '')
    )
    customer.save()
    
    # Sync with Firebase
    firebase_data = customer.to_firebase_dict()
    firebase_id = FirebaseManager.create_customer(firebase_data)
    customer.firebase_id = firebase_id
    customer.save()
    
    return JsonResponse({
        'id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'message': 'Customer created successfully'
    })

@login_required
@role_required('Admin', 'Manager')
def customer_export(request):
    """Export customers to CSV or PDF"""
    export_format = request.GET.get('format', 'csv')
    
    customers = Customer.objects.all()
    
    # Apply filters from request
    status_filter = request.GET.get('status', '')
    if status_filter:
        customers = customers.filter(status=status_filter)
    
    if export_format == 'csv':
        data = [{
            'Name': c.name,
            'Email': c.email,
            'Phone': c.phone,
            'Company': c.company,
            'Status': c.status,
            'Assigned To': c.assigned_to.username if c.assigned_to else '',
            'Created Date': c.created_date.strftime('%Y-%m-%d'),
            'Total Deal Value': c.total_deal_value,
            'Interactions': c.interaction_count
        } for c in customers]
        
        filepath = export_to_csv(data, 'customers')
        
        # Return file download response
        with open(filepath, 'rb') as f:
            response = HttpResponse(f.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="customers.csv"'
            return response
    
    elif export_format == 'pdf':
        # Generate PDF report
        context = {
            'customers': customers,
            'generated_date': datetime.now()
        }
        filepath = export_to_pdf(context, 'customer_report', 'customers')
        
        # Return file download response
        with open(filepath, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="customers.pdf"'
            return response
    
    return JsonResponse({'error': 'Invalid export format'}, status=400)

@login_required
def customer_analytics(request):
    """Customer analytics dashboard"""
    # Get date range
    period = request.GET.get('period', 'month')
    
    # Calculate metrics
    total_customers = Customer.objects.count()
    
    # Customers by status
    status_counts = Customer.objects.values('status').annotate(count=Count('id'))
    
    # New customers this period
    if period == 'week':
        start_date = datetime.now() - timedelta(weeks=1)
    elif period == 'month':
        start_date = datetime.now() - timedelta(days=30)
    elif period == 'quarter':
        start_date = datetime.now() - timedelta(days=90)
    else:
        start_date = datetime.now() - timedelta(days=365)
    
    new_customers = Customer.objects.filter(created_date__gte=start_date).count()
    
    # Top performers (customers with most deals)
    top_customers = Customer.objects.annotate(
        deal_count=Count('deals'),
        total_value=Sum('deals__value')
    ).order_by('-total_value')[:10]
    
    context = {
        'total_customers': total_customers,
        'status_counts': status_counts,
        'new_customers': new_customers,
        'top_customers': top_customers,
        'period': period
    }
    
    return render(request, 'customers/analytics.html', context)