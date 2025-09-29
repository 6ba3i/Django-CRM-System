# Customer and interaction models
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.db.models import Sum

class CustomerTag(models.Model):
    """Tags for categorizing customers"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#4a90e2')  # Hex color
    description = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Customer(models.Model):
    """Customer model with Firebase sync capabilities"""
    STATUS_CHOICES = [
        ('Lead', 'Lead'),
        ('Prospect', 'Prospect'),
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    
    # Firebase ID for syncing
    firebase_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    
    # Basic information
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=255, blank=True)
    
    # Status and assignment
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Lead')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='customers')
    
    # Timestamps
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    # Additional information
    notes = models.TextField(blank=True)
    tags = models.ManyToManyField(CustomerTag, blank=True)
    
    # Address information
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='USA')
    
    # Business information
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    # Lead source
    lead_source = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['created_date']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.company})" if self.company else self.name
    
    @property
    def total_deal_value(self):
        """Calculate total value of all deals for this customer"""
        return self.deals.aggregate(total=Sum('value'))['total'] or 0
    
    @property
    def active_deal_value(self):
        """Calculate total value of active deals"""
        return self.deals.filter(status='Active').aggregate(total=Sum('value'))['total'] or 0
    
    @property
    def won_deal_value(self):
        """Calculate total value of won deals"""
        return self.deals.filter(status='Won').aggregate(total=Sum('value'))['total'] or 0
    
    @property
    def interaction_count(self):
        """Count total interactions with this customer"""
        return self.interactions.count()
    
    @property
    def last_interaction(self):
        """Get the most recent interaction"""
        return self.interactions.order_by('-date').first()
    
    @property
    def days_since_last_interaction(self):
        """Calculate days since last interaction"""
        last = self.last_interaction
        if last:
            return (datetime.now().date() - last.date.date()).days
        return None
    
    @property
    def is_hot_lead(self):
        """Determine if this is a hot lead based on recent activity"""
        return (
            self.status == 'Lead' and 
            self.interaction_count > 2 and
            self.days_since_last_interaction is not None and
            self.days_since_last_interaction <= 7
        )
    
    def to_firebase_dict(self):
        """Convert customer to dictionary for Firebase"""
        return {
            'id': str(self.firebase_id) if self.firebase_id else None,
            'name': str(self.name),
            'email': str(self.email),
            'phone': str(self.phone),
            'company': str(self.company),
            'status': str(self.status),
            'assigned_to': str(self.assigned_to.id) if self.assigned_to else None,
            'notes': str(self.notes),
            'address': str(self.address),
            'city': str(self.city),
            'state': str(self.state),
            'zip_code': str(self.zip_code),
            'country': str(self.country),
            'industry': str(self.industry),
            'company_size': str(self.company_size),
            'website': str(self.website),
            'lead_source': str(self.lead_source),
            'created_date': self.created_date.isoformat() if self.created_date else datetime.now().isoformat(),
            'updated_date': self.updated_date.isoformat() if self.updated_date else datetime.now().isoformat(),
            'tags': [tag.name for tag in self.tags.all()],
            'total_deal_value': float(self.total_deal_value),
            'interaction_count': self.interaction_count
        }

class Interaction(models.Model):
    """Track interactions with customers"""
    INTERACTION_TYPES = [
        ('Call', 'Phone Call'),
        ('Email', 'Email'),
        ('Meeting', 'Meeting'),
        ('Demo', 'Product Demo'),
        ('Follow-up', 'Follow-up'),
        ('Support', 'Support Request'),
        ('Other', 'Other'),
    ]
    
    OUTCOME_CHOICES = [
        ('Positive', 'Positive'),
        ('Neutral', 'Neutral'),
        ('Negative', 'Negative'),
        ('No Response', 'No Response'),
        ('Follow-up Required', 'Follow-up Required'),
    ]
    
    # Firebase sync
    firebase_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    
    # Relationships
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='interactions')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Interaction details
    type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    subject = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    
    # Timing
    date = models.DateTimeField()
    duration = models.DurationField(blank=True, null=True)  # For calls/meetings
    
    # Follow-up
    follow_up_date = models.DateTimeField(blank=True, null=True)
    follow_up_completed = models.BooleanField(default=False)
    
    # Outcome
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, blank=True)
    
    # Timestamps
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    # Additional data
    attachments = models.JSONField(default=list, blank=True)  # File references
    location = models.CharField(max_length=255, blank=True)  # For meetings
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['type']),
            models.Index(fields=['date']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.type} with {self.customer.name} on {self.date.strftime('%Y-%m-%d')}"
    
    @property
    def is_overdue_followup(self):
        """Check if follow-up is overdue"""
        return (
            self.follow_up_date and 
            not self.follow_up_completed and 
            self.follow_up_date < datetime.now()
        )
    
    def to_firebase_dict(self):
        """Convert interaction to dictionary for Firebase"""
        return {
            'id': str(self.firebase_id) if self.firebase_id else None,
            'customer_id': str(self.customer.firebase_id) if self.customer.firebase_id else str(self.customer.id),
            'created_by': str(self.created_by.id) if self.created_by else None,
            'type': str(self.type),
            'subject': str(self.subject),
            'description': str(self.description),
            'date': self.date.isoformat() if self.date else datetime.now().isoformat(),
            'duration': str(self.duration) if self.duration else None,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'follow_up_completed': self.follow_up_completed,
            'outcome': str(self.outcome),
            'location': str(self.location),
            'attachments': self.attachments if self.attachments else [],
            'created_date': self.created_date.isoformat() if self.created_date else datetime.now().isoformat()
        }

class CustomerNote(models.Model):
    """Additional notes for customers"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_notes')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    is_important = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return f"Note for {self.customer.name}: {self.title or 'Untitled'}"

class CustomerDocument(models.Model):
    """Documents associated with customers"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file_path = models.CharField(max_length=500)  # Path to file (could be cloud storage)
    file_type = models.CharField(max_length=50)
    file_size = models.BigIntegerField()  # Size in bytes
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.title} - {self.customer.name}"