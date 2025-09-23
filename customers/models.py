from django.db import models
from datetime import datetime

class Customer(models.Model):
    """Simple customer model"""
    STATUS_CHOICES = [
        ('Lead', 'Lead'),
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    
    firebase_id = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Lead')
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    # Using list field (stored as JSON)
    tags = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return self.name
    
    def to_dict(self):
        """Convert to dictionary for Firebase"""
        return {
            'name': str(self.name),
            'email': str(self.email),
            'phone': str(self.phone),
            'company': str(self.company),
            'status': str(self.status),
            'value': float(self.value),
            'notes': str(self.notes),
            'tags': self.tags if isinstance(self.tags, list) else [],
            'created_date': self.created_date.isoformat() if self.created_date else datetime.now().isoformat()
        }