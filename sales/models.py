# Firebase collection schemas and utilities for sales data
from datetime import datetime
from typing import Dict, List, Optional

class DealSchema:
    """Firebase schema definition for deals collection"""
    
    # Stage choices for validation
    STAGE_CHOICES = [
        'Lead',
        'Qualified', 
        'Proposal',
        'Negotiation',
        'Won',
        'Lost',
        'On Hold'
    ]
    
    STATUS_CHOICES = [
        'Active',
        'Won', 
        'Lost',
        'On Hold'
    ]
    
    @staticmethod
    def create_deal_document(data: dict) -> dict:
        """Create a properly formatted deal document for Firebase"""
        return {
            'id': data.get('id', ''),
            'customer': str(data.get('customer', '')),
            'title': str(data.get('title', '')),
            'value': float(data.get('value', 0)),
            'stage': data.get('stage', 'Lead'),
            'probability': int(data.get('probability', 0)),
            'expected_close': data.get('expected_close', ''),
            'created_date': data.get('created_date', datetime.now().isoformat()),
            'updated_date': datetime.now().isoformat(),
            'assigned_to': str(data.get('assigned_to', '')),
            'status': data.get('status', 'Active'),
            'notes': str(data.get('notes', '')),
            'products': data.get('products', []),
            'competitors': str(data.get('competitors', '')),
            'loss_reason': str(data.get('loss_reason', ''))
        }
    
    @staticmethod
    def validate_deal(data: dict) -> tuple[bool, str]:
        """Validate deal data"""
        if not data.get('title'):
            return False, "Title is required"
        
        if not data.get('customer'):
            return False, "Customer is required"
            
        try:
            value = float(data.get('value', 0))
            if value < 0:
                return False, "Value must be positive"
        except ValueError:
            return False, "Invalid value format"
            
        if data.get('stage') not in DealSchema.STAGE_CHOICES:
            return False, "Invalid stage"
            
        try:
            probability = int(data.get('probability', 0))
            if not (0 <= probability <= 100):
                return False, "Probability must be between 0 and 100"
        except ValueError:
            return False, "Invalid probability format"
            
        return True, "Valid"

class PipelineHistorySchema:
    """Firebase schema for pipeline history tracking"""
    
    @staticmethod
    def create_history_document(data: dict) -> dict:
        """Create pipeline history document"""
        return {
            'id': data.get('id', ''),
            'deal_id': str(data.get('deal_id', '')),
            'from_stage': str(data.get('from_stage', '')),
            'to_stage': str(data.get('to_stage', '')),
            'changed_by': str(data.get('changed_by', '')),
            'changed_date': data.get('changed_date', datetime.now().isoformat()),
            'notes': str(data.get('notes', ''))
        }

class SalesActivitySchema:
    """Firebase schema for sales activities"""
    
    ACTIVITY_TYPES = [
        'Call',
        'Email', 
        'Meeting',
        'Demo',
        'Follow-up',
        'Other'
    ]
    
    @staticmethod
    def create_activity_document(data: dict) -> dict:
        """Create sales activity document"""
        return {
            'id': data.get('id', ''),
            'deal_id': str(data.get('deal_id', '')),
            'activity_type': data.get('activity_type', 'Other'),
            'subject': str(data.get('subject', '')),
            'description': str(data.get('description', '')),
            'due_date': data.get('due_date', ''),
            'completed': bool(data.get('completed', False)),
            'completed_date': data.get('completed_date', ''),
            'assigned_to': str(data.get('assigned_to', '')),
            'created_date': data.get('created_date', datetime.now().isoformat())
        }

class SalesForecastSchema:
    """Firebase schema for sales forecasting"""
    
    @staticmethod
    def create_forecast_document(data: dict) -> dict:
        """Create forecast document"""
        return {
            'id': data.get('id', ''),
            'period': str(data.get('period', '')),
            'forecast_type': data.get('forecast_type', 'monthly'),
            'total_pipeline': float(data.get('total_pipeline', 0)),
            'weighted_pipeline': float(data.get('weighted_pipeline', 0)),
            'expected_revenue': float(data.get('expected_revenue', 0)),
            'actual_revenue': float(data.get('actual_revenue', 0)) if data.get('actual_revenue') else None,
            'created_by': str(data.get('created_by', '')),
            'created_date': data.get('created_date', datetime.now().isoformat())
        }

# Firebase collection names
SALES_COLLECTIONS = {
    'deals': 'deals',
    'pipeline_history': 'pipeline_history', 
    'sales_activities': 'sales_activities',
    'sales_forecasts': 'sales_forecasts'
}