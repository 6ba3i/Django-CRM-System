 # Deal and pipeline models
from django.db import models
from django.contrib.auth.models import User
from customers.models import Customer
from datetime import datetime, timedelta

class Deal(models.Model):
    """Deal model - syncs with Firestore 'deals' collection"""
    # Pipeline stages
    LEAD = 'Lead'
    QUALIFIED = 'Qualified'
    PROPOSAL = 'Proposal'
    NEGOTIATION = 'Negotiation'
    WON = 'Won'
    LOST = 'Lost'
    ON_HOLD = 'On Hold'
    
    STAGE_CHOICES = [
        (LEAD, 'Lead'),
        (QUALIFIED, 'Qualified'),
        (PROPOSAL, 'Proposal'),
        (NEGOTIATION, 'Negotiation'),
        (WON, 'Won'),
        (LOST, 'Lost'),
        (ON_HOLD, 'On Hold'),
    ]
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Won', 'Won'),
        ('Lost', 'Lost'),
        ('On Hold', 'On Hold'),
    ]
    
    # Auto-generated Firebase ID
    firebase_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    
    # Reference to customer
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='deals')
    
    # Deal name/description
    title = models.CharField(max_length=255)
    
    # Deal monetary value
    value = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Pipeline stage
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default=LEAD)
    
    # Win probability (0-100%)
    probability = models.IntegerField(default=0, help_text="Win probability (0-100%)")
    
    # Expected close date
    expected_close = models.DateField(blank=True, null=True)
    
    # Deal creation date
    created_date = models.DateTimeField(auto_now_add=True)
    
    # Last modified date
    updated_date = models.DateTimeField(auto_now=True)
    
    # Sales rep user ID
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='deals')
    
    # Active, Won, Lost, On Hold
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    
    # Deal notes
    notes = models.TextField(blank=True)
    
    # Products/services involved (JSON list)
    products = models.JSONField(default=list, blank=True)
    
    # Competition
    competitors = models.TextField(blank=True, help_text="Competing companies for this deal")
    
    # Loss reason (if lost)
    loss_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['stage']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['expected_close']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.customer.name} - ${self.value:,.2f}"
    
    def to_firebase_dict(self):
        """Convert to dictionary for Firebase"""
        return {
            'id': str(self.firebase_id) if self.firebase_id else None,
            'customer_id': str(self.customer.firebase_id) if self.customer.firebase_id else str(self.customer.id),
            'title': str(self.title),
            'value': float(self.value),
            'stage': str(self.stage),
            'probability': int(self.probability),
            'expected_close': self.expected_close.isoformat() if self.expected_close else None,
            'created_date': self.created_date.isoformat() if self.created_date else datetime.now().isoformat(),
            'assigned_to': str(self.assigned_to.id) if self.assigned_to else None,
            'status': str(self.status),
            'notes': str(self.notes),
            'products': self.products if self.products else []
        }
    
    @property
    def weighted_value(self):
        """Calculate weighted value based on probability"""
        return self.value * (self.probability / 100)
    
    @property
    def days_in_pipeline(self):
        """Calculate number of days in pipeline"""
        return (datetime.now().date() - self.created_date.date()).days
    
    @property
    def is_overdue(self):
        """Check if deal is past expected close date"""
        if self.expected_close and self.status == 'Active':
            return self.expected_close < datetime.now().date()
        return False
    
    def update_stage(self, new_stage):
        """Update deal stage and related fields"""
        old_stage = self.stage
        self.stage = new_stage
        
        # Update probability based on stage
        stage_probabilities = {
            'Lead': 10,
            'Qualified': 25,
            'Proposal': 50,
            'Negotiation': 75,
            'Won': 100,
            'Lost': 0,
            'On Hold': self.probability  # Keep current probability
        }
        self.probability = stage_probabilities.get(new_stage, self.probability)
        
        # Update status based on stage
        if new_stage == 'Won':
            self.status = 'Won'
        elif new_stage == 'Lost':
            self.status = 'Lost'
        elif new_stage == 'On Hold':
            self.status = 'On Hold'
        else:
            self.status = 'Active'
        
        self.save()
        
        # Create pipeline history entry
        PipelineHistory.objects.create(
            deal=self,
            from_stage=old_stage,
            to_stage=new_stage,
            changed_by=self.assigned_to
        )

class PipelineHistory(models.Model):
    """Track deal movement through pipeline stages"""
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='pipeline_history')
    from_stage = models.CharField(max_length=20)
    to_stage = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-changed_date']
        verbose_name_plural = "Pipeline histories"
    
    def __str__(self):
        return f"{self.deal.title}: {self.from_stage} → {self.to_stage}"

class SalesForecast(models.Model):
    """Sales forecasting model"""
    period = models.CharField(max_length=20)  # e.g., "2024-Q1", "2024-03"
    forecast_type = models.CharField(max_length=20)  # 'monthly', 'quarterly', 'yearly'
    total_pipeline = models.DecimalField(max_digits=12, decimal_places=2)
    weighted_pipeline = models.DecimalField(max_digits=12, decimal_places=2)
    expected_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    actual_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-period']
        unique_together = ['period', 'forecast_type']
    
    def __str__(self):
        return f"{self.period} - {self.forecast_type} Forecast"
    
    @classmethod
    def generate_forecast(cls, period, forecast_type='monthly'):
        """Generate forecast for a given period"""
        from django.db.models import Sum, Q
        
        # Determine date range based on period
        if forecast_type == 'monthly':
            # Parse month from period (e.g., "2024-03")
            year, month = period.split('-')
            start_date = datetime(int(year), int(month), 1).date()
            if int(month) == 12:
                end_date = datetime(int(year) + 1, 1, 1).date()
            else:
                end_date = datetime(int(year), int(month) + 1, 1).date()
        elif forecast_type == 'quarterly':
            # Parse quarter from period (e.g., "2024-Q1")
            year, quarter = period.split('-Q')
            quarter = int(quarter)
            start_month = (quarter - 1) * 3 + 1
            start_date = datetime(int(year), start_month, 1).date()
            if quarter == 4:
                end_date = datetime(int(year) + 1, 1, 1).date()
            else:
                end_date = datetime(int(year), start_month + 3, 1).date()
        
        # Get deals in the period
        deals = Deal.objects.filter(
            expected_close__gte=start_date,
            expected_close__lt=end_date,
            status='Active'
        )
        
        # Calculate metrics
        total_pipeline = deals.aggregate(total=Sum('value'))['total'] or 0
        
        # Calculate weighted pipeline
        weighted_total = sum(deal.weighted_value for deal in deals)
        
        # Expected revenue (deals with high probability)
        high_prob_deals = deals.filter(probability__gte=70)
        expected_revenue = high_prob_deals.aggregate(total=Sum('value'))['total'] or 0
        
        # Create or update forecast
        forecast, created = cls.objects.update_or_create(
            period=period,
            forecast_type=forecast_type,
            defaults={
                'total_pipeline': total_pipeline,
                'weighted_pipeline': weighted_total,
                'expected_revenue': expected_revenue
            }
        )
        
        return forecast

class SalesActivity(models.Model):
    """Track sales activities and tasks"""
    ACTIVITY_TYPES = [
        ('Call', 'Call'),
        ('Email', 'Email'),
        ('Meeting', 'Meeting'),
        ('Demo', 'Demo'),
        ('Follow-up', 'Follow-up'),
        ('Proposal', 'Proposal'),
        ('Other', 'Other'),
    ]
    
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    completed = models.BooleanField(default=False)
    completed_date = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['due_date']
        verbose_name_plural = "Sales activities"
    
    def __str__(self):
        return f"{self.activity_type} - {self.subject}"
    
    def mark_complete(self):
        """Mark activity as completed"""
        self.completed = True
        self.completed_date = datetime.now()
        self.save()