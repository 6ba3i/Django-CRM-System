 # Business logic for pipeline
from django.db.models import Sum, Q, Count, Avg
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import Deal, PipelineHistory, SalesForecast, SalesActivity
from core.firebase_config import FirebaseManager
from core.utils import calculate_roi, get_quarter

class PipelineManager:
    """Manager for pipeline operations and analytics"""
    
    @staticmethod
    def get_pipeline_stages():
        """Get all pipeline stages with their order"""
        return [
            ('Lead', 1),
            ('Qualified', 2),
            ('Proposal', 3),
            ('Negotiation', 4),
            ('Won', 5),
            ('Lost', 6),
            ('On Hold', 7)
        ]
    
    @staticmethod
    def get_pipeline_data(user=None, date_range=None):
        """Get pipeline data for visualization"""
        deals = Deal.objects.filter(status='Active')
        
        if user:
            deals = deals.filter(assigned_to=user)
        
        if date_range:
            start_date, end_date = date_range
            deals = deals.filter(created_date__range=(start_date, end_date))
        
        # Group by stage
        pipeline_data = {}
        for stage, order in PipelineManager.get_pipeline_stages():
            stage_deals = deals.filter(stage=stage)
            pipeline_data[stage] = {
                'count': stage_deals.count(),
                'total_value': stage_deals.aggregate(total=Sum('value'))['total'] or 0,
                'weighted_value': sum(d.weighted_value for d in stage_deals),
                'deals': list(stage_deals.values('id', 'title', 'customer__name', 'value', 'probability'))
            }
        
        return pipeline_data
    
    @staticmethod
    def calculate_conversion_rates():
        """Calculate conversion rates between stages"""
        conversion_rates = {}
        stages = ['Lead', 'Qualified', 'Proposal', 'Negotiation']
        
        for i, stage in enumerate(stages):
            if i < len(stages) - 1:
                next_stage = stages[i + 1]
                
                # Count deals that moved from stage to next_stage
                moved_deals = PipelineHistory.objects.filter(
                    from_stage=stage,
                    to_stage=next_stage
                ).count()
                
                # Count all deals that were in stage
                total_deals = PipelineHistory.objects.filter(from_stage=stage).count()
                
                if total_deals > 0:
                    conversion_rates[f"{stage}_to_{next_stage}"] = (moved_deals / total_deals) * 100
                else:
                    conversion_rates[f"{stage}_to_{next_stage}"] = 0
        
        # Calculate overall win rate
        total_closed = Deal.objects.filter(status__in=['Won', 'Lost']).count()
        total_won = Deal.objects.filter(status='Won').count()
        
        if total_closed > 0:
            conversion_rates['win_rate'] = (total_won / total_closed) * 100
        else:
            conversion_rates['win_rate'] = 0
        
        return conversion_rates
    
    @staticmethod
    def calculate_velocity_metrics():
        """Calculate sales velocity and cycle time"""
        metrics = {}
        
        # Average time to close (won deals)
        won_deals = Deal.objects.filter(status='Won')
        if won_deals.exists():
            cycle_times = []
            for deal in won_deals:
                # Get the time from creation to won
                history = deal.pipeline_history.filter(to_stage='Won').first()
                if history:
                    cycle_time = (history.changed_date - deal.created_date).days
                    cycle_times.append(cycle_time)
            
            if cycle_times:
                metrics['average_cycle_time'] = sum(cycle_times) / len(cycle_times)
                metrics['min_cycle_time'] = min(cycle_times)
                metrics['max_cycle_time'] = max(cycle_times)
        
        # Average time in each stage
        stage_times = {}
        for stage, _ in PipelineManager.get_pipeline_stages():
            stage_histories = PipelineHistory.objects.filter(from_stage=stage)
            if stage_histories.exists():
                times = []
                for history in stage_histories:
                    # Get previous history entry
                    prev_history = PipelineHistory.objects.filter(
                        deal=history.deal,
                        to_stage=stage
                    ).first()
                    
                    if prev_history:
                        time_in_stage = (history.changed_date - prev_history.changed_date).days
                        times.append(time_in_stage)
                
                if times:
                    stage_times[stage] = sum(times) / len(times)
        
        metrics['stage_times'] = stage_times
        
        # Sales velocity (deals closed per month)
        last_month = datetime.now() - timedelta(days=30)
        recent_wins = Deal.objects.filter(
            status='Won',
            updated_date__gte=last_month
        ).count()
        metrics['monthly_velocity'] = recent_wins
        
        return metrics
    
    @staticmethod
    def get_pipeline_forecast(period='quarter'):
        """Generate pipeline forecast"""
        current_date = datetime.now()
        
        if period == 'quarter':
            current_quarter = get_quarter(current_date)
            current_year = current_date.year
            forecast_period = f"{current_year}-{current_quarter}"
            
            # Get deals expected to close this quarter
            quarter_start = datetime(current_year, ((int(current_quarter[1]) - 1) * 3) + 1, 1)
            if current_quarter == 'Q4':
                quarter_end = datetime(current_year + 1, 1, 1)
            else:
                quarter_end = datetime(current_year, ((int(current_quarter[1]) * 3) + 1), 1)
            
            deals = Deal.objects.filter(
                expected_close__gte=quarter_start.date(),
                expected_close__lt=quarter_end.date(),
                status='Active'
            )
        
        elif period == 'month':
            forecast_period = current_date.strftime('%Y-%m')
            month_start = datetime(current_date.year, current_date.month, 1)
            if current_date.month == 12:
                month_end = datetime(current_date.year + 1, 1, 1)
            else:
                month_end = datetime(current_date.year, current_date.month + 1, 1)
            
            deals = Deal.objects.filter(
                expected_close__gte=month_start.date(),
                expected_close__lt=month_end.date(),
                status='Active'
            )
        
        # Calculate forecast metrics
        total_pipeline = deals.aggregate(total=Sum('value'))['total'] or 0
        
        # Group by probability ranges
        forecast_breakdown = {
            'high_probability': {  # 70-100%
                'deals': deals.filter(probability__gte=70),
                'total': 0,
                'weighted': 0
            },
            'medium_probability': {  # 40-69%
                'deals': deals.filter(probability__gte=40, probability__lt=70),
                'total': 0,
                'weighted': 0
            },
            'low_probability': {  # 0-39%
                'deals': deals.filter(probability__lt=40),
                'total': 0,
                'weighted': 0
            }
        }
        
        for category, data in forecast_breakdown.items():
            data['total'] = data['deals'].aggregate(total=Sum('value'))['total'] or 0
            data['weighted'] = sum(d.weighted_value for d in data['deals'])
            data['count'] = data['deals'].count()
        
        # Calculate expected revenue
        weighted_total = sum(d['weighted'] for d in forecast_breakdown.values())
        
        return {
            'period': forecast_period,
            'total_pipeline': total_pipeline,
            'weighted_pipeline': weighted_total,
            'breakdown': forecast_breakdown,
            'deal_count': deals.count()
        }
    
    @staticmethod
    def move_deal_stage(deal, new_stage, user, notes=''):
        """Move a deal to a new stage"""
        old_stage = deal.stage
        
        # Update deal
        deal.update_stage(new_stage)
        
        # Sync with Firebase
        if deal.firebase_id:
            firebase_data = deal.to_firebase_dict()
            FirebaseManager.update_deal(deal.firebase_id, firebase_data)
        
        # Create activity log
        SalesActivity.objects.create(
            deal=deal,
            activity_type='Other',
            subject=f"Stage changed from {old_stage} to {new_stage}",
            description=notes or f"Deal moved from {old_stage} to {new_stage}",
            due_date=datetime.now(),
            completed=True,
            completed_date=datetime.now(),
            assigned_to=user
        )
        
        return deal
    
    @staticmethod
    def get_team_performance(date_range=None):
        """Get performance metrics for the sales team"""
        team_metrics = []
        
        # Get all sales users
        from django.contrib.auth.models import User
        sales_users = User.objects.filter(
            Q(groups__name='Sales') | Q(is_staff=True)
        ).distinct()
        
        for user in sales_users:
            user_deals = Deal.objects.filter(assigned_to=user)
            
            if date_range:
                start_date, end_date = date_range
                user_deals = user_deals.filter(created_date__range=(start_date, end_date))
            
            # Calculate metrics
            total_deals = user_deals.count()
            won_deals = user_deals.filter(status='Won').count()
            lost_deals = user_deals.filter(status='Lost').count()
            active_deals = user_deals.filter(status='Active').count()
            
            total_value = user_deals.filter(status='Won').aggregate(
                total=Sum('value'))['total'] or 0
            
            pipeline_value = user_deals.filter(status='Active').aggregate(
                total=Sum('value'))['total'] or 0
            
            # Win rate
            closed_deals = won_deals + lost_deals
            win_rate = (won_deals / closed_deals * 100) if closed_deals > 0 else 0
            
            # Average deal size
            avg_deal_size = (total_value / won_deals) if won_deals > 0 else 0
            
            team_metrics.append({
                'user': user,
                'total_deals': total_deals,
                'won_deals': won_deals,
                'lost_deals': lost_deals,
                'active_deals': active_deals,
                'total_revenue': total_value,
                'pipeline_value': pipeline_value,
                'win_rate': win_rate,
                'avg_deal_size': avg_deal_size
            })
        
        # Sort by total revenue
        team_metrics.sort(key=lambda x: x['total_revenue'], reverse=True)
        
        return team_metrics
    
    @staticmethod
    def get_deal_recommendations(deal):
        """Get AI-powered recommendations for a deal"""
        recommendations = []
        
        # Check if deal is stagnant
        days_in_stage = (datetime.now().date() - deal.updated_date.date()).days
        if days_in_stage > 14:
            recommendations.append({
                'type': 'warning',
                'message': f'Deal has been in {deal.stage} stage for {days_in_stage} days',
                'action': 'Schedule a follow-up activity'
            })
        
        # Check if close date is approaching
        if deal.expected_close:
            days_to_close = (deal.expected_close - datetime.now().date()).days
            if 0 < days_to_close <= 7:
                recommendations.append({
                    'type': 'urgent',
                    'message': f'Deal expected to close in {days_to_close} days',
                    'action': 'Intensify engagement and finalize terms'
                })
        
        # Check probability alignment
        expected_probabilities = {
            'Lead': (5, 20),
            'Qualified': (20, 40),
            'Proposal': (40, 60),
            'Negotiation': (60, 90)
        }
        
        if deal.stage in expected_probabilities:
            min_prob, max_prob = expected_probabilities[deal.stage]
            if deal.probability < min_prob:
                recommendations.append({
                    'type': 'info',
                    'message': f'Probability seems low for {deal.stage} stage',
                    'action': 'Review deal qualification and update probability'
                })
            elif deal.probability > max_prob:
                recommendations.append({
                    'type': 'success',
                    'message': f'High probability for {deal.stage} stage',
                    'action': 'Consider moving to next stage'
                })
        
        # Check for missing activities
        recent_activities = deal.activities.filter(
            created_date__gte=datetime.now() - timedelta(days=7)
        ).count()
        
        if recent_activities == 0:
            recommendations.append({
                'type': 'warning',
                'message': 'No recent activities on this deal',
                'action': 'Schedule a touchpoint with the customer'
            })
        
        return recommendations