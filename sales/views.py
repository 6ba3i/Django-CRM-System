# Sales tracking views
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q, Sum, Count
from datetime import datetime, timedelta
import json

from .models import Deal, PipelineHistory, SalesForecast, SalesActivity
from .forms import DealForm, SalesActivityForm, PipelineFilterForm
from .pipeline_logic import PipelineManager
from customers.models import Customer
from core.decorators import role_required, log_activity
from core.firebase_config import FirebaseManager

@login_required
@log_activity('view_pipeline')
def pipeline_view(request):
    """Main pipeline dashboard view"""
    # Get filter parameters
    stage_filter = request.GET.get('stage', '')
    user_filter = request.GET.get('user', '')
    date_range = request.GET.get('range', 'all')
    
    # Get pipeline data
    pipeline_data = PipelineManager.get_pipeline_data(
        user=request.user if not request.user.is_staff else None,
        date_range=None  # Will implement date range logic
    )
    
    # Get metrics
    conversion_rates = PipelineManager.calculate_conversion_rates()
    velocity_metrics = PipelineManager.calculate_velocity_metrics()
    
    # Get forecast
    forecast = PipelineManager.get_pipeline_forecast('quarter')
    
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
    """List all deals with filtering"""
    deals = Deal.objects.all()
    
    # Apply filters
    if not request.user.is_staff:
        deals = deals.filter(assigned_to=request.user)
    
    # Search
    search = request.GET.get('search', '')
    if search:
        deals = deals.filter(
            Q(title__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(customer__company__icontains=search)
        )
    
    # Status filter
    status = request.GET.get('status', '')
    if status:
        deals = deals.filter(status=status)
    
    # Stage filter
    stage = request.GET.get('stage', '')
    if stage:
        deals = deals.filter(stage=stage)
    
    # Sort
    sort = request.GET.get('sort', '-created_date')
    deals = deals.order_by(sort)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(deals, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'deals': page_obj,
        'search': search,
        'status': status,
        'stage': stage,
        'total_value': deals.aggregate(total=Sum('value'))['total'] or 0,
        'active_tab': 'deals'
    }
    
    return render(request, 'sales/deal_list.html', context)

@login_required
@log_activity('view_deal_detail')
def deal_detail(request, deal_id):
    """Deal detail view"""
    deal = get_object_or_404(Deal, id=deal_id)
    
    # Check permissions
    if not request.user.is_staff and deal.assigned_to != request.user:
        messages.error(request, "You don't have permission to view this deal.")
        return redirect('deal_list')
    
    # Get deal history
    history = deal.pipeline_history.all()[:10]
    
    # Get activities
    activities = deal.activities.all()[:10]
    
    # Get recommendations
    recommendations = PipelineManager.get_deal_recommendations(deal)
    
    context = {
        'deal': deal,
        'history': history,
        'activities': activities,
        'recommendations': recommendations,
        'active_tab': 'deals'
    }
    
    return render(request, 'sales/deal_detail.html', context)

@login_required
@log_activity('create_deal')
def deal_create(request):
    """Create a new deal"""
    if request.method == 'POST':
        form = DealForm(request.POST)
        if form.is_valid():
            deal = form.save(commit=False)
            deal.assigned_to = request.user
            deal.save()
            
            # Sync with Firebase
            firebase_data = deal.to_firebase_dict()
            firebase_id = FirebaseManager.create_deal(firebase_data)
            deal.firebase_id = firebase_id
            deal.save()
            
            # Create initial pipeline history
            PipelineHistory.objects.create(
                deal=deal,
                from_stage='New',
                to_stage=deal.stage,
                changed_by=request.user,
                notes='Deal created'
            )
            
            messages.success(request, f"Deal '{deal.title}' created successfully!")
            return redirect('deal_detail', deal_id=deal.id)
    else:
        form = DealForm()
        
        # Pre-populate customer if coming from customer page
        customer_id = request.GET.get('customer')
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
                form.fields['customer'].initial = customer
            except Customer.DoesNotExist:
                pass
    
    return render(request, 'sales/deal_form.html', {
        'form': form,
        'action': 'Create',
        'active_tab': 'deals'
    })

@login_required
@log_activity('update_deal')
def deal_update(request, deal_id):
    """Update deal information"""
    deal = get_object_or_404(Deal, id=deal_id)
    
    # Check permissions
    if not request.user.is_staff and deal.assigned_to != request.user:
        messages.error(request, "You don't have permission to edit this deal.")
        return redirect('deal_list')
    
    if request.method == 'POST':
        form = DealForm(request.POST, instance=deal)
        if form.is_valid():
            old_stage = deal.stage
            deal = form.save()
            
            # Check if stage changed
            if old_stage != deal.stage:
                PipelineHistory.objects.create(
                    deal=deal,
                    from_stage=old_stage,
                    to_stage=deal.stage,
                    changed_by=request.user,
                    notes='Stage updated via form'
                )
            
            # Sync with Firebase
            if deal.firebase_id:
                firebase_data = deal.to_firebase_dict()
                FirebaseManager.update_deal(deal.firebase_id, firebase_data)
            
            messages.success(request, f"Deal '{deal.title}' updated successfully!")
            return redirect('deal_detail', deal_id=deal.id)
    else:
        form = DealForm(instance=deal)
    
    return render(request, 'sales/deal_form.html', {
        'form': form,
        'action': 'Update',
        'deal': deal,
        'active_tab': 'deals'
    })

@login_required
@role_required('Admin', 'Manager')
@log_activity('delete_deal')
def deal_delete(request, deal_id):
    """Delete a deal"""
    deal = get_object_or_404(Deal, id=deal_id)
    
    if request.method == 'POST':
        # Delete from Firebase
        if deal.firebase_id:
            # Firebase deletion would go here
            pass
        
        deal_title = deal.title
        deal.delete()
        
        messages.success(request, f"Deal '{deal_title}' deleted successfully!")
        return redirect('deal_list')
    
    return render(request, 'sales/deal_confirm_delete.html', {
        'deal': deal,
        'active_tab': 'deals'
    })

@login_required
@require_http_methods(["POST"])
def deal_move_stage(request, deal_id):
    """API endpoint to move deal to different stage"""
    deal = get_object_or_404(Deal, id=deal_id)
    
    # Check permissions
    if not request.user.is_staff and deal.assigned_to != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    data = json.loads(request.body)
    new_stage = data.get('stage')
    notes = data.get('notes', '')
    
    if not new_stage:
        return JsonResponse({'error': 'Stage is required'}, status=400)
    
    # Move deal
    PipelineManager.move_deal_stage(deal, new_stage, request.user, notes)
    
    return JsonResponse({
        'success': True,
        'deal_id': deal.id,
        'new_stage': new_stage,
        'status': deal.status,
        'probability': deal.probability
    })

@login_required
def activity_add(request, deal_id):
    """Add activity to a deal"""
    deal = get_object_or_404(Deal, id=deal_id)
    
    # Check permissions
    if not request.user.is_staff and deal.assigned_to != request.user:
        messages.error(request, "You don't have permission to add activities to this deal.")
        return redirect('deal_list')
    
    if request.method == 'POST':
        form = SalesActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.deal = deal
            activity.assigned_to = request.user
            activity.save()
            
            messages.success(request, "Activity added successfully!")
            return redirect('deal_detail', deal_id=deal.id)
    else:
        form = SalesActivityForm()
    
    return render(request, 'sales/activity_form.html', {
        'form': form,
        'deal': deal,
        'active_tab': 'deals'
    })

@login_required
@require_http_methods(["POST"])
def activity_complete(request, activity_id):
    """Mark activity as complete"""
    activity = get_object_or_404(SalesActivity, id=activity_id)
    
    # Check permissions
    if not request.user.is_staff and activity.assigned_to != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    activity.mark_complete()
    
    return JsonResponse({
        'success': True,
        'activity_id': activity.id,
        'completed': activity.completed,
        'completed_date': activity.completed_date.isoformat() if activity.completed_date else None
    })

@login_required
@role_required('Admin', 'Manager')
def sales_forecast(request):
    """Sales forecasting view"""
    period_type = request.GET.get('type', 'monthly')
    
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
        
        forecast = SalesForecast.generate_forecast(period, period_type)
        forecasts.append(forecast)
    
    context = {
        'forecasts': forecasts,
        'period_type': period_type,
        'active_tab': 'forecast'
    }
    
    return render(request, 'sales/forecast.html', context)

@login_required
def team_performance(request):
    """Team performance dashboard"""
    date_range = request.GET.get('range', 'month')
    
    if date_range == 'week':
        start_date = datetime.now() - timedelta(weeks=1)
    elif date_range == 'month':
        start_date = datetime.now() - timedelta(days=30)
    elif date_range == 'quarter':
        start_date = datetime.now() - timedelta(days=90)
    else:
        start_date = datetime.now() - timedelta(days=365)
    
    team_metrics = PipelineManager.get_team_performance(
        date_range=(start_date, datetime.now())
    )
    
    context = {
        'team_metrics': team_metrics,
        'date_range': date_range,
        'active_tab': 'team'
    }
    
    return render(request, 'sales/team_performance.html', context)

@login_required
def pipeline_api(request):
    """API endpoint for pipeline data (for drag-and-drop)"""
    pipeline_data = PipelineManager.get_pipeline_data(
        user=request.user if not request.user.is_staff else None
    )
    
    # Format for frontend
    formatted_data = []
    for stage, data in pipeline_data.items():
        formatted_data.append({
            'stage': stage,
            'count': data['count'],
            'total_value': float(data['total_value']),
            'weighted_value': float(data['weighted_value']),
            'deals': data['deals']
        })
    
    return JsonResponse({'pipeline': formatted_data})