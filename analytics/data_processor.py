 # Data analysis logic
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg, Q, F
from django.core.cache import cache
import json

from customers.models import Customer, Interaction
from sales.models import Deal, PipelineHistory, SalesForecast
from core.utils import get_quarter, calculate_roi

class DataProcessor:
    """Process and analyze CRM data for insights"""
    
    @staticmethod
    def get_dashboard_metrics(user=None, period='month'):
        """Get main dashboard metrics"""
        cache_key = f'dashboard_metrics_{user.id if user else "all"}_{period}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Get date range
        end_date = datetime.now()
        if period == 'week':
            start_date = end_date - timedelta(weeks=1)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'quarter':
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=365)
        
        # Base querysets
        customers = Customer.objects.all()
        deals = Deal.objects.all()
        interactions = Interaction.objects.all()
        
        if user and not user.is_staff:
            customers = customers.filter(assigned_to=user)
            deals = deals.filter(assigned_to=user)
            interactions = interactions.filter(created_by=user)
        
        # Calculate metrics
        metrics = {
            'period': period,
            'generated_at': datetime.now().isoformat(),
            
            # Customer metrics
            'total_customers': customers.count(),
            'new_customers': customers.filter(created_date__gte=start_date).count(),
            'active_customers': customers.filter(status='Active').count(),
            'customer_growth_rate': DataProcessor._calculate_growth_rate(
                customers, start_date, period
            ),
            
            # Deal metrics
            'total_deals': deals.filter(created_date__gte=start_date).count(),
            'active_deals': deals.filter(status='Active').count(),
            'won_deals': deals.filter(status='Won', updated_date__gte=start_date).count(),
            'lost_deals': deals.filter(status='Lost', updated_date__gte=start_date).count(),
            
            # Revenue metrics
            'total_revenue': deals.filter(
                status='Won', 
                updated_date__gte=start_date
            ).aggregate(total=Sum('value'))['total'] or 0,
            
            'pipeline_value': deals.filter(
                status='Active'
            ).aggregate(total=Sum('value'))['total'] or 0,
            
            'weighted_pipeline': sum(
                deal.weighted_value for deal in deals.filter(status='Active')
            ),
            
            'average_deal_size': deals.filter(
                status='Won',
                updated_date__gte=start_date
            ).aggregate(avg=Avg('value'))['avg'] or 0,
            
            # Activity metrics
            'total_interactions': interactions.filter(date__gte=start_date).count(),
            'interactions_per_customer': DataProcessor._calculate_interaction_rate(
                customers, interactions, start_date
            ),
            
            # Conversion metrics
            'win_rate': DataProcessor._calculate_win_rate(deals, start_date),
            'conversion_rate': DataProcessor._calculate_conversion_rate(
                customers, deals, start_date
            ),
            'average_sales_cycle': DataProcessor._calculate_sales_cycle(
                deals, start_date
            ),
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, metrics, 300)
        
        return metrics
    
    @staticmethod
    def _calculate_growth_rate(queryset, start_date, period):
        """Calculate growth rate for a period"""
        current_count = queryset.filter(created_date__gte=start_date).count()
        
        # Get previous period count
        if period == 'week':
            prev_start = start_date - timedelta(weeks=1)
        elif period == 'month':
            prev_start = start_date - timedelta(days=30)
        elif period == 'quarter':
            prev_start = start_date - timedelta(days=90)
        else:
            prev_start = start_date - timedelta(days=365)
        
        prev_count = queryset.filter(
            created_date__gte=prev_start,
            created_date__lt=start_date
        ).count()
        
        if prev_count > 0:
            return ((current_count - prev_count) / prev_count) * 100
        return 0
    
    @staticmethod
    def _calculate_interaction_rate(customers, interactions, start_date):
        """Calculate average interactions per customer"""
        customer_count = customers.count()
        if customer_count == 0:
            return 0
        
        interaction_count = interactions.filter(date__gte=start_date).count()
        return round(interaction_count / customer_count, 2)
    
    @staticmethod
    def _calculate_win_rate(deals, start_date):
        """Calculate win rate percentage"""
        closed_deals = deals.filter(
            Q(status='Won') | Q(status='Lost'),
            updated_date__gte=start_date
        ).count()
        
        if closed_deals == 0:
            return 0
        
        won_deals = deals.filter(
            status='Won',
            updated_date__gte=start_date
        ).count()
        
        return round((won_deals / closed_deals) * 100, 2)
    
    @staticmethod
    def _calculate_conversion_rate(customers, deals, start_date):
        """Calculate customer to deal conversion rate"""
        new_customers = customers.filter(created_date__gte=start_date).count()
        if new_customers == 0:
            return 0
        
        new_deals = deals.filter(created_date__gte=start_date).count()
        return round((new_deals / new_customers) * 100, 2)
    
    @staticmethod
    def _calculate_sales_cycle(deals, start_date):
        """Calculate average sales cycle in days"""
        won_deals = deals.filter(
            status='Won',
            updated_date__gte=start_date
        )
        
        if not won_deals.exists():
            return 0
        
        cycle_times = []
        for deal in won_deals:
            # Get the time from creation to won
            cycle_time = (deal.updated_date - deal.created_date).days
            cycle_times.append(cycle_time)
        
        return round(sum(cycle_times) / len(cycle_times), 1) if cycle_times else 0
    
    @staticmethod
    def get_sales_trends(period='month', user=None):
        """Get sales trends data"""
        trends = {
            'labels': [],
            'revenue': [],
            'deals': [],
            'customers': [],
            'win_rate': []
        }
        
        # Generate data points
        num_points = 12 if period == 'month' else 4
        
        for i in range(num_points - 1, -1, -1):
            if period == 'month':
                date = datetime.now() - timedelta(days=30*i)
                label = date.strftime('%b')
            else:
                date = datetime.now() - timedelta(days=90*i)
                label = f'Q{((date.month-1)//3)+1} {date.year}'
            
            trends['labels'].append(label)
            
            # Calculate metrics for this period
            if period == 'month':
                period_start = datetime(date.year, date.month, 1)
                if date.month == 12:
                    period_end = datetime(date.year + 1, 1, 1)
                else:
                    period_end = datetime(date.year, date.month + 1, 1)
            else:
                quarter = ((date.month-1)//3)+1
                period_start = datetime(date.year, (quarter-1)*3+1, 1)
                if quarter == 4:
                    period_end = datetime(date.year + 1, 1, 1)
                else:
                    period_end = datetime(date.year, quarter*3+1, 1)
            
            # Get data for period
            deals = Deal.objects.filter(
                updated_date__gte=period_start,
                updated_date__lt=period_end
            )
            
            if user and not user.is_staff:
                deals = deals.filter(assigned_to=user)
            
            # Revenue
            revenue = deals.filter(status='Won').aggregate(
                total=Sum('value'))['total'] or 0
            trends['revenue'].append(float(revenue))
            
            # Deal count
            trends['deals'].append(deals.filter(status='Won').count())
            
            # New customers
            customers = Customer.objects.filter(
                created_date__gte=period_start,
                created_date__lt=period_end
            )
            if user and not user.is_staff:
                customers = customers.filter(assigned_to=user)
            trends['customers'].append(customers.count())
            
            # Win rate
            closed = deals.filter(Q(status='Won') | Q(status='Lost')).count()
            won = deals.filter(status='Won').count()
            win_rate = (won / closed * 100) if closed > 0 else 0
            trends['win_rate'].append(round(win_rate, 2))
        
        return trends
    
    @staticmethod
    def get_pipeline_analytics():
        """Get detailed pipeline analytics"""
        analytics = {
            'stage_metrics': {},
            'velocity_metrics': {},
            'bottlenecks': [],
            'opportunities': []
        }
        
        # Analyze each stage
        stages = ['Lead', 'Qualified', 'Proposal', 'Negotiation']
        for stage in stages:
            stage_deals = Deal.objects.filter(stage=stage, status='Active')
            
            analytics['stage_metrics'][stage] = {
                'count': stage_deals.count(),
                'value': stage_deals.aggregate(total=Sum('value'))['total'] or 0,
                'avg_time': DataProcessor._calculate_stage_time(stage),
                'conversion_rate': DataProcessor._calculate_stage_conversion(stage)
            }
        
        # Velocity metrics
        analytics['velocity_metrics'] = {
            'average_cycle_time': DataProcessor._calculate_average_cycle_time(),
            'stage_velocity': DataProcessor._calculate_stage_velocity(),
            'deal_velocity': DataProcessor._calculate_deal_velocity()
        }
        
        # Identify bottlenecks
        for stage, metrics in analytics['stage_metrics'].items():
            if metrics['avg_time'] > 14:  # More than 2 weeks
                analytics['bottlenecks'].append({
                    'stage': stage,
                    'avg_time': metrics['avg_time'],
                    'message': f'Deals spending too long in {stage} stage',
                    'recommendation': 'Review qualification criteria and accelerate decision-making'
                })
        
        # Identify opportunities
        high_value_deals = Deal.objects.filter(
            status='Active',
            value__gte=10000,
            probability__gte=60
        ).count()
        
        if high_value_deals > 0:
            analytics['opportunities'].append({
                'type': 'high_value',
                'count': high_value_deals,
                'message': f'{high_value_deals} high-value deals with good probability',
                'action': 'Focus resources on closing these deals'
            })
        
        return analytics
    
    @staticmethod
    def _calculate_stage_time(stage):
        """Calculate average time in a specific stage"""
        histories = PipelineHistory.objects.filter(from_stage=stage)
        
        if not histories.exists():
            return 0
        
        times = []
        for history in histories[:50]:  # Sample last 50 for performance
            # Find when deal entered this stage
            entry = PipelineHistory.objects.filter(
                deal=history.deal,
                to_stage=stage
            ).first()
            
            if entry:
                time_in_stage = (history.changed_date - entry.changed_date).days
                times.append(time_in_stage)
        
        return round(sum(times) / len(times), 1) if times else 0
    
    @staticmethod
    def _calculate_stage_conversion(stage):
        """Calculate conversion rate from stage to next"""
        stage_map = {
            'Lead': 'Qualified',
            'Qualified': 'Proposal',
            'Proposal': 'Negotiation',
            'Negotiation': 'Won'
        }
        
        if stage not in stage_map:
            return 0
        
        next_stage = stage_map[stage]
        
        # Count movements
        from_stage = PipelineHistory.objects.filter(from_stage=stage).count()
        to_next = PipelineHistory.objects.filter(
            from_stage=stage,
            to_stage=next_stage
        ).count()
        
        if from_stage == 0:
            return 0
        
        return round((to_next / from_stage) * 100, 2)
    
    @staticmethod
    def _calculate_average_cycle_time():
        """Calculate average sales cycle time"""
        won_deals = Deal.objects.filter(status='Won')[:50]  # Sample
        
        if not won_deals.exists():
            return 0
        
        cycle_times = []
        for deal in won_deals:
            cycle_time = (deal.updated_date - deal.created_date).days
            cycle_times.append(cycle_time)
        
        return round(sum(cycle_times) / len(cycle_times), 1) if cycle_times else 0
    
    @staticmethod
    def _calculate_stage_velocity():
        """Calculate how fast deals move through stages"""
        last_month = datetime.now() - timedelta(days=30)
        
        movements = PipelineHistory.objects.filter(
            changed_date__gte=last_month
        ).count()
        
        return movements  # Number of stage changes in last 30 days
    
    @staticmethod
    def _calculate_deal_velocity():
        """Calculate deal closing velocity"""
        last_month = datetime.now() - timedelta(days=30)
        
        closed_deals = Deal.objects.filter(
            Q(status='Won') | Q(status='Lost'),
            updated_date__gte=last_month
        ).count()
        
        return closed_deals  # Deals closed in last 30 days
    
    @staticmethod
    def export_analytics_report(format='pdf'):
        """Export comprehensive analytics report"""
        # Gather all analytics data
        report_data = {
            'generated_date': datetime.now(),
            'dashboard_metrics': DataProcessor.get_dashboard_metrics(),
            'sales_trends': DataProcessor.get_sales_trends(),
            'pipeline_analytics': DataProcessor.get_pipeline_analytics(),
            'team_performance': DataProcessor._get_team_performance()
        }
        
        if format == 'pdf':
            # Generate PDF report (would use ReportLab or similar)
            pass
        elif format == 'excel':
            # Generate Excel report using pandas
            df_metrics = pd.DataFrame([report_data['dashboard_metrics']])
            df_trends = pd.DataFrame(report_data['sales_trends'])
            
            with pd.ExcelWriter('analytics_report.xlsx') as writer:
                df_metrics.to_excel(writer, sheet_name='Dashboard')
                df_trends.to_excel(writer, sheet_name='Trends')
        
        return report_data
    
    @staticmethod
    def _get_team_performance():
        """Get team performance metrics"""
        from django.contrib.auth.models import User
        
        team_data = []
        
        sales_users = User.objects.filter(
            Q(groups__name='Sales') | Q(is_staff=True)
        ).distinct()
        
        for user in sales_users:
            user_deals = Deal.objects.filter(assigned_to=user)
            
            team_data.append({
                'user': user.get_full_name() or user.username,
                'total_revenue': user_deals.filter(
                    status='Won'
                ).aggregate(total=Sum('value'))['total'] or 0,
                'deals_won': user_deals.filter(status='Won').count(),
                'deals_lost': user_deals.filter(status='Lost').count(),
                'active_deals': user_deals.filter(status='Active').count(),
                'win_rate': DataProcessor._calculate_win_rate(user_deals, datetime.now() - timedelta(days=30))
            })
        
        return sorted(team_data, key=lambda x: x['total_revenue'], reverse=True)