 # Customer forms
from django import forms
from django.contrib.auth.models import User
from .models import Customer, Interaction, CustomerTag
from core.utils import validate_email, validate_phone

class CustomerForm(forms.ModelForm):
    """Form for creating/updating customers"""
    tags = forms.ModelMultipleChoiceField(
        queryset=CustomerTag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'company', 'status', 'assigned_to', 'notes', 'tags']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'glass-input',
                'placeholder': 'Enter customer name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'glass-input',
                'placeholder': 'email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'glass-input',
                'placeholder': '+1 (555) 123-4567'
            }),
            'company': forms.TextInput(attrs={
                'class': 'glass-input',
                'placeholder': 'Company name'
            }),
            'status': forms.Select(attrs={
                'class': 'glass-select'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'glass-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'glass-input',
                'rows': 4,
                'placeholder': 'Add notes about the customer...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active users in assigned_to field
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
    
    def clean_email(self):
        """Validate email format"""
        email = self.cleaned_data.get('email')
        if not validate_email(email):
            raise forms.ValidationError("Please enter a valid email address.")
        
        # Check for duplicate emails (excluding current instance in update)
        qs = Customer.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A customer with this email already exists.")
        
        return email
    
    def clean_phone(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone')
        if phone and not validate_phone(phone):
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone

class InteractionForm(forms.ModelForm):
    """Form for logging customer interactions"""
    class Meta:
        model = Interaction
        fields = ['type', 'description', 'date', 'follow_up_date', 'outcome']
        widgets = {
            'type': forms.Select(attrs={
                'class': 'glass-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'glass-input',
                'rows': 4,
                'placeholder': 'Describe the interaction...'
            }),
            'date': forms.DateTimeInput(attrs={
                'class': 'glass-input',
                'type': 'datetime-local'
            }),
            'follow_up_date': forms.DateTimeInput(attrs={
                'class': 'glass-input',
                'type': 'datetime-local'
            }),
            'outcome': forms.Select(attrs={
                'class': 'glass-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set current datetime as default for date field
        from datetime import datetime
        self.fields['date'].initial = datetime.now()
    
    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        follow_up_date = cleaned_data.get('follow_up_date')
        
        if follow_up_date and date and follow_up_date <= date:
            raise forms.ValidationError("Follow-up date must be after the interaction date.")
        
        return cleaned_data

class CustomerSearchForm(forms.Form):
    """Form for searching customers"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'glass-input',
            'placeholder': 'Search by name, email, or company...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Customer.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'glass-select'
        })
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="All Sales Reps",
        widget=forms.Select(attrs={
            'class': 'glass-select'
        })
    )
    
    tags = forms.ModelMultipleChoiceField(
        queryset=CustomerTag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'glass-select',
            'size': '3'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'glass-input',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'glass-input',
            'type': 'date'
        })
    )

class CustomerImportForm(forms.Form):
    """Form for importing customers from CSV"""
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'glass-input',
            'accept': '.csv'
        })
    )
    
    def clean_csv_file(self):
        """Validate CSV file"""
        csv_file = self.cleaned_data.get('csv_file')
        
        if not csv_file.name.endswith('.csv'):
            raise forms.ValidationError("Please upload a CSV file.")
        
        # Check file size (max 5MB)
        if csv_file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("File size must be under 5MB.")
        
        return csv_file

class BulkActionForm(forms.Form):
    """Form for bulk actions on customers"""
    ACTION_CHOICES = [
        ('assign', 'Assign to User'),
        ('status', 'Change Status'),
        ('tag', 'Add Tags'),
        ('export', 'Export Selected'),
        ('delete', 'Delete Selected')
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'glass-select'
        })
    )
    
    selected_customers = forms.CharField(
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
    
    status = forms.ChoiceField(
        choices=Customer.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'glass-select'
        })
    )
    
    tags = forms.ModelMultipleChoiceField(
        queryset=CustomerTag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'glass-select'
        })
    )