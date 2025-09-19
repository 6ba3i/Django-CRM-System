 # Customer data models
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class Customer(models.Model):
    """Customer model - syncs with Firestore"""
    LEAD = 'Lead'
    PROSPECT = 'Prospect'
    ACTIVE = 'Active'
    INACTIVE = 'Inactive'
    
    STATUS_CHOICES = [
        (LEAD, 'Lead'),
        (PROSPECT, 'Prospect'),
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    ]
    
    # Auto-generated Firebase ID
    firebase_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    
    # Customer full name
    name = models.CharField(max_length=255)
    
    # Email address
    email = models.EmailField(unique=True)
    
    # Phone number
    phone = models.CharField(max_length=20, blank=True)
    
    # Company name
    company = models.CharField(max_length=255, blank=True)
    
    # Lead, Prospect, Active, Inactive
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=LEAD)
    
    # Account creation date
    created_date = models.DateTimeField(auto_now_add=True)
    
    # Last modified date
    updated_date = models.DateTimeField(auto_now=True)
    
    # Sales rep user ID
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='customers')
    
    # General notes
    notes = models.TextField(blank=True)
    
    # Customer tags/categories (stored as JSON)
    tags = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['company']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.company}"
    
    def to_firebase_dict(self):
        """Convert to dictionary for Firebase"""
        return {
            'id': str(self.firebase_id) if self.firebase_id else None,
            'name': str(self.name),
            'email': str(self.email),
            'phone': str(self.phone),
            'company': str(self.company),
            'status': str(self.status),
            'created_date': self.created_date.isoformat() if self.created_date else datetime.now().isoformat(),
            'interactions': [],  # Will be populated from Interaction model
            'deals': [],  # Will be populated from Deal model
            'tags': self.tags if self.tags else [],
            'assigned_to': str(self.assigned_to.id) if self.assigned_to else None,
            'notes': str(self.notes)
        }
    
    @property
    def total_deal_value(self):
        """Calculate total value of all deals"""
        return sum(deal.value for deal in self.deals.all())
    
    @property
    def interaction_count(self):
        """Count of all interactions"""
        return self.interactions.count()

class Interaction(models.Model):
    """Interaction model for customer communications"""
    EMAIL = 'Email'
    CALL = 'Call'
    MEETING = 'Meeting'
    DEMO = 'Demo'
    
    TYPE_CHOICES = [
        (EMAIL, 'Email'),
        (CALL, 'Call'),
        (MEETING, 'Meeting'),
        (DEMO, 'Demo'),
    ]
    
    POSITIVE = 'Positive'
    NEUTRAL = 'Neutral'
    NEGATIVE = 'Negative'
    
    OUTCOME_CHOICES = [
        (POSITIVE, 'Positive'),
        (NEUTRAL, 'Neutral'),
        (NEGATIVE, 'Negative'),
    ]
    
    # Auto-generated Firebase ID
    firebase_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    
    # Reference to customer
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='interactions')
    
    # Email, Call, Meeting, Demo
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    # Detailed description
    description = models.TextField()
    
    # Interaction date
    date = models.DateTimeField(default=datetime.now)
    
    # Next follow-up date
    follow_up_date = models.DateTimeField(blank=True, null=True)
    
    # User who logged interaction
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='logged_interactions')
    
    # Positive, Neutral, Negative
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, default=NEUTRAL)
    
    # Attachments (stored as JSON list of URLs)
    attachments = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['type']),
            models.Index(fields=['date']),
            models.Index(fields=['follow_up_date']),
        ]
    
    def __str__(self):
        return f"{self.type} - {self.customer.name} - {self.date.strftime('%Y-%m-%d')}"
    
    def to_firebase_dict(self):
        """Convert to dictionary for Firebase"""
        return {
            'id': str(self.firebase_id) if self.firebase_id else None,
            'customer_id': str(self.customer.firebase_id) if self.customer.firebase_id else str(self.customer.id),
            'type': str(self.type),
            'description': str(self.description),
            'date': self.date.isoformat() if self.date else datetime.now().isoformat(),
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'created_by': str(self.created_by.id) if self.created_by else None,
            'outcome': str(self.outcome),
            'attachments': self.attachments if self.attachments else []
        }

class CustomerTag(models.Model):
    """Tags for categorizing customers"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#4a90e2')  # Hex color code
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name