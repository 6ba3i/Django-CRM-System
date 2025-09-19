# Sales forms
from django import forms
from django.contrib.auth.models import User
from .models import Deal, SalesActivity
from customers.models import Customer
from datetime import datetime, timedelta

class DealForm(forms.ModelForm):
    """Form for creating/updating deals"""
    class Meta:
        model = Deal
        fields = ['customer', 'title', 'value', 'stage', 'probability', 'expected_close', 
                 'assigned_to', 'notes', 'products', 'competitors']
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'glass-select',
                'required': True
            }),
            'title': forms.TextInput(attrs={
                'class': 'glass-input',
                'placeholder': 'Enter deal title'
            }),
            'value': forms.NumberInput(attrs={
                'class': 'glass-input',
                'placeholder': 'Deal value in USD',
                'min': '0',
                'step': '0.01'
            }),
            'stage': forms.Select(attrs={
                'class': 'glass-select'
            }),
            'probability': forms.NumberInput(attrs={
                'class': 'glass-input',
                'placeholder': 'Win probability (0-100)',
                'min': '0',
                'max': '100'
            }),
            'expected_close': forms.DateInput(attrs={
                'class': 'glass-input',
                'type': 'date'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'glass-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'glass-input',
                'rows': 4,
                'placeholder': 'Add notes about the deal...'
            }),
            'competitors': forms.Textarea(attrs={
                'class': 'glass-input',
                'rows': 2,
                'placeholder': 'List competing companies...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show active customers
        self.fields['customer'].queryset = Customer.objects.filter(
            status__in=['Lead', 'Prospect', 'Active']
        )
        
        # Only show active users
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
        
        # Set default expected close date to 30 days from now
        if not self.instance.pk:
            self.fields['expected_close'].initial = (datetime.now() + timedelta(days=30)).date()
    
    def clean_probability(self):
        """Validate probability is between 0 and 100"""
        probability = self.cleaned_data.get('probability')
        if probability < 0 or probability > 100:
            raise forms.ValidationError("Probability must be between 0 and 100")
        return probability
    
    def clean_value(self):
        """Validate deal value is positive"""
        value = self.cleaned_data.get('value')
        if value <= 0:
            raise forms.ValidationError("Deal value must be greater than 0")
        return value
    
    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        stage = cleaned_data.get('stage')
        probability = cleaned_data.get('probability')
        
        # Validate probability matches stage
        stage_probability_ranges = {
            'Lead': (0, 25),
            'Qualified': (20, 50),
            'Proposal': (40, 70),
            'Negotiation': (60, 90),
            'Won': (100, 100),
            'Lost': (0, 0)
        }
        
        if stage in stage_probability_ranges:
            min_prob, max_prob = stage_probability_ranges[stage]
            if stage in ['Won', 'Lost']:
                # Exact probability for Won/Lost
                if probability != min_prob:
                    self.add_error('probability', 
                                 f"Probability should be {min_prob}% for {stage} deals")
            else:
                # Recommended range for other stages (warning only)
                if not (min_prob <= probability <= max_prob):
                    # Just a warning, not an error
                    pass
        
        return cleaned_data

class SalesActivityForm(forms.ModelForm):
    """Form for sales activities"""
    class Meta:
        model = SalesActivity
        fields = ['activity_type', 'subject', 'description', 'due_date', 'assigned_to']
        widgets = {
            'activity_type': forms.Select(attrs={
                'class': 'glass-select'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'glass-input',
                'placeholder': 'Activity subject'
            }),
            'description': forms.Textarea(attrs={
                'class': 'glass-input',
                'rows': 3,
                'placeholder': 'Describe the activity...'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'glass-input',
                'type': 'datetime-local'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'glass-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show active users
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
        
        # Set default due date to tomorrow
        if not self.instance.pk:
            self.fields['due_date'].initial = datetime.now() + timedelta(days=1)
    
    def clean_due_date(self):
        """Validate due date is in the future"""
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < datetime.now():
            raise forms.ValidationError("Due date must be in the future")
        return due_date

class PipelineFilterForm(forms.Form):
    """Form for filtering pipeline view"""
    stage = forms.ChoiceField(
        choices=[('', 'All Stages')] + Deal.STAGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'glass-select'
        })
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={
            'class': 'glass-select'
        })
    )
    
    date_range = forms.ChoiceField(
        choices=[
            ('all', 'All Time'),
            ('today', 'Today'),
            ('week', 'This Week'),
            ('month', 'This Month'),
            ('quarter', 'This Quarter'),
            ('year', 'This Year')
        ],
        initial='month',
        widget=forms.Select(attrs={
            'class': 'glass-select'
        })
    )
    
    min_value = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'glass-input',
            'placeholder': 'Min value'
        })
    )
    
    max_value = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'glass-input',
            'placeholder': 'Max value'
        })
    )

class ForecastForm(forms.Form):
    """Form for sales forecast parameters"""
    period_type = forms.ChoiceField(
        choices=[
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly')
        ],
        widget=forms.Select(attrs={
            'class': 'glass-select'
        })
    )
    
    num_periods = forms.IntegerField(
        min_value=1,
        max_value=12,
        initial=6,
        widget=forms.NumberInput(attrs={
            'class': 'glass-input',
            'placeholder': 'Number of periods to forecast'
        })
    )
    
    include_probability = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

class BulkDealActionForm(forms.Form):
    """Form for bulk actions on deals"""
    ACTION_CHOICES = [
        ('assign', 'Assign to User'),
        ('stage', 'Change Stage'),
        ('status', 'Change Status'),
        ('export', 'Export Selected'),
        ('delete', 'Delete Selected')
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'glass-select'
        })
    )
    
    selected_deals = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    # Optional fields based on action
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'glass-select'
        })
    )
    
    stage = forms.ChoiceField(
        choices=Deal.STAGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'glass-select'
        })
    )
    
    status = forms.ChoiceField(
        choices=Deal.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'glass-select'
        })
    )