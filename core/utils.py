 # Utility functions
import hashlib
import random
import string
from datetime import datetime, timedelta
import re
from typing import Dict, List, Any, Optional
import json

def generate_unique_id(prefix: str = '') -> str:
    """Generate a unique ID with optional prefix"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}{timestamp}{random_str}"

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove non-numeric characters
    cleaned = re.sub(r'\D', '', phone)
    # Check if it's a valid length (10-15 digits)
    return 10 <= len(cleaned) <= 15

def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format amount as currency"""
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥'
    }
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"

def calculate_deal_metrics(deals: List[Dict]) -> Dict[str, Any]:
    """Calculate metrics from deals list"""
    if not deals:
        return {
            'total_value': 0,
            'average_value': 0,
            'win_rate': 0,
            'total_deals': 0,
            'deals_won': 0,
            'deals_lost': 0,
            'deals_active': 0
        }
    
    total_value = sum(deal.get('value', 0) for deal in deals)
    deals_won = [d for d in deals if d.get('status') == 'Won']
    deals_lost = [d for d in deals if d.get('status') == 'Lost']
    deals_active = [d for d in deals if d.get('status') == 'Active']
    
    closed_deals = len(deals_won) + len(deals_lost)
    win_rate = (len(deals_won) / closed_deals * 100) if closed_deals > 0 else 0
    
    return {
        'total_value': total_value,
        'average_value': total_value / len(deals) if deals else 0,
        'win_rate': round(win_rate, 2),
        'total_deals': len(deals),
        'deals_won': len(deals_won),
        'deals_lost': len(deals_lost),
        'deals_active': len(deals_active)
    }

def get_date_range(period: str) -> tuple:
    """Get start and end dates for a given period"""
    end_date = datetime.now()
    
    periods = {
        'today': timedelta(days=1),
        'week': timedelta(weeks=1),
        'month': timedelta(days=30),
        'quarter': timedelta(days=90),
        'year': timedelta(days=365)
    }
    
    delta = periods.get(period, timedelta(days=30))
    start_date = end_date - delta
    
    return start_date, end_date

def paginate_results(data: List, page: int = 1, page_size: int = 20) -> Dict:
    """Paginate a list of results"""
    total_items = len(data)
    total_pages = (total_items + page_size - 1) // page_size
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    return {
        'results': data[start_idx:end_idx],
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1
        }
    }

def export_to_csv(data: List[Dict], filename: str) -> str:
    """Export data to CSV file"""
    import csv
    
    if not data:
        return None
    
    filepath = f"exports/{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(data)
    
    return filepath

def export_to_pdf(data: Dict, template: str, filename: str) -> str:
    """Export data to PDF using template"""
    # This would use a library like ReportLab or WeasyPrint
    # Placeholder implementation
    filepath = f"exports/{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Here you would generate the PDF
    # For now, we'll just return the filepath
    return filepath

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS"""
    if not text:
        return ''
    
    # Remove HTML tags
    clean = re.sub('<.*?>', '', text)
    # Escape special characters
    clean = clean.replace('&', '&amp;')
    clean = clean.replace('<', '&lt;')
    clean = clean.replace('>', '&gt;')
    clean = clean.replace('"', '&quot;')
    clean = clean.replace("'", '&#x27;')
    
    return clean

def calculate_roi(investment: float, revenue: float) -> float:
    """Calculate ROI (Return on Investment)"""
    if investment == 0:
        return 0
    return ((revenue - investment) / investment) * 100

def get_quarter(date: datetime) -> str:
    """Get quarter from date"""
    month = date.month
    if month <= 3:
        return 'Q1'
    elif month <= 6:
        return 'Q2'
    elif month <= 9:
        return 'Q3'
    else:
        return 'Q4'

def format_datetime(dt: datetime, format_type: str = 'full') -> str:
    """Format datetime based on type"""
    formats = {
        'full': '%Y-%m-%d %H:%M:%S',
        'date': '%Y-%m-%d',
        'time': '%H:%M:%S',
        'friendly': '%B %d, %Y',
        'short': '%m/%d/%y'
    }
    
    return dt.strftime(formats.get(format_type, formats['full']))

def calculate_pipeline_velocity(deals: List[Dict]) -> Dict[str, float]:
    """Calculate how fast deals move through the pipeline"""
    stage_durations = {
        'Lead': [],
        'Prospect': [],
        'Qualified': [],
        'Proposal': [],
        'Negotiation': []
    }
    
    for deal in deals:
        # Calculate time spent in each stage
        # This is a simplified version
        pass
    
    return {
        stage: sum(durations) / len(durations) if durations else 0
        for stage, durations in stage_durations.items()
    }