# Sales pipeline business logic
from django.db.models import Q, Sum, Count, Avg
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

class PipelineManager:
    """Manages sales pipeline operations and analytics"""
    
    # Stage conversion probabilities
    STAGE_PROBABILITIES = {
        'Lead': 10,
        'Qualified': 25,
        'Proposal': 50,
        'Negotiation': 75,
        'Won': 100,
        'Lost': 0,
        'On Hold': 0
    }
    
    @staticmethod
    def get_pipeline_data(user=None, date_range=None):
        """Get pipeline data grouped by stage"""
        from .models import Deal
        
        deals = Deal.objects.filter(status='Active')
        
        if user:
            deals = deals.filter(assigned_to=user)
        
        if date_range:
            start_date, end_date = date_range
            deals = deals.filter(created_date__range=(start_date, end_date))
        
        pipeline_data = {}
        
        for stage_choice in Deal.STAGE_CHOICES:
            stage = stage_choice[0]
            stage_deals = deals.filter(stage=stage)
            
            pipeline_data[stage] = {
                'count': stage_deals.count(),
                'total_value': stage_deals.aggregate(total=Sum('value'))['total'] or 0,
                'weighted_value': sum(deal.weighted_value for deal in stage_deals),
                'deals': [{
                    'id': deal.id,
                    'title': deal.title,
                    'customer': deal.customer.name,
                    'value': float(deal.value),
                    'probability': deal.probability,
                    'expected_close': deal.expected_close.isoformat() if deal.expected_close else None
                } for deal in stage_deals[:10]]  # Limit to 10 for performance
            }
        
        return pipeline_data
    
    @staticmethod
    def calculate_conversion_rates():
        """Calculate conversion rates between pipeline stages"""
        from .models import PipelineHistory
        
        # Get all stage transitions from history
        transitions = PipelineHistory.objects.values('from_stage', 'to_stage').annotate(
            count=Count('id')
        )
        
        conversion_rates = {}
        stage_totals = {}
        
        # Count total transitions from each stage
        for transition in transitions:
            from_stage = transition['from_stage']
            count = transition['count']
            
            if from_stage not in stage_totals:
                stage_totals[from_stage] = 0
            stage_totals[from_stage] += count
        
        # Calculate conversion rates
        for transition in transitions:
            from_stage = transition['from_stage']
            to_stage = transition['to_stage']
            count = transition['count']
            
            if from_stage not in conversion_rates:
                conversion_rates[from_stage] = {}
            
            if stage_totals[from_stage] > 0:
                rate = (count / stage_totals[from_stage]) * 100
                conversion_rates[from_stage][to_stage] = round(rate, 2)
        
        return conversion_rates
    
    @staticmethod
    def calculate_velocity_metrics():
        """Calculate how fast deals move through pipeline"""
        from .models import Deal, PipelineHistory
        
        velocity_metrics = {}
        
        for stage_choice in Deal.STAGE_CHOICES:
            stage = stage_choice[0]
            
            # Get deals that moved FROM this stage
            stage_histories = PipelineHistory.objects.filter(from_stage=stage)
            
            if stage_histories.exists():
                # Calculate average time in stage
                total_time = 0
                count = 0
                
                for history in stage_histories:
                    # Find when deal entered this stage
                    previous_history = PipelineHistory.objects.filter(
                        deal=history.deal,
                        to_stage=stage,
                        changed_date__lt=history.changed_date
                    ).order_by('-changed_date').first()
                    
                    if previous_history:
                        time_in_stage = (history.changed_date - previous_history.changed_date).days
                        total_time += time_in_stage
                        count += 1
                
                avg_time = total_time / count if count > 0 else 0
                velocity_metrics[stage] = {
                    'avg_days': round(avg_time, 1),
                    'sample_size': count
                }
            else:
                velocity_metrics[stage] = {
                    'avg_days': 0,
                    'sample_size': 0
                }
        
        return velocity_metrics
    
    @staticmethod
    def get_pipeline_forecast(period='quarter'):
        """Generate pipeline forecast"""
        from .models import Deal
        
        # Get deals likely to close in the period
        end_date = datetime.now()
        
        if period == 'month':
            end_date += timedelta(days=30)
        elif period == 'quarter':
            end_date += timedelta(days=90)
        elif period == 'year':
            end_date += timedelta(days=365)
        
        # Get active deals expected to close in period
        deals = Deal.objects.filter(
            status='Active',
            expected_close__lte=end_date.date(),
            expected_close__gte=datetime.now().date()
        )
        
        forecast = {
            'period': period,
            'total_deals': deals.count(),
            'total_value': deals.aggregate(total=Sum('value'))['total'] or 0,
            'weighted_value': sum(deal.weighted_value for deal in deals),
            'high_probability': deals.filter(probability__gte=70).aggregate(
                total=Sum('value'))['total'] or 0,
            'by_stage': {}
        }
        
        # Group by stage
        for stage_choice in Deal.STAGE_CHOICES:
            stage = stage_choice[0]
            stage_deals = deals.filter(stage=stage)
            
            forecast['by_stage'][stage] = {
                'count': stage_deals.count(),
                'value': stage_deals.aggregate(total=Sum('value'))['total'] or 0,
                'weighted_value': sum(deal.weighted_value for deal in stage_deals)
            }
        
        return forecast
    
    @staticmethod
    def move_deal_stage(deal, new_stage, user, notes=''):
        """Move a deal to a new stage"""
        from .models import PipelineHistory
        
        old_stage = deal.stage
        
        if old_stage != new_stage:
            # Update deal
            deal.stage = new_stage
            deal.probability = PipelineManager.STAGE_PROBABILITIES.get(new_stage, deal.probability)
            
            # Update status based on stage
            if new_stage == 'Won':
                deal.status = 'Won'
            elif new_stage == 'Lost':
                deal.status = 'Lost'
            elif new_stage == 'On Hold':
                deal.status = 'On Hold'
            else:
                deal.status = 'Active'
            
            deal.save()
            
            # Create history record
            PipelineHistory.objects.create(
                deal=deal,
                from_stage=old_stage,
                to_stage=new_stage,
                changed_by=user,
                notes=notes
            )
            
            return True
        
        return False
    
    @staticmethod
    def get_deal_recommendations(deal):
        """Get AI-powered recommendations for a deal"""
        recommendations = []
        
        # Time-based recommendations
        if deal.expected_close:
            days_to_close = (deal.expected_close - datetime.now().date()).days
            
            if days_to_close < 0:
                recommendations.append({
                    'type': 'urgent',
                    'message': 'Deal is overdue. Consider updating expected close date or pushing to close.',
                    'action': 'Update expected close date'
                })
            elif days_to_close <= 7:
                recommendations.append({
                    'type': 'warning',
                    'message': 'Deal closes soon. Ensure all requirements are met.',
                    'action': 'Review deal requirements'
                })
        
        # Stage-based recommendations
        if deal.stage == 'Lead' and deal.days_in_pipeline > 30:
            recommendations.append({
                'type': 'info',
                'message': 'Deal has been in Lead stage for over 30 days. Consider qualifying or moving to Lost.',
                'action': 'Qualify or close deal'
            })
        
        if deal.stage == 'Proposal' and deal.probability < 50:
            recommendations.append({
                'type': 'info',
                'message': 'Low probability for Proposal stage. Review proposal or adjust probability.',
                'action': 'Review proposal'
            })
        
        # Value-based recommendations
        if deal.value > 100000 and deal.stage in ['Lead', 'Qualified']:
            recommendations.append({
                'type': 'opportunity',
                'message': 'High-value deal in early stage. Consider executive involvement.',
                'action': 'Involve executive sponsor'
            })
        
        return recommendations
    
    @staticmethod
    def get_team_performance(date_range=None):
        """Get team performance metrics"""
        from .models import Deal
        
        if not date_range:
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
        else:
            start_date, end_date = date_range
        
        # Get deals created in the period
        deals = Deal.objects.filter(
            created_date__range=(start_date, end_date)
        )
        
        # Group by assigned user
        team_metrics = {}
        
        for user in User.objects.filter(is_active=True):
            user_deals = deals.filter(assigned_to=user)
            won_deals = user_deals.filter(status='Won')
            
            team_metrics[user.username] = {
                'total_deals': user_deals.count(),
                'won_deals': won_deals.count(),
                'total_value': user_deals.aggregate(total=Sum('value'))['total'] or 0,
                'won_value': won_deals.aggregate(total=Sum('value'))['total'] or 0,
                'win_rate': (won_deals.count() / user_deals.count() * 100) if user_deals.count() > 0 else 0,
                'avg_deal_size': user_deals.aggregate(avg=Avg('value'))['avg'] or 0
            }
        
        return team_metrics
    
    @staticmethod
    def get_pipeline_health():
        """Calculate overall pipeline health metrics"""
        from .models import Deal
        
        total_deals = Deal.objects.filter(status='Active').count()
        
        if total_deals == 0:
            return {'health_score': 0, 'issues': ['No active deals in pipeline']}
        
        health_score = 100
        issues = []
        
        # Check stage distribution
        stage_distribution = Deal.objects.filter(status='Active').values('stage').annotate(
            count=Count('id')
        )
        
        lead_count = 0
        for dist in stage_distribution:
            if dist['stage'] == 'Lead':
                lead_count = dist['count']
                break
        
        lead_percentage = (lead_count / total_deals) * 100
        
        if lead_percentage > 60:
            health_score -= 20
            issues.append('Too many deals in Lead stage')
        
        # Check for stale deals
        stale_deals = Deal.objects.filter(
            status='Active',
            created_date__lt=datetime.now() - timedelta(days=90)
        ).count()
        
        stale_percentage = (stale_deals / total_deals) * 100
        
        if stale_percentage > 30:
            health_score -= 15
            issues.append('High number of stale deals (>90 days old)')
        
        # Check conversion rate
        total_closed = Deal.objects.filter(status__in=['Won', 'Lost']).count()
        won_deals = Deal.objects.filter(status='Won').count()
        
        if total_closed > 0:
            win_rate = (won_deals / total_closed) * 100
            if win_rate < 20:
                health_score -= 25
                issues.append('Low win rate (<20%)')
        
        return {
            'health_score': max(0, health_score),
            'issues': issues,
            'total_deals': total_deals,
            'lead_percentage': round(lead_percentage, 1),
            'stale_percentage': round(stale_percentage, 1),
            'win_rate': round(win_rate, 1) if total_closed > 0 else 0
        }