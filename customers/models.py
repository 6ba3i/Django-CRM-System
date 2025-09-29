# Firebase collection schemas and utilities for customer data
from datetime import datetime
from typing import Dict, List, Optional

class CustomerSchema:
    """Firebase schema definition for customers collection"""
    
    STATUS_CHOICES = [
        'Lead',
        'Prospect', 
        'Active',
        'Inactive'
    ]
    
    @staticmethod
    def create_customer_document(data: dict) -> dict:
        """Create a properly formatted customer document for Firebase"""
        return {
            'id': data.get('id', ''),
            'name': str(data.get('name', '')),
            'email': str(data.get('email', '')),
            'phone': str(data.get('phone', '')),
            'company': str(data.get('company', '')),
            'status': data.get('status', 'Lead'),
            'assigned_to': str(data.get('assigned_to', '')),
            'created_date': data.get('created_date', datetime.now().isoformat()),
            'updated_date': datetime.now().isoformat(),
            'notes': str(data.get('notes', '')),
            'tags': data.get('tags', []),
            'address': str(data.get('address', '')),
            'city': str(data.get('city', '')),
            'state': str(data.get('state', '')),
            'zip_code': str(data.get('zip_code', '')),
            'country': data.get('country', 'USA'),
            'industry': str(data.get('industry', '')),
            'company_size': str(data.get('company_size', '')),
            'website': str(data.get('website', '')),
            'lead_source': str(data.get('lead_source', '')),
            'total_deal_value': float(data.get('total_deal_value', 0)),
            'interaction_count': int(data.get('interaction_count', 0))
        }
    
    @staticmethod
    def validate_customer(data: dict) -> tuple[bool, str]:
        """Validate customer data"""
        if not data.get('name'):
            return False, "Name is required"
        
        if not data.get('email'):
            return False, "Email is required"
            
        # Basic email validation
        email = data.get('email', '')
        if '@' not in email or '.' not in email:
            return False, "Invalid email format"
            
        if data.get('status') not in CustomerSchema.STATUS_CHOICES:
            return False, "Invalid status"
            
        return True, "Valid"

class InteractionSchema:
    """Firebase schema for customer interactions"""
    
    INTERACTION_TYPES = [
        'Call',
        'Email',
        'Meeting', 
        'Demo',
        'Follow-up',
        'Support',
        'Other'
    ]
    
    OUTCOME_CHOICES = [
        'Positive',
        'Neutral',
        'Negative', 
        'No Response',
        'Follow-up Required'
    ]
    
    @staticmethod
    def create_interaction_document(data: dict) -> dict:
        """Create interaction document"""
        return {
            'id': data.get('id', ''),
            'customer_id': str(data.get('customer_id', '')),
            'created_by': str(data.get('created_by', '')),
            'type': data.get('type', 'Other'),
            'subject': str(data.get('subject', '')),
            'description': str(data.get('description', '')),
            'date': data.get('date', datetime.now().isoformat()),
            'duration': str(data.get('duration', '')),
            'follow_up_date': data.get('follow_up_date', ''),
            'follow_up_completed': bool(data.get('follow_up_completed', False)),
            'outcome': data.get('outcome', ''),
            'location': str(data.get('location', '')),
            'attachments': data.get('attachments', []),
            'created_date': data.get('created_date', datetime.now().isoformat())
        }

class CustomerTagSchema:
    """Firebase schema for customer tags"""
    
    @staticmethod
    def create_tag_document(data: dict) -> dict:
        """Create customer tag document"""
        return {
            'id': data.get('id', ''),
            'name': str(data.get('name', '')),
            'color': data.get('color', '#4a90e2'),
            'description': str(data.get('description', '')),
            'created_date': data.get('created_date', datetime.now().isoformat())
        }

class CustomerNoteSchema:
    """Firebase schema for customer notes"""
    
    @staticmethod
    def create_note_document(data: dict) -> dict:
        """Create customer note document"""
        return {
            'id': data.get('id', ''),
            'customer_id': str(data.get('customer_id', '')),
            'created_by': str(data.get('created_by', '')),
            'title': str(data.get('title', '')),
            'content': str(data.get('content', '')),
            'is_important': bool(data.get('is_important', False)),
            'created_date': data.get('created_date', datetime.now().isoformat()),
            'updated_date': datetime.now().isoformat()
        }

# Firebase collection names
CUSTOMER_COLLECTIONS = {
    'customers': 'customers',
    'interactions': 'interactions',
    'customer_tags': 'customer_tags',
    'customer_notes': 'customer_notes',
    'customer_documents': 'customer_documents'
}