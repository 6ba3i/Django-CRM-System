# Main CRM views
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Count, Q
from django.contrib import messages
from django.core.management import execute_from_command_line
from datetime import datetime, timedelta
import logging
import os

from core.firebase_config import FirebaseManager
logger = logging.getLogger(__name__)

@login_required
def dashboard_view(request):
    """Main dashboard view using Firebase data"""
    try:
        # Get Firebase data
        customers = FirebaseManager.get_customers(limit=100)
        deals = FirebaseManager.get_deals(limit=100)
        
        # Calculate basic metrics
        total_customers = len(customers)
        total_deals = len(deals)
        active_deals = len([d for d in deals if d.get('status') == 'Active'])
        total_revenue = sum(d.get('value', 0) for d in deals if d.get('status') == 'Won')
        pipeline_value = sum(d.get('value', 0) for d in deals if d.get('status') == 'Active')
        
        # Calculate win rate
        closed_deals = [d for d in deals if d.get('status') in ['Won', 'Lost']]
        won_deals = [d for d in deals if d.get('status') == 'Won']
        win_rate = (len(won_deals) / len(closed_deals) * 100) if closed_deals else 0
        
        # Get top deals
        top_deals = sorted(
            [d for d in deals if d.get('status') == 'Active'],
            key=lambda x: x.get('value', 0),
            reverse=True
        )[:5]
        
        # Pipeline counts for chart
        pipeline_stages = ['Lead', 'Qualified', 'Proposal', 'Negotiation', 'Won']
        pipeline_counts = []
        for stage in pipeline_stages:
            count = len([d for d in deals if d.get('stage') == stage and d.get('status') == 'Active'])
            pipeline_counts.append(str(count))
        
        # Revenue trend (mock data for now)
        revenue_labels = []
        revenue_values = []
        for i in range(5, -1, -1):
            month = datetime.now() - timedelta(days=30*i)
            revenue_labels.append(month.strftime('%b'))
            # Mock revenue data - in real implementation, filter by date
            revenue_values.append(str(float(total_revenue / 6)))
        
        metrics = {
            'total_customers': total_customers,
            'new_customers': min(10, total_customers),  # Mock value
            'active_deals': active_deals,
            'total_deals': total_deals,
            'total_revenue': total_revenue,
            'pipeline_value': pipeline_value,
            'win_rate': round(win_rate, 1),
            'won_deals': len(won_deals),
            'lost_deals': len(closed_deals) - len(won_deals),
            'average_deal_size': total_revenue / len(won_deals) if won_deals else 0,
            'period': 'month'
        }
        
        # Recent activities (mock data)
        recent_activities = [
            {
                'type': 'Deal',
                'description': f'New deal: {deal.get("title", "Unknown")}',
                'user': request.user.get_full_name() or request.user.username,
                'time_ago': '2 hours ago'
            } for deal in top_deals[:3]
        ]
        
        context = {
            'metrics': metrics,
            'recent_activities': recent_activities,
            'top_deals': [{'title': d.get('title'), 'value': d.get('value'), 'stage': d.get('stage')} for d in top_deals],
            'team_performance': [],  # Will be implemented later
            'pipeline_counts': ','.join(pipeline_counts),
            'revenue_labels': ','.join(revenue_labels),
            'revenue_values': ','.join(revenue_values),
            'active_tab': 'dashboard'
        }
        
        return render(request, 'dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        # Fallback to empty dashboard
        context = {
            'metrics': {
                'total_customers': 0,
                'new_customers': 0,
                'active_deals': 0,
                'total_deals': 0,
                'total_revenue': 0,
                'pipeline_value': 0,
                'win_rate': 0,
                'won_deals': 0,
                'lost_deals': 0,
                'average_deal_size': 0,
                'period': 'month'
            },
            'recent_activities': [],
            'top_deals': [],
            'team_performance': [],
            'pipeline_counts': '0,0,0,0,0',
            'revenue_labels': 'Jan,Feb,Mar,Apr,May,Jun',
            'revenue_values': '0,0,0,0,0,0',
            'active_tab': 'dashboard'
        }
        messages.warning(request, "Dashboard data could not be loaded. Please check Firebase connection.")
        return render(request, 'dashboard.html', context)

@login_required
@require_http_methods(["GET"])
def dashboard_metrics_api(request):
    """API endpoint for dashboard metrics"""
    try:
        customers = FirebaseManager.get_customers(limit=100)
        deals = FirebaseManager.get_deals(limit=100)
        
        metrics = {
            'total_customers': len(customers),
            'active_deals': len([d for d in deals if d.get('status') == 'Active']),
            'total_revenue': sum(d.get('value', 0) for d in deals if d.get('status') == 'Won'),
            'pipeline_value': sum(d.get('value', 0) for d in deals if d.get('status') == 'Active'),
        }
        
        return JsonResponse(metrics)
    except Exception as e:
        logger.error(f"Metrics API error: {e}")
        return JsonResponse({'error': 'Could not load metrics'}, status=500)

@login_required
@require_http_methods(["GET"])
def notifications_api(request):
    """API endpoint for user notifications"""
    notifications = []
    
    try:
        deals = FirebaseManager.get_deals()
        
        # Check for high-value deals
        high_value_deals = [d for d in deals if d.get('value', 0) > 100000 and d.get('status') == 'Active']
        if high_value_deals:
            notifications.append({
                'type': 'info',
                'message': f'{len(high_value_deals)} high-value deals in pipeline',
                'link': '/sales/deals/'
            })
        
        # Check for deals in negotiation
        negotiation_deals = [d for d in deals if d.get('stage') == 'Negotiation']
        if negotiation_deals:
            notifications.append({
                'type': 'warning',
                'message': f'{len(negotiation_deals)} deals in negotiation stage',
                'link': '/sales/deals/'
            })
    
    except Exception as e:
        logger.error(f"Notifications API error: {e}")
    
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
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'profile.html', {
        'user': request.user,
        'active_tab': 'profile'
    })

@require_http_methods(["POST"])
def initialize_system(request):
    """Initialize the entire CRM system"""
    try:
        # Run Django migrations
        logger.info("Running Django migrations...")
        os.system("python manage.py migrate")
        
        # Create superuser if doesn't exist
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@crm.local',
                password='admin123'
            )
            logger.info("Created superuser: admin/admin123")
        
        # Create groups
        groups = ['Sales', 'Manager', 'Admin']
        for group_name in groups:
            Group.objects.get_or_create(name=group_name)
        
        # Set up Google OAuth if credentials are provided
        google_client_id = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
        google_client_secret = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET')
        
        if google_client_id and google_client_secret:
            from allauth.socialaccount.models import SocialApp
            from django.contrib.sites.models import Site
            
            # Get or create the default site
            site, created = Site.objects.get_or_create(
                id=1,
                defaults={
                    'domain': '127.0.0.1:8000',
                    'name': 'CRM Pro Local'
                }
            )
            
            # Create or update Google OAuth app
            google_app, created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google OAuth',
                    'client_id': google_client_id,
                    'secret': google_client_secret,
                }
            )
            
            if not created:
                google_app.client_id = google_client_id
                google_app.secret = google_client_secret
                google_app.save()
            
            # Associate with site
            google_app.sites.clear()
            google_app.sites.add(site)
            
            logger.info("Google OAuth configured successfully")
        else:
            logger.warning("Google OAuth credentials not found in environment variables")
        
        # Initialize Firebase
        if FirebaseManager.is_enabled():
            FirebaseManager.initialize_collections()
            FirebaseManager.create_sample_data()
            logger.info("Firebase initialized successfully")
        else:
            logger.warning("Firebase not enabled")
        
        return JsonResponse({
            'success': True,
            'message': 'System initialized successfully!',
            'firebase_enabled': FirebaseManager.is_enabled(),
            'google_oauth_enabled': bool(google_client_id and google_client_secret)
        })
        
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)