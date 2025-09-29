# Data processing utilities for analytics - Firebase Only
from django.contrib.auth.models import User
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
import json
from collections import defaultdict

from core.firebase_config import FirebaseDB

class DataProcessor:
    """Processes data for analytics and reporting using Firebase"""
    
    @staticmethod
    def get_dashboard_metrics(user=None, period='month'):
        """Get comprehensive dashboard metrics using Firebase"""
        
        # Get data from Firebase
        customers = FirebaseDB.get_records('customers')
        deals = FirebaseDB.get_records('deals')
        activities = FirebaseDB.get_records('sales_activities')
        
        # Filter by user if specified
        if user and not user.is_staff:
            user_email = user.email
            customers = [c for c in customers if c.get('assigned_to') == user_email]
            deals = [d for d in deals if d.get('assigned_to') == user_email]
            activities = [a for a in activities if a.get('assigned_to') == user_email]
        
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
        
        start_date_str = start_date.isoformat()
        
        # Customer metrics
        new_period_customers = [c for c in customers if c.get('created_date', '') >= start_date_str]
        customer_metrics = {
            'total': len(customers),
            'new_period': len(new_period_customers),
            'by_status': {},
            'conversion_rate': 0
        }
        
        # Count by status
        for status in ['Lead', 'Prospect', 'Active', 'Inactive']:
            customer_metrics['by_status'][status] = len([c for c in customers if c.get('status') == status])
        
        # Calculate conversion rate
        active_customers = len([c for c in customers if c.get('status') == 'Active'])
        if customer_metrics['total'] > 0:
            customer_metrics['conversion_rate'] = round((active_customers / customer_metrics['total']) * 100, 2)
        
        # Deal metrics
        won_deals = [d for d in deals if d.get('status') == 'Won']
        lost_deals = [d for d in deals if d.get('status') == 'Lost']
        active_deals = [d for d in deals if d.get('status') == 'Active']
        
        deal_metrics = {
            'total': len(deals),
            'active': len(active_deals),
            'won': len(won_deals),
            'lost': len(lost_deals),
            'total_value': sum([d.get('value', 0) for d in deals]),
            'won_value': sum([d.get('value', 0) for d in won_deals]),
            'pipeline_value': sum([d.get('value', 0) for d in active_deals]),
            'avg_deal_size': sum([d.get('value', 0) for d in deals]) / len(deals) if deals else 0,
            'win_rate': 0
        }
        
        # Calculate win rate
        closed_deals = len(won_deals) + len(lost_deals)
        if closed_deals > 0:
            deal_metrics['win_rate'] = round((len(won_deals) / closed_deals) * 100, 2)
        
        # Activity metrics
        completed_activities = [a for a in activities if a.get('completed')]
        activity_metrics = {
            'total': len(activities),
            'completed': len(completed_activities),
            'pending': len(activities) - len(completed_activities),
            'overdue': 0,  # Simplified - would need date comparison
            'completion_rate': round((len(completed_activities) / len(activities)) * 100, 2) if activities else 0
        }
        
        # Revenue metrics
        revenue_metrics = {
            'total': deal_metrics['won_value'],
            'period': sum([d.get('value', 0) for d in won_deals if d.get('updated_date', '') >= start_date_str]),
            'forecast': sum([d.get('value', 0) for d in deals if d.get('probability', 0) >= 70])
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
    def get_chart_data():
        """Get properly formatted data for chart generation using Firebase"""
        
        # Get all data from Firebase
        customers = FirebaseDB.get_records('customers')
        deals = FirebaseDB.get_records('deals')
        
        # Convert to consistent format for charts
        customers_data = []
        for customer in customers:
            customers_data.append({
                'id': customer.get('id', ''),
                'name': customer.get('name', ''),
                'status': customer.get('status', 'Unknown'),
                'company': customer.get('company', ''),
                'created_date': customer.get('created_date', ''),
                'value': float(customer.get('total_deal_value', 0))
            })
        
        deals_data = []
        for deal in deals:
            deals_data.append({
                'id': deal.get('id', ''),
                'title': deal.get('title', ''),
                'stage': deal.get('stage', 'Unknown'),
                'status': deal.get('status', 'Active'),
                'value': float(deal.get('value', 0)),
                'probability': deal.get('probability', 0),
                'created_date': deal.get('created_date', ''),
                'updated_date': deal.get('updated_date', ''),
                'assigned_to': deal.get('assigned_to', ''),
                'customer': deal.get('customer', '')
            })
        
        return {
            'customers': customers_data,
            'deals': deals_data,
            'customer_statuses': [c['status'] for c in customers_data],
            'deal_stages': [d['stage'] for d in deals_data]
        }
    
    @staticmethod
    def get_sales_trends(period='month', user=None):
        """Get sales trends over time with REAL Firebase data"""
        
        deals = FirebaseDB.get_records('deals')
        
        # Filter by user if specified
        if user and not user.is_staff:
            user_email = user.email
            deals = [d for d in deals if d.get('assigned_to') == user_email]
        
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
        
        start_date_str = start_date.isoformat()
        
        # Filter deals by date range
        filtered_deals = [d for d in deals if d.get('created_date', '') >= start_date_str]
        
        # Group data by time period
        trends = defaultdict(lambda: {
            'revenue': 0,
            'deals': 0,
            'won_deals': 0,
            'pipeline_value': 0
        })
        
        for deal in filtered_deals:
            created_date = deal.get('created_date', '')
            if not created_date:
                continue
                
            try:
                deal_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
            except:
                continue
            
            # Format date based on period
            if period == 'quarter':
                quarter = (deal_date.month - 1) // 3 + 1
                period_key = f"{deal_date.year}-Q{quarter}"
            else:
                period_key = deal_date.strftime(date_format)
            
            trends[period_key]['deals'] += 1
            
            if deal.get('status') == 'Won':
                trends[period_key]['revenue'] += float(deal.get('value', 0))
                trends[period_key]['won_deals'] += 1
            elif deal.get('status') == 'Active':
                trends[period_key]['pipeline_value'] += float(deal.get('value', 0))
        
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
        """Get detailed pipeline analytics using Firebase"""
        
        deals = FirebaseDB.get_records('deals')
        active_deals = [d for d in deals if d.get('status') == 'Active']
        
        # Current pipeline distribution
        pipeline_dist = {}
        stage_choices = ['Lead', 'Qualified', 'Proposal', 'Negotiation', 'Won', 'Lost', 'On Hold']
        
        for stage in stage_choices:
            stage_deals = [d for d in active_deals if d.get('stage') == stage]
            
            total_value = sum([d.get('value', 0) for d in stage_deals])
            weighted_value = sum([d.get('value', 0) * d.get('probability', 0) / 100 for d in stage_deals])
            avg_probability = sum([d.get('probability', 0) for d in stage_deals]) / len(stage_deals) if stage_deals else 0
            
            pipeline_dist[stage] = {
                'count': len(stage_deals),
                'value': total_value,
                'weighted_value': weighted_value,
                'avg_probability': round(avg_probability, 1)
            }
        
        # Simplified velocity analysis (would need pipeline history for accurate calculation)
        velocity = {}
        for stage in stage_choices:
            velocity[stage] = {
                'avg_days': 0,  # Would need pipeline history to calculate
                'sample_size': 0
            }
        
        # Simplified conversion rates (would need pipeline history for accurate calculation)
        conversions = {}
        for stage in stage_choices:
            conversions[stage] = {}
            for to_stage in stage_choices:
                conversions[stage][to_stage] = 0
        
        return {
            'distribution': pipeline_dist,
            'velocity': velocity,
            'conversions': conversions,
            'total_pipeline_value': sum(stage['value'] for stage in pipeline_dist.values()),
            'total_weighted_value': sum(stage['weighted_value'] for stage in pipeline_dist.values())
        }
    
    @staticmethod
    def export_analytics_report(format='json'):
        """Export comprehensive analytics report using Firebase"""
        
        # Gather all data from Firebase
        customers = FirebaseDB.get_records('customers')
        deals = FirebaseDB.get_records('deals')
        activities = FirebaseDB.get_records('sales_activities')
        
        # Calculate statistics
        customer_stats = FirebaseDB.get_statistics('customers')
        deal_stats = FirebaseDB.get_statistics('deals')
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'format': format,
            'summary': {
                'total_customers': len(customers),
                'total_deals': len(deals),
                'total_activities': len(activities),
                'total_revenue': sum([d.get('value', 0) for d in deals if d.get('status') == 'Won'])
            },
            'customers': {
                'by_status': {},
                'by_month': DataProcessor._group_by_month_firebase(customers, 'created_date'),
                'top_by_value': DataProcessor._get_top_customers(customers, deals)
            },
            'deals': {
                'by_stage': {},
                'by_status': {},
                'by_month': DataProcessor._group_by_month_firebase(deals, 'created_date'),
                'largest_deals': sorted(deals, key=lambda x: x.get('value', 0), reverse=True)[:10]
            },
            'performance': DataProcessor.get_dashboard_metrics(),
            'trends': DataProcessor.get_sales_trends(),
            'pipeline': DataProcessor.get_pipeline_analytics()
        }
        
        # Calculate by_status for customers
        for status in ['Lead', 'Prospect', 'Active', 'Inactive']:
            report['customers']['by_status'][status] = len([c for c in customers if c.get('status') == status])
        
        # Calculate by_stage and by_status for deals
        for stage in ['Lead', 'Qualified', 'Proposal', 'Negotiation', 'Won', 'Lost']:
            report['deals']['by_stage'][stage] = len([d for d in deals if d.get('stage') == stage])
        
        for status in ['Active', 'Won', 'Lost', 'On Hold']:
            report['deals']['by_status'][status] = len([d for d in deals if d.get('status') == status])
        
        return report
    
    @staticmethod
    def _group_by_month_firebase(data_list, date_field):
        """Helper method to group Firebase data by month"""
        monthly_data = defaultdict(int)
        
        for item in data_list:
            date_value = item.get(date_field, '')
            if date_value:
                try:
                    if isinstance(date_value, str):
                        date_obj = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                    else:
                        date_obj = date_value
                    month_key = date_obj.strftime('%Y-%m')
                    monthly_data[month_key] += 1
                except:
                    continue
        
        return dict(monthly_data)
    
    @staticmethod
    def _get_top_customers(customers, deals):
        """Get top customers by deal value"""
        customer_values = {}
        
        # Calculate total deal value per customer
        for deal in deals:
            customer_name = deal.get('customer', '')
            if customer_name:
                if customer_name not in customer_values:
                    customer_values[customer_name] = {
                        'total_value': 0,
                        'deal_count': 0,
                        'customer_data': None
                    }
                customer_values[customer_name]['total_value'] += deal.get('value', 0)
                customer_values[customer_name]['deal_count'] += 1
        
        # Match with customer data
        for customer in customers:
            customer_name = customer.get('name', '')
            if customer_name in customer_values:
                customer_values[customer_name]['customer_data'] = customer
        
        # Sort and return top 10
        top_customers = []
        for customer_name, data in customer_values.items():
            customer_info = data['customer_data'] or {'name': customer_name, 'company': ''}
            top_customers.append({
                'name': customer_name,
                'company': customer_info.get('company', ''),
                'total_deals': data['deal_count'],
                'total_value': data['total_value']
            })
        
        top_customers.sort(key=lambda x: x['total_value'], reverse=True)
        return top_customers[:10]
    
    @staticmethod
    def get_user_performance(user_id):
        """Get performance metrics for a specific user using Firebase"""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
        
        user_email = user.email
        
        # Get user's data from Firebase
        customers = [c for c in FirebaseDB.get_records('customers') if c.get('assigned_to') == user_email]
        deals = [d for d in FirebaseDB.get_records('deals') if d.get('assigned_to') == user_email]
        activities = [a for a in FirebaseDB.get_records('sales_activities') if a.get('assigned_to') == user_email]
        
        # Calculate metrics
        won_deals = [d for d in deals if d.get('status') == 'Won']
        lost_deals = [d for d in deals if d.get('status') == 'Lost']
        active_deals = [d for d in deals if d.get('status') == 'Active']
        completed_activities = [a for a in activities if a.get('completed')]
        
        performance = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name()
            },
            'customers': {
                'total': len(customers),
                'active': len([c for c in customers if c.get('status') == 'Active']),
                'conversion_rate': 0
            },
            'deals': {
                'total': len(deals),
                'won': len(won_deals),
                'lost': len(lost_deals),
                'pipeline_value': sum([d.get('value', 0) for d in active_deals]),
                'won_value': sum([d.get('value', 0) for d in won_deals]),
                'avg_deal_size': sum([d.get('value', 0) for d in deals]) / len(deals) if deals else 0,
                'win_rate': 0
            },
            'activities': {
                'total': len(activities),
                'completed': len(completed_activities),
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
        """Generate forecast data for given periods using Firebase"""
        
        deals = FirebaseDB.get_records('deals')
        active_deals = [d for d in deals if d.get('status') == 'Active']
        
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
            
            # Find deals expected to close in this period
            period_deals = []
            for deal in active_deals:
                expected_close = deal.get('expected_close', '')
                if expected_close and expected_close.startswith(period_key[:7]):
                    period_deals.append(deal)
            
            # Calculate forecast metrics
            total_pipeline = sum([d.get('value', 0) for d in period_deals])
            weighted_pipeline = sum([d.get('value', 0) * d.get('probability', 0) / 100 for d in period_deals])
            expected_revenue = sum([d.get('value', 0) for d in period_deals if d.get('probability', 0) >= 70])
            
            forecasts.append({
                'period': period_key,
                'total_pipeline': float(total_pipeline),
                'weighted_pipeline': float(weighted_pipeline),
                'expected_revenue': float(expected_revenue),
                'actual_revenue': None  # Would be filled in after the period ends
            })
        
        return forecasts