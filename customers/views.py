# Customer views and logic - Firebase Only
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from datetime import datetime, timedelta
import json

from .models import CustomerSchema, InteractionSchema, CustomerTagSchema
from core.firebase_config import FirebaseDB
from core.decorators import role_required, log_activity, validate_json_request
from core.utils import export_to_csv, export_to_pdf

@login_required
@log_activity('view_customers')
def customer_list(request):
    """Display list of customers with search and filtering using Firebase"""
    customers = FirebaseDB.get_records('customers')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        customers = [c for c in customers if
                    search_query.lower() in c.get('name', '').lower() or
                    search_query.lower() in c.get('email', '').lower() or
                    search_query.lower() in c.get('company', '').lower()]
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        customers = [c for c in customers if c.get('status') == status_filter]
    
    # Filter by assigned user (for sales reps)
    if not request.user.is_staff:
        user_email = request.user.email
        customers = [c for c in customers if c.get('assigned_to') == user_email]
    
    # Sort by created_date (newest first)
    customers.sort(key=lambda x: x.get('created_date', ''), reverse=True)
    
    # Simple pagination
    page = int(request.GET.get('page', 1))
    page_size = 20
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_customers = customers[start_idx:end_idx]
    
    context = {
        'customers': page_customers,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_count': len(customers),
        'has_next': end_idx < len(customers),
        'has_previous': start_idx > 0,
        'page': page
    }
    
    return render(request, 'customers/customer_list.html', context)

@login_required
@log_activity('view_customer_detail')
def customer_detail(request, customer_id):
    """Display detailed customer information using Firebase"""
    customers = FirebaseDB.get_records('customers')
    customer = None
    
    # Find customer by ID
    for c in customers:
        if c.get('id') == customer_id:
            customer = c
            break
    
    if not customer:
        messages.error(request, "Customer not found.")
        return redirect('customer_list')
    
    # Check permissions
    if not request.user.is_staff and customer.get('assigned_to') != request.user.email:
        messages.error(request, "You don't have permission to view this customer.")
        return redirect('customer_list')
    
    # Get recent interactions
    interactions = FirebaseDB.get_records('interactions')
    customer_interactions = [i for i in interactions if i.get('customer_id') == customer_id]
    customer_interactions.sort(key=lambda x: x.get('date', ''), reverse=True)
    customer_interactions = customer_interactions[:10]
    
    # Get deals
    deals = FirebaseDB.get_records('deals')
    customer_deals = [d for d in deals if d.get('customer') == customer.get('name')]
    
    # Calculate metrics
    total_value = sum([d.get('value', 0) for d in customer_deals])
    
    context = {
        'customer': customer,
        'interactions': customer_interactions,
        'deals': customer_deals,
        'total_value': total_value,
        'interaction_count': len(customer_interactions),
    }
    
    return render(request, 'customers/customer_detail.html', context)

@login_required
@log_activity('create_customer')
def customer_create(request):
    """Create a new customer using Firebase"""
    if request.method == 'POST':
        customer_data = {
            'name': request.POST.get('name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone', ''),
            'company': request.POST.get('company', ''),
            'status': request.POST.get('status', 'Lead'),
            'assigned_to': request.user.email,
            'notes': request.POST.get('notes', ''),
            'tags': request.POST.getlist('tags'),
            'address': request.POST.get('address', ''),
            'city': request.POST.get('city', ''),
            'state': request.POST.get('state', ''),
            'zip_code': request.POST.get('zip_code', ''),
            'country': request.POST.get('country', 'USA'),
            'industry': request.POST.get('industry', ''),
            'company_size': request.POST.get('company_size', ''),
            'website': request.POST.get('website', ''),
            'lead_source': request.POST.get('lead_source', '')
        }
        
        # Validate
        is_valid, error_msg = CustomerSchema.validate_customer(customer_data)
        if not is_valid:
            messages.error(request, f"❌ {error_msg}")
            return render(request, 'customers/customer_form.html', {
                'form_data': customer_data,
                'action': 'Create',
                'statuses': CustomerSchema.STATUS_CHOICES
            })
        
        # Check for duplicate email
        existing_customers = FirebaseDB.get_records('customers')
        for existing in existing_customers:
            if existing.get('email', '').lower() == customer_data['email'].lower():
                messages.error(request, "❌ A customer with this email already exists.")
                return render(request, 'customers/customer_form.html', {
                    'form_data': customer_data,
                    'action': 'Create',
                    'statuses': CustomerSchema.STATUS_CHOICES
                })
        
        # Create customer document
        customer_doc = CustomerSchema.create_customer_document(customer_data)
        doc_id = FirebaseDB.add_record('customers', customer_doc)
        
        if doc_id:
            messages.success(request, f"✅ Customer '{customer_data['name']}' created successfully!")
            return redirect('customer_detail', customer_id=doc_id)
        else:
            messages.error(request, "❌ Failed to create customer")
    
    context = {
        'action': 'Create',
        'statuses': CustomerSchema.STATUS_CHOICES
    }
    
    return render(request, 'customers/customer_form.html', context)

@login_required
@log_activity('update_customer')
def customer_update(request, customer_id):
    """Update customer information using Firebase"""
    customers = FirebaseDB.get_records('customers')
    customer = None
    
    # Find customer by ID
    for c in customers:
        if c.get('id') == customer_id:
            customer = c
            break
    
    if not customer:
        messages.error(request, "Customer not found.")
        return redirect('customer_list')
    
    # Check permissions
    if not request.user.is_staff and customer.get('assigned_to') != request.user.email:
        messages.error(request, "You don't have permission to edit this customer.")
        return redirect('customer_list')
    
    if request.method == 'POST':
        update_data = {
            'name': request.POST.get('name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone', ''),
            'company': request.POST.get('company', ''),
            'status': request.POST.get('status'),
            'notes': request.POST.get('notes', ''),
            'tags': request.POST.getlist('tags'),
            'address': request.POST.get('address', ''),
            'city': request.POST.get('city', ''),
            'state': request.POST.get('state', ''),
            'zip_code': request.POST.get('zip_code', ''),
            'country': request.POST.get('country', 'USA'),
            'industry': request.POST.get('industry', ''),
            'company_size': request.POST.get('company_size', ''),
            'website': request.POST.get('website', ''),
            'lead_source': request.POST.get('lead_source', ''),
            'updated_date': datetime.now().isoformat()
        }
        
        # Validate
        is_valid, error_msg = CustomerSchema.validate_customer(update_data)
        if not is_valid:
            messages.error(request, f"❌ {error_msg}")
            return render(request, 'customers/customer_form.html', {
                'customer': customer,
                'action': 'Update',
                'statuses': CustomerSchema.STATUS_CHOICES
            })
        
        # Check for duplicate email (excluding current customer)
        all_customers = FirebaseDB.get_records('customers')
        for existing in all_customers:
            if (existing.get('id') != customer_id and 
                existing.get('email', '').lower() == update_data['email'].lower()):
                messages.error(request, "❌ Another customer with this email already exists.")
                return render(request, 'customers/customer_form.html', {
                    'customer': customer,
                    'action': 'Update',
                    'statuses': CustomerSchema.STATUS_CHOICES
                })
        
        # Update in Firebase
        success = FirebaseDB.update_record('customers', customer_id, update_data)
        
        if success:
            messages.success(request, f"✅ Customer '{update_data['name']}' updated successfully!")
            return redirect('customer_detail', customer_id=customer_id)
        else:
            messages.error(request, "❌ Failed to update customer")
    
    context = {
        'customer': customer,
        'action': 'Update',
        'statuses': CustomerSchema.STATUS_CHOICES
    }
    
    return render(request, 'customers/customer_form.html', context)

@login_required
@role_required('Admin', 'Manager')
@log_activity('delete_customer')
def customer_delete(request, customer_id):
    """Delete a customer using Firebase"""
    customers = FirebaseDB.get_records('customers')
    customer = None
    
    # Find customer by ID
    for c in customers:
        if c.get('id') == customer_id:
            customer = c
            break
    
    if not customer:
        messages.error(request, "Customer not found.")
        return redirect('customer_list')
    
    if request.method == 'POST':
        success = FirebaseDB.delete_record('customers', customer_id)
        
        if success:
            customer_name = customer.get('name', 'Unknown')
            messages.success(request, f"✅ Customer '{customer_name}' deleted successfully!")
            return redirect('customer_list')
        else:
            messages.error(request, "❌ Failed to delete customer")
    
    return render(request, 'customers/customer_confirm_delete.html', {'customer': customer})

@login_required
@log_activity('add_interaction')
def interaction_add(request, customer_id):
    """Add a new interaction for a customer using Firebase"""
    customers = FirebaseDB.get_records('customers')
    customer = None
    
    # Find customer by ID
    for c in customers:
        if c.get('id') == customer_id:
            customer = c
            break
    
    if not customer:
        messages.error(request, "Customer not found.")
        return redirect('customer_list')
    
    # Check permissions
    if not request.user.is_staff and customer.get('assigned_to') != request.user.email:
        messages.error(request, "You don't have permission to add interactions for this customer.")
        return redirect('customer_list')
    
    if request.method == 'POST':
        interaction_data = {
            'customer_id': customer_id,
            'created_by': request.user.email,
            'type': request.POST.get('type'),
            'subject': request.POST.get('subject'),
            'description': request.POST.get('description'),
            'date': request.POST.get('date') or datetime.now().isoformat(),
            'follow_up_date': request.POST.get('follow_up_date'),
            'outcome': request.POST.get('outcome'),
            'location': request.POST.get('location', '')
        }
        
        interaction_doc = InteractionSchema.create_interaction_document(interaction_data)
        doc_id = FirebaseDB.add_record('interactions', interaction_doc)
        
        if doc_id:
            messages.success(request, "✅ Interaction added successfully!")
            return redirect('customer_detail', customer_id=customer_id)
        else:
            messages.error(request, "❌ Failed to add interaction")
    
    context = {
        'customer': customer,
        'interaction_types': InteractionSchema.INTERACTION_TYPES,
        'outcome_choices': InteractionSchema.OUTCOME_CHOICES
    }
    
    return render(request, 'customers/interaction_form.html', context)

@login_required
@require_http_methods(["GET"])
def customer_search_api(request):
    """API endpoint for customer search using Firebase"""
    query = request.GET.get('q', '')
    limit = int(request.GET.get('limit', 10))
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    customers = FirebaseDB.get_records('customers')
    
    # Filter customers based on search query
    filtered_customers = []
    for customer in customers:
        name = customer.get('name', '').lower()
        email = customer.get('email', '').lower()
        company = customer.get('company', '').lower()
        
        if (query.lower() in name or 
            query.lower() in email or 
            query.lower() in company):
            filtered_customers.append(customer)
    
    # Filter by assigned user if not staff
    if not request.user.is_staff:
        user_email = request.user.email
        filtered_customers = [c for c in filtered_customers if c.get('assigned_to') == user_email]
    
    # Limit results
    filtered_customers = filtered_customers[:limit]
    
    results = [{
        'id': c.get('id'),
        'name': c.get('name'),
        'email': c.get('email'),
        'company': c.get('company'),
        'status': c.get('status')
    } for c in filtered_customers]
    
    return JsonResponse({'results': results})

@login_required
@validate_json_request(['name', 'email'])
@require_http_methods(["POST"])
def customer_quick_add_api(request):
    """API endpoint for quick customer addition using Firebase"""
    data = json.loads(request.body)
    
    # Check if customer already exists
    existing_customers = FirebaseDB.get_records('customers')
    for existing in existing_customers:
        if existing.get('email', '').lower() == data['email'].lower():
            return JsonResponse({'error': 'Customer with this email already exists'}, status=400)
    
    customer_data = {
        'name': data['name'],
        'email': data['email'],
        'phone': data.get('phone', ''),
        'company': data.get('company', ''),
        'status': 'Lead',
        'assigned_to': request.user.email,
        'notes': data.get('notes', '')
    }
    
    customer_doc = CustomerSchema.create_customer_document(customer_data)
    doc_id = FirebaseDB.add_record('customers', customer_doc)
    
    if doc_id:
        return JsonResponse({
            'id': doc_id,
            'name': customer_data['name'],
            'email': customer_data['email'],
            'message': 'Customer created successfully'
        })
    
    return JsonResponse({'error': 'Failed to create customer'}, status=500)

@login_required
@role_required('Admin', 'Manager')
def customer_export(request):
    """Export customers to CSV or PDF using Firebase"""
    export_format = request.GET.get('format', 'csv')
    
    customers = FirebaseDB.get_records('customers')
    
    # Apply filters from request
    status_filter = request.GET.get('status', '')
    if status_filter:
        customers = [c for c in customers if c.get('status') == status_filter]
    
    if export_format == 'csv':
        data = [{
            'Name': c.get('name', ''),
            'Email': c.get('email', ''),
            'Phone': c.get('phone', ''),
            'Company': c.get('company', ''),
            'Status': c.get('status', ''),
            'Assigned To': c.get('assigned_to', ''),
            'Created Date': c.get('created_date', '')[:10] if c.get('created_date') else '',
            'Total Deal Value': c.get('total_deal_value', 0),
            'Interactions': c.get('interaction_count', 0)
        } for c in customers]
        
        # Create CSV file (simplified - in production use proper CSV export)
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys() if data else [])
        writer.writeheader()
        writer.writerows(data)
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="customers.csv"'
        return response
    
    elif export_format == 'pdf':
        # Simplified PDF export - in production use proper PDF library
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="customers.pdf"'
        response.write(b'PDF export not implemented yet')
        return response
    
    return JsonResponse({'error': 'Invalid export format'}, status=400)

@login_required
def customer_analytics(request):
    """Customer analytics dashboard using Firebase"""
    # Get date range
    period = request.GET.get('period', 'month')
    
    customers = FirebaseDB.get_records('customers')
    
    # Calculate metrics
    total_customers = len(customers)
    
    # Customers by status
    status_counts = {}
    for status in CustomerSchema.STATUS_CHOICES:
        status_counts[status] = len([c for c in customers if c.get('status') == status])
    
    # New customers this period
    if period == 'week':
        start_date = datetime.now() - timedelta(weeks=1)
    elif period == 'month':
        start_date = datetime.now() - timedelta(days=30)
    elif period == 'quarter':
        start_date = datetime.now() - timedelta(days=90)
    else:
        start_date = datetime.now() - timedelta(days=365)
    
    start_date_str = start_date.isoformat()
    new_customers = len([c for c in customers if c.get('created_date', '') >= start_date_str])
    
    # Top customers by deal value
    deals = FirebaseDB.get_records('deals')
    customer_values = {}
    
    for deal in deals:
        customer_name = deal.get('customer', '')
        if customer_name:
            if customer_name not in customer_values:
                customer_values[customer_name] = 0
            customer_values[customer_name] += deal.get('value', 0)
    
    # Find top customers
    top_customers = []
    for customer in customers:
        customer_name = customer.get('name', '')
        total_value = customer_values.get(customer_name, 0)
        deal_count = len([d for d in deals if d.get('customer') == customer_name])
        
        top_customers.append({
            'name': customer_name,
            'company': customer.get('company', ''),
            'total_value': total_value,
            'deal_count': deal_count
        })
    
    top_customers.sort(key=lambda x: x['total_value'], reverse=True)
    top_customers = top_customers[:10]
    
    context = {
        'total_customers': total_customers,
        'status_counts': status_counts,
        'new_customers': new_customers,
        'top_customers': top_customers,
        'period': period
    }
    
    return render(request, 'customers/analytics.html', context)