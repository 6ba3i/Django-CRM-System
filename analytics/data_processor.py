# Data processing utilities for analytics
from django.db.models import Sum, Count, Avg, Q
from django.contrib.auth.models import User
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
import json
from collections import defaultdict

class DataProcessor:
    """Processes data for analytics and reporting"""
    
    @staticmethod
    def get_dashboard_metrics(user=None, period='month'):
        """Get comprehensive dashboard metrics"""
        from customers.models import Customer
        from sales.models import Deal, SalesActivity
        
        # Date range calculation
        end_date = datetime.now()
        if period == 'today':
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date = end_date - timedelta(weeks=1)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'quarter':
            start_date = end_date - timedelta(days=90)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Filter data by user if specified
        customers = Customer.objects.all()
        deals = Deal.objects.all()
        activities = SalesActivity.objects.all()
        
        if user and not user.is_staff:
            customers = customers.filter(assigned_to=user)
            deals = deals.filter(assigned_to=user)
            activities = activities.filter(assigned_to=user)
        
        # Customer metrics
        customer_metrics = {
            'total': customers.count(),
            'new_period': customers.filter(created_date__gte=start_date).count(),
            'by_status': {
                status[0]: customers.filter(status=status[0]).count()
                for status in Customer.STATUS_CHOICES
            },
            'conversion_rate': 0
        }
        
        # Calculate conversion rate (Active customers / Total customers)
        active_customers = customers.filter(status='Active').count()
        if customer_metrics['total'] > 0:
            customer_metrics['conversion_rate'] = round(
                (active_customers / customer_metrics['total']) * 100, 2
            )
        
        # Deal metrics
        deal_metrics = {
            'total': deals.count(),
            'active': deals.filter(status='Active').count(),
            'won': deals.filter(status='Won').count(),
            'lost': deals.filter(status='Lost').count(),
            'total_value': deals.aggregate(total=Sum('value'))['total'] or 0,
            'won_value': deals.filter(status='Won').aggregate(total=Sum('value'))['total'] or 0,
            'pipeline_value': deals.filter(status='Active').aggregate(total=Sum('value'))['total'] or 0,
            'avg_deal_size': deals.aggregate(avg=Avg('value'))['avg'] or 0,
            'win_rate': 0
        }
        
        # Calculate win rate
        closed_deals = deal_metrics['won'] + deal_metrics['lost']
        if closed_deals > 0:
            deal_metrics['win_rate'] = round((deal_metrics['won'] / closed_deals) * 100, 2)
        
        # Activity metrics
        activity_metrics = {
            'total': activities.count(),
            'completed': activities.filter(completed=True).count(),
            'pending': activities.filter(completed=False).count(),
            'overdue': activities.filter(
                completed=False,
                due_date__lt=datetime.now()
            ).count(),
            'completion_rate': 0
        }
        
        if activity_metrics['total'] > 0:
            activity_metrics['completion_rate'] = round(
                (activity_metrics['completed'] / activity_metrics['total']) * 100, 2
            )
        
        # Revenue metrics (from won deals)
        revenue_metrics = {
            'total': deal_metrics['won_value'],
            'period': deals.filter(
                status='Won',
                updated_date__gte=start_date
            ).aggregate(total=Sum('value'))['total'] or 0,
            'forecast': deals.filter(
                status='Active',
                probability__gte=70
            ).aggregate(total=Sum('value'))['total'] or 0
        }
        
        return {
            'customers': customer_metrics,
            'deals': deal_metrics,
            'activities': activity_metrics,
            'revenue': revenue_metrics,
            'period': period,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
    
    @staticmethod
    def get_sales_trends(period='month', user=None):
        """Get sales trends over time"""
        from sales.models import Deal
        
        deals = Deal.objects.all()
        if user and not user.is_staff:
            deals = deals.filter(assigned_to=user)
        
        # Determine date range and grouping
        end_date = datetime.now()
        if period == 'week':
            start_date = end_date - timedelta(weeks=12)  # 12 weeks
            date_format = '%Y-W%U'  # Week format
        elif period == 'month':
            start_date = end_date - timedelta(days=365)  # 12 months
            date_format = '%Y-%m'  # Month format
        elif period == 'quarter':
            start_date = end_date - timedelta(days=365*2)  # 2 years
            date_format = '%Y-Q'  # Quarter format
        else:
            start_date = end_date - timedelta(days=365)
            date_format = '%Y-%m'
        
        # Filter deals by date range
        deals = deals.filter(created_date__gte=start_date)
        
        # Group data by time period
        trends = defaultdict(lambda: {
            'revenue': 0,
            'deals': 0,
            'won_deals': 0,
            'pipeline_value': 0
        })
        
        for deal in deals:
            # Format date based on period
            if period == 'quarter':
                quarter = (deal.created_date.month - 1) // 3 + 1
                period_key = f"{deal.created_date.year}-Q{quarter}"
            else:
                period_key = deal.created_date.strftime(date_format)
            
            trends[period_key]['deals'] += 1
            
            if deal.status == 'Won':
                trends[period_key]['revenue'] += float(deal.value)
                trends[period_key]['won_deals'] += 1
            elif deal.status == 'Active':
                trends[period_key]['pipeline_value'] += float(deal.value)
        
        # Convert to lists for charting
        sorted_periods = sorted(trends.keys())
        
        return {
            'labels': sorted_periods,
            'revenue': [trends[period]['revenue'] for period in sorted_periods],
            'deals': [trends[period]['deals'] for period in sorted_periods],
            'won_deals': [trends[period]['won_deals'] for period in sorted_periods],
            'pipeline_value': [trends[period]['pipeline_value'] for period in sorted_periods]
        }
    
    @staticmethod
    def get_pipeline_analytics():
        """Get detailed pipeline analytics"""
        from sales.models import Deal, PipelineHistory
        
        # Current pipeline distribution
        pipeline_dist = {}
        for stage_choice in Deal.STAGE_CHOICES:
            stage = stage_choice[0]
            stage_deals = Deal.objects.filter(stage=stage, status='Active')
            
            pipeline_dist[stage] = {
                'count': stage_deals.count(),
                'value': stage_deals.aggregate(total=Sum('value'))['total'] or 0,
                'weighted_value': sum(deal.weighted_value for deal in stage_deals),
                'avg_probability': stage_deals.aggregate(avg=Avg('probability'))['avg'] or 0
            }
        
        # Velocity analysis (average time in each stage)
        velocity = {}
        for stage_choice in Deal.STAGE_CHOICES:
            stage = stage_choice[0]
            
            # Get moves FROM this stage
            moves = PipelineHistory.objects.filter(from_stage=stage)
            
            if moves.exists():
                total_days = 0
                count = 0
                
                for move in moves:
                    # Find when deal entered this stage
                    entry = PipelineHistory.objects.filter(
                        deal=move.deal,
                        to_stage=stage,
                        changed_date__lt=move.changed_date
                    ).order_by('-changed_date').first()
                    
                    if entry:
                        days_in_stage = (move.changed_date - entry.changed_date).days
                        total_days += days_in_stage
                        count += 1
                
                velocity[stage] = {
                    'avg_days': round(total_days / count, 1) if count > 0 else 0,
                    'sample_size': count
                }
            else:
                velocity[stage] = {'avg_days': 0, 'sample_size': 0}
        
        # Conversion rates between stages
        conversions = {}
        for stage_choice in Deal.STAGE_CHOICES:
            from_stage = stage_choice[0]
            
            total_from = PipelineHistory.objects.filter(from_stage=from_stage).count()
            if total_from > 0:
                conversions[from_stage] = {}
                
                for to_stage_choice in Deal.STAGE_CHOICES:
                    to_stage = to_stage_choice[0]
                    count = PipelineHistory.objects.filter(
                        from_stage=from_stage,
                        to_stage=to_stage
                    ).count()
                    
                    conversions[from_stage][to_stage] = round((count / total_from) * 100, 1)
        
        return {
            'distribution': pipeline_dist,
            'velocity': velocity,
            'conversions': conversions,
            'total_pipeline_value': sum(stage['value'] for stage in pipeline_dist.values()),
            'total_weighted_value': sum(stage['weighted_value'] for stage in pipeline_dist.values())
        }
    
    @staticmethod
    def export_analytics_report(format='json'):
        """Export comprehensive analytics report"""
        from customers.models import Customer
        from sales.models import Deal, SalesActivity
        
        # Gather all data
        customers = Customer.objects.all()
        deals = Deal.objects.all()
        activities = SalesActivity.objects.all()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'format': format,
            'summary': {
                'total_customers': customers.count(),
                'total_deals': deals.count(),
                'total_activities': activities.count(),
                'total_revenue': deals.filter(status='Won').aggregate(
                    total=Sum('value'))['total'] or 0
            },
            'customers': {
                'by_status': {
                    status[0]: customers.filter(status=status[0]).count()
                    for status in Customer.STATUS_CHOICES
                },
                'by_month': DataProcessor._group_by_month(customers, 'created_date'),
                'top_by_value': [
                    {
                        'name': customer.name,
                        'company': customer.company,
                        'total_deals': customer.deals.count(),
                        'total_value': customer.deals.aggregate(
                            total=Sum('value'))['total'] or 0
                    }
                    for customer in customers.annotate(
                        deal_value=Sum('deals__value')
                    ).order_by('-deal_value')[:10]
                ]
            },
            'deals': {
                'by_stage': {
                    stage[0]: deals.filter(stage=stage[0]).count()
                    for stage in Deal.STAGE_CHOICES
                },
                'by_status': {
                    status[0]: deals.filter(status=status[0]).count()
                    for status in Deal.STATUS_CHOICES
                },
                'by_month': DataProcessor._group_by_month(deals, 'created_date'),
                'largest_deals': [
                    {
                        'title': deal.title,
                        'customer': deal.customer.name,
                        'value': float(deal.value),
                        'stage': deal.stage,
                        'probability': deal.probability
                    }
                    for deal in deals.order_by('-value')[:10]
                ]
            },
            'performance': DataProcessor.get_dashboard_metrics(),
            'trends': DataProcessor.get_sales_trends(),
            'pipeline': DataProcessor.get_pipeline_analytics()
        }
        
        return report
    
    @staticmethod
    def _group_by_month(queryset, date_field):
        """Helper method to group queryset by month"""
        monthly_data = defaultdict(int)
        
        for obj in queryset:
            date_value = getattr(obj, date_field)
            if isinstance(date_value, datetime):
                month_key = date_value.strftime('%Y-%m')
            else:
                month_key = date_value.strftime('%Y-%m')
            monthly_data[month_key] += 1
        
        return dict(monthly_data)
    
    @staticmethod
    def get_user_performance(user_id):
        """Get performance metrics for a specific user"""
        from customers.models import Customer
        from sales.models import Deal, SalesActivity
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
        
        # Get user's data
        customers = Customer.objects.filter(assigned_to=user)
        deals = Deal.objects.filter(assigned_to=user)
        activities = SalesActivity.objects.filter(assigned_to=user)
        
        # Calculate metrics
        performance = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name()
            },
            'customers': {
                'total': customers.count(),
                'active': customers.filter(status='Active').count(),
                'conversion_rate': 0
            },
            'deals': {
                'total': deals.count(),
                'won': deals.filter(status='Won').count(),
                'lost': deals.filter(status='Lost').count(),
                'pipeline_value': deals.filter(status='Active').aggregate(
                    total=Sum('value'))['total'] or 0,
                'won_value': deals.filter(status='Won').aggregate(
                    total=Sum('value'))['total'] or 0,
                'avg_deal_size': deals.aggregate(avg=Avg('value'))['avg'] or 0,
                'win_rate': 0
            },
            'activities': {
                'total': activities.count(),
                'completed': activities.filter(completed=True).count(),
                'completion_rate': 0
            }
        }
        
        # Calculate rates
        if performance['customers']['total'] > 0:
            performance['customers']['conversion_rate'] = round(
                (performance['customers']['active'] / performance['customers']['total']) * 100, 2
            )
        
        closed_deals = performance['deals']['won'] + performance['deals']['lost']
        if closed_deals > 0:
            performance['deals']['win_rate'] = round(
                (performance['deals']['won'] / closed_deals) * 100, 2
            )
        
        if performance['activities']['total'] > 0:
            performance['activities']['completion_rate'] = round(
                (performance['activities']['completed'] / performance['activities']['total']) * 100, 2
            )
        
        return performance
    
    @staticmethod
    def get_forecast_data(periods=6, period_type='monthly'):
        """Generate forecast data for given periods"""
        from sales.models import Deal, SalesForecast
        
        forecasts = []
        
        for i in range(periods):
            if period_type == 'monthly':
                forecast_date = datetime.now() + timedelta(days=30*i)
                period_key = forecast_date.strftime('%Y-%m')
            elif period_type == 'quarterly':
                forecast_date = datetime.now() + timedelta(days=90*i)
                quarter = ((forecast_date.month - 1) // 3) + 1
                period_key = f"{forecast_date.year}-Q{quarter}"
            else:  # yearly
                forecast_date = datetime.now() + timedelta(days=365*i)
                period_key = str(forecast_date.year)
            
            # Generate or get existing forecast
            try:
                forecast = SalesForecast.objects.get(
                    period=period_key,
                    forecast_type=period_type
                )
            except SalesForecast.DoesNotExist:
                forecast = SalesForecast.generate_forecast(period_key, period_type)
            
            forecasts.append({
                'period': period_key,
                'total_pipeline': float(forecast.total_pipeline),
                'weighted_pipeline': float(forecast.weighted_pipeline),
                'expected_revenue': float(forecast.expected_revenue),
                'actual_revenue': float(forecast.actual_revenue) if forecast.actual_revenue else None
            })
        
        return forecasts