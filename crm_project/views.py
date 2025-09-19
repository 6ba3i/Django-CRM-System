# Main CRM views
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta

from customers.models import Customer, Interaction
from sales.models import Deal, SalesActivity
from analytics.data_processor import DataProcessor
from sales.pipeline_logic import PipelineManager

@login_required
def dashboard_view(request):
    """Main dashboard view"""
    # Get user-specific or all data based on role
    user_filter = request.user if not request.user.is_staff else None
    
    # Get dashboard metrics
    metrics = DataProcessor.get_dashboard_metrics(user=user_filter, period='month')
    
    # Get recent activities
    recent_activities = get_recent_activities(request.user)
    
    # Get top deals
    top_deals = Deal.objects.filter(status='Active')
    if user_filter:
        top_deals = top_deals.filter(assigned_to=user_filter)
    top_deals = top_deals.order_by('-value')[:5]
    
    # Get team performance (for managers)
    team_performance = []
    if request.user.is_staff:
        team_performance = PipelineManager.get_team_performance()[:5]
    
    # Get pipeline counts for chart
    pipeline_counts = []
    for stage, _ in PipelineManager.get_pipeline_stages():
        count = Deal.objects.filter(stage=stage, status='Active')
        if user_filter:
            count = count.filter(assigned_to=user_filter)
        pipeline_counts.append(str(count.count()))
    
    # Get revenue trend data
    revenue_labels = []
    revenue_values = []
    for i in range(5, -1, -1):
        month = datetime.now() - timedelta(days=30*i)
        revenue_labels.append(month.strftime('%b'))
        
        month_revenue = Deal.objects.filter(
            status='Won',
            updated_date__month=month.month,
            updated_date__year=month.year
        )
        if user_filter:
            month_revenue = month_revenue.filter(assigned_to=user_filter)
        
        total = month_revenue.aggregate(Sum('value'))['value__sum'] or 0
        revenue_values.append(str(float(total)))
    
    context = {
        'metrics': metrics,
        'recent_activities': recent_activities,
        'top_deals': top_deals,
        'team_performance': team_performance,
        'pipeline_counts': ','.join(pipeline_counts),
        'revenue_labels': ','.join(revenue_labels),
        'revenue_values': ','.join(revenue_values),
        'active_tab': 'dashboard'
    }
    
    return render(request, 'dashboard.html', context)

def signup_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'auth/signup.html', {'form': form})

@login_required
@require_http_methods(["GET"])
def dashboard_metrics_api(request):
    """API endpoint for dashboard metrics"""
    period = request.GET.get('period', 'month')
    user_filter = request.user if not request.user.is_staff else None
    
    metrics = DataProcessor.get_dashboard_metrics(user=user_filter, period=period)
    
    return JsonResponse(metrics)

@login_required
@require_http_methods(["GET"])
def notifications_api(request):
    """API endpoint for user notifications"""
    notifications = []
    
    # Check for overdue deals
    overdue_deals = Deal.objects.filter(
        assigned_to=request.user,
        status='Active',
        expected_close__lt=datetime.now().date()
    ).count()
    
    if overdue_deals > 0:
        notifications.append({
            'type': 'warning',
            'message': f'You have {overdue_deals} overdue deals',
            'link': '/sales/deals/?filter=overdue'
        })
    
    # Check for upcoming activities
    upcoming_activities = SalesActivity.objects.filter(
        assigned_to=request.user,
        completed=False,
        due_date__lte=datetime.now() + timedelta(days=1)
    ).count()
    
    if upcoming_activities > 0:
        notifications.append({
            'type': 'info',
            'message': f'{upcoming_activities} activities due soon',
            'link': '/sales/activities/'
        })
    
    # Check for new customer interactions
    new_interactions = Interaction.objects.filter(
        customer__assigned_to=request.user,
        date__gte=datetime.now() - timedelta(hours=24)
    ).exclude(created_by=request.user).count()
    
    if new_interactions > 0:
        notifications.append({
            'type': 'info',
            'message': f'{new_interactions} new customer interactions',
            'link': '/customers/interactions/'
        })
    
    return JsonResponse({
        'count': len(notifications),
        'notifications': notifications
    })

@login_required
def profile_view(request):
    """User profile and settings"""
    if request.method == 'POST':
        # Update user profile
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        return JsonResponse({'success': True, 'message': 'Profile updated successfully'})
    
    return render(request, 'profile.html', {
        'user': request.user,
        'active_tab': 'profile'
    })

def get_recent_activities(user):
    """Get recent activities for dashboard"""
    activities = []
    
    # Recent deals
    recent_deals = Deal.objects.filter(
        created_date__gte=datetime.now() - timedelta(days=7)
    )
    if not user.is_staff:
        recent_deals = recent_deals.filter(assigned_to=user)
    
    for deal in recent_deals[:3]:
        activities.append({
            'type': 'Deal',
            'description': f'New deal: {deal.title}',
            'user': deal.assigned_to.get_full_name() or deal.assigned_to.username,
            'time_ago': time_ago(deal.created_date)
        })
    
    # Recent customers
    recent_customers = Customer.objects.filter(
        created_date__gte=datetime.now() - timedelta(days=7)
    )
    if not user.is_staff:
        recent_customers = recent_customers.filter(assigned_to=user)
    
    for customer in recent_customers[:3]:
        activities.append({
            'type': 'Customer',
            'description': f'New customer: {customer.name}',
            'user': customer.assigned_to.get_full_name() or customer.assigned_to.username if customer.assigned_to else 'System',
            'time_ago': time_ago(customer.created_date)
        })
    
    # Recent interactions
    recent_interactions = Interaction.objects.filter(
        date__gte=datetime.now() - timedelta(days=7)
    )
    if not user.is_staff:
        recent_interactions = recent_interactions.filter(created_by=user)
    
    for interaction in recent_interactions[:2]:
        activities.append({
            'type': 'Interaction',
            'description': f'{interaction.type} with {interaction.customer.name}',
            'user': interaction.created_by.get_full_name() or interaction.created_by.username if interaction.created_by else 'System',
            'time_ago': time_ago(interaction.date)
        })
    
    # Sort by time and return top 8
    activities.sort(key=lambda x: x.get('time_ago', ''), reverse=True)
    return activities[:8]

def time_ago(date_time):
    """Convert datetime to human-readable time ago"""
    if not date_time:
        return ''
    
    # Ensure we're working with timezone-aware datetime
    if hasattr(date_time, 'tzinfo') and date_time.tzinfo is None:
        from django.utils import timezone
        date_time = timezone.make_aware(date_time)
    
    from django.utils import timezone
    now = timezone.now()
    diff = now - date_time
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours > 1 else ""} ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days > 1 else ""} ago'
    else:
        weeks = int(seconds / 604800)
        return f'{weeks} week{"s" if weeks > 1 else ""} ago'