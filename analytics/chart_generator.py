# Matplotlib integration for chart generation
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg

from customers.models import Customer
from sales.models import Deal, PipelineHistory

class ChartGenerator:
    """Generate charts using Matplotlib for analytics dashboard"""
    
    # Define glassmorphism colors
    COLORS = {
        'primary': '#1a1d29',  # Deep Navy
        'secondary': '#4a90e2',  # Soft Blue
        'accent': '#50c878',  # Mint Green
        'background': 'rgba(255, 255, 255, 0.1)',
        'grid': 'rgba(255, 255, 255, 0.3)'
    }
    
    @staticmethod
    def setup_style():
        """Set up matplotlib style for glassmorphic appearance"""
        plt.style.use('dark_background')
        plt.rcParams['figure.facecolor'] = '#1a1d29'
        plt.rcParams['axes.facecolor'] = 'rgba(255, 255, 255, 0.05)'
        plt.rcParams['axes.edgecolor'] = 'rgba(255, 255, 255, 0.3)'
        plt.rcParams['axes.labelcolor'] = 'white'
        plt.rcParams['text.color'] = 'white'
        plt.rcParams['xtick.color'] = 'white'
        plt.rcParams['ytick.color'] = 'white'
        plt.rcParams['grid.color'] = 'rgba(255, 255, 255, 0.2)'
        plt.rcParams['font.family'] = 'Inter, Poppins, sans-serif'
    
    @staticmethod
    def generate_pipeline_funnel():
        """Generate pipeline funnel chart"""
        ChartGenerator.setup_style()
        
        # Get pipeline data
        stages = ['Lead', 'Qualified', 'Proposal', 'Negotiation', 'Won']
        stage_counts = []
        stage_values = []
        
        for stage in stages:
            if stage == 'Won':
                deals = Deal.objects.filter(status='Won')
            else:
                deals = Deal.objects.filter(stage=stage, status='Active')
            
            stage_counts.append(deals.count())
            stage_values.append(deals.aggregate(total=Sum('value'))['total'] or 0)
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.patch.set_alpha(0.0)
        
        # Funnel chart (deal counts)
        y_pos = np.arange(len(stages))
        colors = ['#4a90e2', '#5a9fe2', '#6aafe2', '#7abfe2', '#50c878']
        
        bars1 = ax1.barh(y_pos, stage_counts, color=colors, alpha=0.8)
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(stages)
        ax1.set_xlabel('Number of Deals')
        ax1.set_title('Sales Funnel - Deal Count', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.2)
        
        # Add value labels
        for i, (bar, count) in enumerate(zip(bars1, stage_counts)):
            ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    f'{count}', va='center', fontweight='bold')
        
        # Value chart
        bars2 = ax2.barh(y_pos, [v/1000 for v in stage_values], color=colors, alpha=0.8)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(stages)
        ax2.set_xlabel('Total Value ($K)')
        ax2.set_title('Sales Funnel - Deal Value', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.2)
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars2, stage_values)):
            ax2.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                    f'${value/1000:.0f}K', va='center', fontweight='bold')
        
        plt.tight_layout()
        
        # Convert to base64 string
        buffer = BytesIO()
        plt.savefig(buffer, format='png', transparent=True, dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return image_base64
    
    @staticmethod
    def generate_revenue_forecast():
        """Generate revenue forecast chart"""
        ChartGenerator.setup_style()
        
        # Generate forecast data for next 6 months
        months = []
        expected = []
        weighted = []
        actual = []
        
        current_date = datetime.now()
        for i in range(6):
            month_date = current_date + timedelta(days=30*i)
            month_name = month_date.strftime('%b %Y')
            months.append(month_name)
            
            # Get deals expected to close in this month
            month_start = datetime(month_date.year, month_date.month, 1)
            if month_date.month == 12:
                month_end = datetime(month_date.year + 1, 1, 1)
            else:
                month_end = datetime(month_date.year, month_date.month + 1, 1)
            
            deals = Deal.objects.filter(
                expected_close__gte=month_start.date(),
                expected_close__lt=month_end.date()
            )
            
            # Calculate expected and weighted revenue
            exp_revenue = deals.filter(status='Active', probability__gte=70).aggregate(
                total=Sum('value'))['total'] or 0
            expected.append(exp_revenue / 1000)  # Convert to thousands
            
            weight_revenue = sum(d.weighted_value for d in deals.filter(status='Active'))
            weighted.append(weight_revenue / 1000)
            
            # Actual revenue (for past months)
            if i == 0:
                act_revenue = deals.filter(status='Won').aggregate(
                    total=Sum('value'))['total'] or 0
                actual.append(act_revenue / 1000)
            else:
                actual.append(0)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_alpha(0.0)
        
        x = np.arange(len(months))
        width = 0.25
        
        # Create bars
        bars1 = ax.bar(x - width, expected, width, label='Expected', color='#50c878', alpha=0.8)
        bars2 = ax.bar(x, weighted, width, label='Weighted', color='#4a90e2', alpha=0.8)
        bars3 = ax.bar(x + width, actual, width, label='Actual', color='#ffd700', alpha=0.8)
        
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Revenue ($K)', fontsize=12)
        ax.set_title('Revenue Forecast - Next 6 Months', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45, ha='right')
        ax.legend(loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.2)
        
        # Add value labels on bars
        def add_value_labels(bars):
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'${height:.0f}K',
                           ha='center', va='bottom', fontsize=9)
        
        add_value_labels(bars1)
        add_value_labels(bars2)
        add_value_labels(bars3)
        
        plt.tight_layout()
        
        # Convert to base64 string
        buffer = BytesIO()
        plt.savefig(buffer, format='png', transparent=True, dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return image_base64
    
    @staticmethod
    def generate_performance_metrics():
        """Generate team performance metrics chart"""
        ChartGenerator.setup_style()
        
        # Get top 5 sales reps by revenue
        from django.contrib.auth.models import User
        from django.db.models import Sum, Q
        
        top_reps = User.objects.annotate(
            total_revenue=Sum('deals__value', filter=Q(deals__status='Won'))
        ).filter(total_revenue__isnull=False).order_by('-total_revenue')[:5]
        
        names = []
        revenues = []
        deal_counts = []
        
        for rep in top_reps:
            names.append(rep.get_full_name() or rep.username)
            revenues.append((rep.total_revenue or 0) / 1000)
            deal_counts.append(rep.deals.filter(status='Won').count())
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.patch.set_alpha(0.0)
        
        # Revenue chart
        bars1 = ax1.bar(names, revenues, color='#50c878', alpha=0.8)
        ax1.set_ylabel('Revenue ($K)', fontsize=12)
        ax1.set_title('Top Performers - Revenue', fontsize=14, fontweight='bold')
        ax1.set_xticklabels(names, rotation=45, ha='right')
        ax1.grid(True, alpha=0.2, axis='y')
        
        # Add value labels
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'${height:.0f}K',
                    ha='center', va='bottom', fontweight='bold')
        
        # Deal count chart
        bars2 = ax2.bar(names, deal_counts, color='#4a90e2', alpha=0.8)
        ax2.set_ylabel('Number of Deals Won', fontsize=12)
        ax2.set_title('Top Performers - Deals Won', fontsize=14, fontweight='bold')
        ax2.set_xticklabels(names, rotation=45, ha='right')
        ax2.grid(True, alpha=0.2, axis='y')
        
        # Add value labels
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # Convert to base64 string
        buffer = BytesIO()
        plt.savefig(buffer, format='png', transparent=True, dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return image_base64
    
    @staticmethod
    def generate_customer_acquisition_chart():
        """Generate customer acquisition and ROI chart"""
        ChartGenerator.setup_style()
        
        # Get customer data for last 6 months
        months = []
        new_customers = []
        acquisition_costs = []
        
        for i in range(5, -1, -1):
            month_date = datetime.now() - timedelta(days=30*i)
            month_name = month_date.strftime('%b')
            months.append(month_name)
            
            # Count new customers in this month
            month_start = datetime(month_date.year, month_date.month, 1)
            if month_date.month == 12:
                month_end = datetime(month_date.year + 1, 1, 1)
            else:
                month_end = datetime(month_date.year, month_date.month + 1, 1)
            
            customers = Customer.objects.filter(
                created_date__gte=month_start,
                created_date__lt=month_end
            ).count()
            new_customers.append(customers)
            
            # Simulated acquisition cost (in real app, this would come from marketing data)
            acquisition_costs.append(np.random.randint(50, 200))
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.patch.set_alpha(0.0)
        
        # Customer acquisition chart
        ax1.plot(months, new_customers, marker='o', color='#50c878', linewidth=2, markersize=8)
        ax1.fill_between(range(len(months)), new_customers, alpha=0.3, color='#50c878')
        ax1.set_xlabel('Month', fontsize=12)
        ax1.set_ylabel('New Customers', fontsize=12)
        ax1.set_title('Customer Acquisition Trend', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.2)
        
        # Add value labels
        for i, (month, count) in enumerate(zip(months, new_customers)):
            ax1.text(i, count + 1, str(count), ha='center', fontweight='bold')
        
        # CAC (Customer Acquisition Cost) chart
        x = np.arange(len(months))
        width = 0.35
        
        bars = ax2.bar(x, acquisition_costs, width, color='#4a90e2', alpha=0.8)
        ax2.set_xlabel('Month', fontsize=12)
        ax2.set_ylabel('Cost per Customer ($)', fontsize=12)
        ax2.set_title('Customer Acquisition Cost', fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(months)
        ax2.grid(True, alpha=0.2, axis='y')
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'${int(height)}',
                    ha='center', va='bottom', fontweight='bold')
        
        # Add average line
        avg_cost = np.mean(acquisition_costs)
        ax2.axhline(y=avg_cost, color='#ffd700', linestyle='--', linewidth=2, alpha=0.7)
        ax2.text(len(months)-1, avg_cost, f'Avg: ${avg_cost:.0f}', 
                ha='right', va='bottom', color='#ffd700', fontweight='bold')
        
        plt.tight_layout()
        
        # Convert to base64 string
        buffer = BytesIO()
        plt.savefig(buffer, format='png', transparent=True, dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return image_base64