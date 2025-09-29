# Sales tracking views - Firebase Only
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from datetime import datetime, timedelta
import json

from .models import DealSchema, PipelineHistorySchema, SalesActivitySchema, SalesForecastSchema
from customers.models import CustomerSchema
from core.decorators import role_required, log_activity
from core.firebase_config import FirebaseDB

@login_required
@log_activity('view_pipeline')
def pipeline_view(request):
    """Main pipeline dashboard view using Firebase"""
    # Get deals from Firebase
    deals = FirebaseDB.get_records('deals')
    
    # Filter by user if not staff
    if not request.user.is_staff:
        user_email = request.user.email
        deals = [d for d in deals if d.get('assigned_to') == user_email]
    
    # Apply filters
    stage_filter = request.GET.get('stage', '')
    if stage_filter:
        deals = [d for d in deals if d.get('stage') == stage_filter]
    
    # Group by stage
    pipeline_data = {}
    for stage in DealSchema.STAGE_CHOICES:
        stage_deals = [d for d in deals if d.get('stage') == stage]
        pipeline_data[stage] = {
            'count': len(stage_deals),
            'total_value': sum([d.get('value', 0) for d in stage_deals]),
            'weighted_value': sum([d.get('value', 0) * d.get('probability', 0) / 100 for d in stage_deals]),
            'deals': stage_deals[:10]  # Limit for performance
        }
    
    # Calculate basic metrics (simplified for Firebase)
    conversion_rates = {}
    velocity_metrics = {}
    forecast = {'total_value': sum([d.get('value', 0) for d in deals])}
    
    context = {
        'pipeline_data': pipeline_data,
        'conversion_rates': conversion_rates,
        'velocity_metrics': velocity_metrics,
        'forecast': forecast,
        'active_tab': 'pipeline'
    }
    
    return render(request, 'sales/pipeline.html', context)

@login_required
@log_activity('view_deals')
def deal_list(request):
    """List all deals with filtering using Firebase"""
    deals = FirebaseDB.get_records('deals')
    
    # Apply user filter
    if not request.user.is_staff:
        user_email = request.user.email
        deals = [d for d in deals if d.get('assigned_to') == user_email]
    
    # Search
    search = request.GET.get('search', '')
    if search:
        deals = [d for d in deals if 
                search.lower() in d.get('title', '').lower() or
                search.lower() in d.get('customer', '').lower()]
    
    # Status filter
    status = request.GET.get('status', '')
    if status:
        deals = [d for d in deals if d.get('status') == status]
    
    # Stage filter
    stage = request.GET.get('stage', '')
    if stage:
        deals = [d for d in deals if d.get('stage') == stage]
    
    # Sort by created_date (newest first)
    deals.sort(key=lambda x: x.get('created_date', ''), reverse=True)
    
    # Simple pagination
    page = int(request.GET.get('page', 1))
    page_size = 20
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_deals = deals[start_idx:end_idx]
    
    context = {
        'deals': page_deals,
        'search': search,
        'status': status,
        'stage': stage,
        'total_value': sum([d.get('value', 0) for d in deals]),
        'active_tab': 'deals',
        'has_next': end_idx < len(deals),
        'has_previous': start_idx > 0,
        'page': page
    }
    
    return render(request, 'sales/deal_list.html', context)

@login_required
@log_activity('view_deal_detail')
def deal_detail(request, deal_id):
    """Deal detail view using Firebase"""
    deals = FirebaseDB.get_records('deals')
    deal = None
    
    # Find deal by ID
    for d in deals:
        if d.get('id') == deal_id:
            deal = d
            break
    
    if not deal:
        messages.error(request, "Deal not found.")
        return redirect('deal_list')
    
    # Check permissions
    if not request.user.is_staff and deal.get('assigned_to') != request.user.email:
        messages.error(request, "You don't have permission to view this deal.")
        return redirect('deal_list')
    
    # Get deal history (simplified)
    history = FirebaseDB.get_records('pipeline_history')
    deal_history = [h for h in history if h.get('deal_id') == deal_id][:10]
    
    # Get activities (simplified)
    activities = FirebaseDB.get_records('sales_activities')
    deal_activities = [a for a in activities if a.get('deal_id') == deal_id][:10]
    
    # Basic recommendations
    recommendations = []
    if deal.get('probability', 0) < 50 and deal.get('stage') == 'Proposal':
        recommendations.append({
            'type': 'warning',
            'message': 'Low probability for Proposal stage. Consider reviewing proposal.',
            'action': 'Review proposal'
        })
    
    context = {
        'deal': deal,
        'history': deal_history,
        'activities': deal_activities,
        'recommendations': recommendations,
        'active_tab': 'deals'
    }
    
    return render(request, 'sales/deal_detail.html', context)

@login_required
@log_activity('create_deal')
def deal_create(request):
    """Create a new deal using Firebase"""
    if request.method == 'POST':
        deal_data = {
            'title': request.POST.get('title'),
            'customer': request.POST.get('customer'),
            'value': float(request.POST.get('value', 0)),
            'stage': request.POST.get('stage', 'Lead'),
            'probability': int(request.POST.get('probability', 10)),
            'expected_close': request.POST.get('expected_close'),
            'notes': request.POST.get('notes', ''),
            'assigned_to': request.user.email,
            'status': 'Active',
            'products': request.POST.getlist('products'),
            'competitors': request.POST.get('competitors', '')
        }
        
        # Validate
        is_valid, error_msg = DealSchema.validate_deal(deal_data)
        if not is_valid:
            messages.error(request, f"❌ {error_msg}")
            return render(request, 'sales/deal_form.html', {
                'form_data': deal_data,
                'action': 'Create',
                'active_tab': 'deals'
            })
        
        # Create deal document
        deal_doc = DealSchema.create_deal_document(deal_data)
        doc_id = FirebaseDB.add_record('deals', deal_doc)
        
        if doc_id:
            # Create initial pipeline history
            history_data = {
                'deal_id': doc_id,
                'from_stage': 'New',
                'to_stage': deal_data['stage'],
                'changed_by': request.user.email,
                'notes': 'Deal created'
            }
            history_doc = PipelineHistorySchema.create_history_document(history_data)
            FirebaseDB.add_record('pipeline_history', history_doc)
            
            messages.success(request, f"✅ Deal '{deal_data['title']}' created successfully!")
            return redirect('deal_detail', deal_id=doc_id)
        else:
            messages.error(request, "❌ Failed to create deal")
    
    # Get customers for dropdown
    customers = FirebaseDB.get_records('customers')
    
    context = {
        'customers': customers,
        'stages': DealSchema.STAGE_CHOICES,
        'action': 'Create',
        'active_tab': 'deals'
    }
    
    return render(request, 'sales/deal_form.html', context)

@login_required
@log_activity('update_deal')
def deal_update(request, deal_id):
    """Update deal information using Firebase"""
    deals = FirebaseDB.get_records('deals')
    deal = None
    
    # Find deal by ID
    for d in deals:
        if d.get('id') == deal_id:
            deal = d
            break
    
    if not deal:
        messages.error(request, "Deal not found.")
        return redirect('deal_list')
    
    # Check permissions
    if not request.user.is_staff and deal.get('assigned_to') != request.user.email:
        messages.error(request, "You don't have permission to edit this deal.")
        return redirect('deal_list')
    
    if request.method == 'POST':
        old_stage = deal.get('stage')
        
        # Update deal data
        update_data = {
            'title': request.POST.get('title'),
            'customer': request.POST.get('customer'),
            'value': float(request.POST.get('value', 0)),
            'stage': request.POST.get('stage'),
            'probability': int(request.POST.get('probability', 0)),
            'expected_close': request.POST.get('expected_close'),
            'notes': request.POST.get('notes', ''),
            'products': request.POST.getlist('products'),
            'competitors': request.POST.get('competitors', ''),
            'updated_date': datetime.now().isoformat()
        }
        
        # Validate
        is_valid, error_msg = DealSchema.validate_deal(update_data)
        if not is_valid:
            messages.error(request, f"❌ {error_msg}")
            return render(request, 'sales/deal_form.html', {
                'deal': deal,
                'action': 'Update',
                'active_tab': 'deals'
            })
        
        # Update in Firebase
        success = FirebaseDB.update_record('deals', deal_id, update_data)
        
        if success:
            # Check if stage changed
            if old_stage != update_data['stage']:
                history_data = {
                    'deal_id': deal_id,
                    'from_stage': old_stage,
                    'to_stage': update_data['stage'],
                    'changed_by': request.user.email,
                    'notes': 'Stage updated via form'
                }
                history_doc = PipelineHistorySchema.create_history_document(history_data)
                FirebaseDB.add_record('pipeline_history', history_doc)
            
            messages.success(request, f"✅ Deal '{update_data['title']}' updated successfully!")
            return redirect('deal_detail', deal_id=deal_id)
        else:
            messages.error(request, "❌ Failed to update deal")
    
    # Get customers for dropdown
    customers = FirebaseDB.get_records('customers')
    
    context = {
        'deal': deal,
        'customers': customers,
        'stages': DealSchema.STAGE_CHOICES,
        'action': 'Update',
        'active_tab': 'deals'
    }
    
    return render(request, 'sales/deal_form.html', context)

@login_required
@role_required('Admin', 'Manager')
@log_activity('delete_deal')
def deal_delete(request, deal_id):
    """Delete a deal using Firebase"""
    deals = FirebaseDB.get_records('deals')
    deal = None
    
    # Find deal by ID
    for d in deals:
        if d.get('id') == deal_id:
            deal = d
            break
    
    if not deal:
        messages.error(request, "Deal not found.")
        return redirect('deal_list')
    
    if request.method == 'POST':
        success = FirebaseDB.delete_record('deals', deal_id)
        
        if success:
            deal_title = deal.get('title', 'Unknown')
            messages.success(request, f"✅ Deal '{deal_title}' deleted successfully!")
            return redirect('deal_list')
        else:
            messages.error(request, "❌ Failed to delete deal")
    
    return render(request, 'sales/deal_confirm_delete.html', {
        'deal': deal,
        'active_tab': 'deals'
    })

@login_required
@require_http_methods(["POST"])
def deal_move_stage(request, deal_id):
    """API endpoint to move deal to different stage using Firebase"""
    deals = FirebaseDB.get_records('deals')
    deal = None
    
    # Find deal by ID
    for d in deals:
        if d.get('id') == deal_id:
            deal = d
            break
    
    if not deal:
        return JsonResponse({'error': 'Deal not found'}, status=404)
    
    # Check permissions
    if not request.user.is_staff and deal.get('assigned_to') != request.user.email:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    data = json.loads(request.body)
    new_stage = data.get('stage')
    notes = data.get('notes', '')
    
    if not new_stage:
        return JsonResponse({'error': 'Stage is required'}, status=400)
    
    # Update deal stage
    old_stage = deal.get('stage')
    update_data = {
        'stage': new_stage,
        'updated_date': datetime.now().isoformat()
    }
    
    # Update probability based on stage
    stage_probabilities = {
        'Lead': 10,
        'Qualified': 25,
        'Proposal': 50,
        'Negotiation': 75,
        'Won': 100,
        'Lost': 0,
        'On Hold': deal.get('probability', 0)
    }
    update_data['probability'] = stage_probabilities.get(new_stage, deal.get('probability', 0))
    
    # Update status based on stage
    if new_stage == 'Won':
        update_data['status'] = 'Won'
    elif new_stage == 'Lost':
        update_data['status'] = 'Lost'
    elif new_stage == 'On Hold':
        update_data['status'] = 'On Hold'
    else:
        update_data['status'] = 'Active'
    
    success = FirebaseDB.update_record('deals', deal_id, update_data)
    
    if success:
        # Create history record
        history_data = {
            'deal_id': deal_id,
            'from_stage': old_stage,
            'to_stage': new_stage,
            'changed_by': request.user.email,
            'notes': notes
        }
        history_doc = PipelineHistorySchema.create_history_document(history_data)
        FirebaseDB.add_record('pipeline_history', history_doc)
        
        return JsonResponse({
            'success': True,
            'deal_id': deal_id,
            'new_stage': new_stage,
            'status': update_data['status'],
            'probability': update_data['probability']
        })
    
    return JsonResponse({'error': 'Failed to update deal'}, status=500)

@login_required
def activity_add(request, deal_id):
    """Add activity to a deal using Firebase"""
    deals = FirebaseDB.get_records('deals')
    deal = None
    
    # Find deal by ID
    for d in deals:
        if d.get('id') == deal_id:
            deal = d
            break
    
    if not deal:
        messages.error(request, "Deal not found.")
        return redirect('deal_list')
    
    # Check permissions
    if not request.user.is_staff and deal.get('assigned_to') != request.user.email:
        messages.error(request, "You don't have permission to add activities to this deal.")
        return redirect('deal_list')
    
    if request.method == 'POST':
        activity_data = {
            'deal_id': deal_id,
            'activity_type': request.POST.get('activity_type'),
            'subject': request.POST.get('subject'),
            'description': request.POST.get('description'),
            'due_date': request.POST.get('due_date'),
            'assigned_to': request.user.email
        }
        
        activity_doc = SalesActivitySchema.create_activity_document(activity_data)
        doc_id = FirebaseDB.add_record('sales_activities', activity_doc)
        
        if doc_id:
            messages.success(request, "✅ Activity added successfully!")
            return redirect('deal_detail', deal_id=deal_id)
        else:
            messages.error(request, "❌ Failed to add activity")
    
    context = {
        'deal': deal,
        'activity_types': SalesActivitySchema.ACTIVITY_TYPES,
        'active_tab': 'deals'
    }
    
    return render(request, 'sales/activity_form.html', context)

@login_required
@require_http_methods(["POST"])
def activity_complete(request, activity_id):
    """Mark activity as complete using Firebase"""
    activities = FirebaseDB.get_records('sales_activities')
    activity = None
    
    # Find activity by ID
    for a in activities:
        if a.get('id') == activity_id:
            activity = a
            break
    
    if not activity:
        return JsonResponse({'error': 'Activity not found'}, status=404)
    
    # Check permissions
    if not request.user.is_staff and activity.get('assigned_to') != request.user.email:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    update_data = {
        'completed': True,
        'completed_date': datetime.now().isoformat()
    }
    
    success = FirebaseDB.update_record('sales_activities', activity_id, update_data)
    
    if success:
        return JsonResponse({
            'success': True,
            'activity_id': activity_id,
            'completed': True,
            'completed_date': update_data['completed_date']
        })
    
    return JsonResponse({'error': 'Failed to update activity'}, status=500)

@login_required
@role_required('Admin', 'Manager')
def sales_forecast(request):
    """Sales forecasting view using Firebase"""
    period_type = request.GET.get('type', 'monthly')
    
    # Get deals from Firebase
    deals = FirebaseDB.get_records('deals')
    
    # Generate forecasts for next 6 periods
    forecasts = []
    current_date = datetime.now()
    
    for i in range(6):
        if period_type == 'monthly':
            forecast_date = current_date + timedelta(days=30*i)
            period = forecast_date.strftime('%Y-%m')
        else:  # quarterly
            quarter = ((current_date.month + i*3 - 1) // 3) + 1
            year = current_date.year + ((current_date.month + i*3 - 1) // 12)
            period = f"{year}-Q{quarter % 4 + 1}"
        
        # Calculate forecast (simplified)
        period_deals = [d for d in deals if d.get('expected_close', '').startswith(period[:7])]
        total_pipeline = sum([d.get('value', 0) for d in period_deals])
        weighted_pipeline = sum([d.get('value', 0) * d.get('probability', 0) / 100 for d in period_deals])
        expected_revenue = sum([d.get('value', 0) for d in period_deals if d.get('probability', 0) >= 70])
        
        forecast_data = {
            'period': period,
            'total_pipeline': total_pipeline,
            'weighted_pipeline': weighted_pipeline,
            'expected_revenue': expected_revenue
        }
        
        forecasts.append(forecast_data)
    
    context = {
        'forecasts': forecasts,
        'period_type': period_type,
        'active_tab': 'forecast'
    }
    
    return render(request, 'sales/forecast.html', context)

@login_required
def team_performance(request):
    """Team performance dashboard using Firebase"""
    date_range = request.GET.get('range', 'month')
    
    # Get data from Firebase
    deals = FirebaseDB.get_records('deals')
    
    # Filter by date range (simplified)
    if date_range == 'week':
        start_date = datetime.now() - timedelta(weeks=1)
    elif date_range == 'month':
        start_date = datetime.now() - timedelta(days=30)
    elif date_range == 'quarter':
        start_date = datetime.now() - timedelta(days=90)
    else:
        start_date = datetime.now() - timedelta(days=365)
    
    start_date_str = start_date.isoformat()
    deals = [d for d in deals if d.get('created_date', '') >= start_date_str]
    
    # Calculate team metrics
    team_metrics = {}
    for deal in deals:
        assigned_to = deal.get('assigned_to', 'Unassigned')
        if assigned_to not in team_metrics:
            team_metrics[assigned_to] = {
                'total_deals': 0,
                'won_deals': 0,
                'total_value': 0,
                'won_value': 0
            }
        
        team_metrics[assigned_to]['total_deals'] += 1
        team_metrics[assigned_to]['total_value'] += deal.get('value', 0)
        
        if deal.get('status') == 'Won':
            team_metrics[assigned_to]['won_deals'] += 1
            team_metrics[assigned_to]['won_value'] += deal.get('value', 0)
    
    # Calculate rates
    for user, metrics in team_metrics.items():
        if metrics['total_deals'] > 0:
            metrics['win_rate'] = round((metrics['won_deals'] / metrics['total_deals']) * 100, 2)
            metrics['avg_deal_size'] = round(metrics['total_value'] / metrics['total_deals'], 2)
        else:
            metrics['win_rate'] = 0
            metrics['avg_deal_size'] = 0
    
    context = {
        'team_metrics': team_metrics,
        'date_range': date_range,
        'active_tab': 'team'
    }
    
    return render(request, 'sales/team_performance.html', context)

@login_required
def pipeline_api(request):
    """API endpoint for pipeline data (for drag-and-drop) using Firebase"""
    deals = FirebaseDB.get_records('deals')
    
    # Filter by user
    if not request.user.is_staff:
        user_email = request.user.email
        deals = [d for d in deals if d.get('assigned_to') == user_email]
    
    # Group by stage
    pipeline_data = []
    for stage in DealSchema.STAGE_CHOICES:
        stage_deals = [d for d in deals if d.get('stage') == stage]
        total_value = sum([d.get('value', 0) for d in stage_deals])
        weighted_value = sum([d.get('value', 0) * d.get('probability', 0) / 100 for d in stage_deals])
        
        pipeline_data.append({
            'stage': stage,
            'count': len(stage_deals),
            'total_value': float(total_value),
            'weighted_value': float(weighted_value),
            'deals': stage_deals
        })
    
    return JsonResponse({'pipeline': pipeline_data})