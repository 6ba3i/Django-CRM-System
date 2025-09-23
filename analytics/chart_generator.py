import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from datetime import datetime, timedelta
from collections import Counter
import random

# Set dark theme for glassmorphism aesthetic
plt.style.use('dark_background')

class ChartGenerator:
    """Generate beautiful charts with glassmorphism style"""
    
    # Glassmorphism color palette
    COLORS = ['#4a90e2', '#50c878', '#ffd700', '#8a2be2', '#ff6b6b', '#00bcd4', '#ff9800']
    
    @staticmethod
    def _setup_glass_style(ax, title):
        """Apply glassmorphism styling to charts"""
        # Use matplotlib-compatible color formats
        ax.set_facecolor((0, 0, 0, 0.02))  # Nearly transparent black
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color((1, 1, 1, 0.3))  # White with opacity
        ax.spines['bottom'].set_color((1, 1, 1, 0.3))
        ax.tick_params(colors=(1, 1, 1, 0.8))
        ax.set_title(title, fontsize=16, fontweight='bold', color='white', pad=20)
        ax.grid(True, alpha=0.1, linestyle='--')
    
    @staticmethod
    def _get_base64_image(fig):
        """Convert matplotlib figure to base64 STRING"""
        buffer = BytesIO()
        fig.patch.set_facecolor('none')  # Transparent background
        fig.patch.set_alpha(0.0)
        fig.savefig(buffer, format='png', transparent=True, dpi=120, bbox_inches='tight', facecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        return image_base64
    
    @staticmethod
    def generate_pie_chart(data_list: list, title: str) -> str:
        """Generate glassmorphic pie chart from LIST"""
        if not data_list:
            # Generate sample data
            data_list = ['Active'] * 5 + ['Lead'] * 3 + ['Prospect'] * 2
        
        # Count occurrences using Counter (DICTIONARY-like)
        counts = Counter(data_list)
        
        if not counts:
            return ""
        
        fig, ax = plt.subplots(figsize=(10, 8), facecolor='none')
        ax.set_facecolor('none')
        
        # Create pie with explosion effect
        explode = [0.05] * len(counts)
        wedges, texts, autotexts = ax.pie(
            counts.values(),
            labels=counts.keys(),
            colors=ChartGenerator.COLORS[:len(counts)],
            autopct='%1.1f%%',
            startangle=90,
            explode=explode,
            shadow=False,  # Shadow doesn't work well with transparent background
            textprops={'color': 'white', 'fontsize': 12}
        )
        
        # Beautify text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(title, fontsize=16, fontweight='bold', color='white', pad=20)
        plt.tight_layout()
        
        return ChartGenerator._get_base64_image(fig)
    
    @staticmethod
    def generate_bar_chart(data_list: list, field: str, title: str) -> str:
        """Generate glassmorphic bar chart from LIST of DICTIONARIES"""
        if not data_list:
            # Generate sample data
            data_list = [
                {'stage': 'New', 'value': 10},
                {'stage': 'Contact', 'value': 15},
                {'stage': 'Proposal', 'value': 8},
                {'stage': 'Closed', 'value': 5}
            ]
        
        # Group data using DICTIONARY
        grouped = {}
        for item in data_list:
            key = item.get(field, 'Unknown')
            grouped[key] = grouped.get(key, 0) + 1
        
        if not grouped:
            grouped = {'Sample': 10, 'Data': 15, 'Chart': 8}
        
        fig, ax = plt.subplots(figsize=(12, 6), facecolor='none')
        ax.set_facecolor('none')
        
        x_pos = np.arange(len(grouped))
        bars = ax.bar(x_pos, list(grouped.values()), 
                      color=ChartGenerator.COLORS[:len(grouped)],
                      alpha=0.8, edgecolor='white', linewidth=2)
        
        # Add value labels with glow effect
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=11, 
                   color='white', fontweight='bold')
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(list(grouped.keys()), rotation=45, ha='right')
        ChartGenerator._setup_glass_style(ax, title)
        
        plt.tight_layout()
        return ChartGenerator._get_base64_image(fig)
    
    @staticmethod
    def generate_line_chart(data_list: list, title: str) -> str:
        """Generate glassmorphic line chart showing trends"""
        # Generate sample monthly data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        values = [random.randint(10000, 100000) for _ in months]
        
        fig, ax = plt.subplots(figsize=(12, 6), facecolor='none')
        ax.set_facecolor('none')
        
        # Create gradient fill
        x = np.arange(len(months))
        ax.plot(x, values, color='#50c878', linewidth=3, marker='o', 
                markersize=8, markerfacecolor='#4a90e2', markeredgewidth=2,
                markeredgecolor='white', label='Revenue')
        
        # Add gradient fill
        ax.fill_between(x, values, alpha=0.3, color='#50c878')
        
        ax.set_xticks(x)
        ax.set_xticklabels(months)
        ax.set_ylabel('Revenue ($)', fontsize=12, color='white')
        
        ChartGenerator._setup_glass_style(ax, title)
        ax.legend(loc='upper left', framealpha=0.3)
        
        plt.tight_layout()
        return ChartGenerator._get_base64_image(fig)
    
    @staticmethod
    def generate_donut_chart(data_list: list, title: str) -> str:
        """Generate glassmorphic donut chart"""
        if not data_list:
            # Generate sample data
            data_list = ['Sales'] * 5 + ['Marketing'] * 3 + ['Engineering'] * 4 + ['HR'] * 2
        
        counts = Counter(data_list)
        
        if not counts:
            return ""
        
        fig, ax = plt.subplots(figsize=(10, 8), facecolor='none')
        ax.set_facecolor('none')
        
        # Create donut
        wedges, texts, autotexts = ax.pie(
            counts.values(),
            labels=counts.keys(),
            colors=ChartGenerator.COLORS[:len(counts)],
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.85,
            textprops={'color': 'white', 'fontsize': 11}
        )
        
        # Draw center circle for donut
        centre_circle = plt.Circle((0, 0), 0.70, fc='#1a1d29', linewidth=3, 
                                   edgecolor='white', alpha=0.3)
        ax.add_artist(centre_circle)
        
        # Add total in center
        total = sum(counts.values())
        ax.text(0, 0, f'{total}\nTotal', ha='center', va='center', 
                fontsize=20, color='white', fontweight='bold')
        
        ax.set_title(title, fontsize=16, fontweight='bold', color='white', pad=20)
        plt.tight_layout()
        
        return ChartGenerator._get_base64_image(fig)
    
    @staticmethod
    def generate_area_chart(data_list: list, title: str) -> str:
        """Generate glassmorphic area chart"""
        # Generate time series data
        days = 30
        dates = [(datetime.now() - timedelta(days=x)).strftime('%d') for x in range(days, 0, -1)]
        values = [random.randint(5, 50) for _ in dates]
        
        fig, ax = plt.subplots(figsize=(12, 6), facecolor='none')
        ax.set_facecolor('none')
        
        x = np.arange(len(dates))
        ax.fill_between(x, 0, values, color='#4a90e2', alpha=0.3)
        ax.plot(x, values, color='#4a90e2', linewidth=2, marker='o', markersize=4)
        
        # Only show every 5th date label
        ax.set_xticks(x[::5])
        ax.set_xticklabels(dates[::5])
        ax.set_ylabel('Count', fontsize=12, color='white')
        
        ChartGenerator._setup_glass_style(ax, title)
        plt.tight_layout()
        
        return ChartGenerator._get_base64_image(fig)
    
    @staticmethod
    def generate_scatter_chart(data_list: list, title: str) -> str:
        """Generate glassmorphic scatter plot"""
        # Generate sample data
        x = [random.randint(10, 100) for _ in range(50)]
        y = [random.randint(1000, 50000) for _ in range(50)]
        
        fig, ax = plt.subplots(figsize=(10, 8), facecolor='none')
        ax.set_facecolor('none')
        
        scatter = ax.scatter(x, y, c=y, cmap='plasma', s=100, alpha=0.6, 
                           edgecolors='white', linewidth=2)
        
        ax.set_xlabel('Probability (%)', fontsize=12, color='white')
        ax.set_ylabel('Deal Value ($)', fontsize=12, color='white')
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Value Range', color='white')
        cbar.ax.tick_params(colors='white')
        
        ChartGenerator._setup_glass_style(ax, title)
        plt.tight_layout()
        
        return ChartGenerator._get_base64_image(fig)
    
    @staticmethod
    def generate_horizontal_bar(data_list: list, title: str) -> str:
        """Generate horizontal bar chart"""
        # Sample data for employees
        departments = ['Sales', 'Marketing', 'Engineering', 'HR', 'Finance']
        salaries = [75000, 65000, 85000, 55000, 70000]
        
        fig, ax = plt.subplots(figsize=(10, 6), facecolor='none')
        ax.set_facecolor('none')
        
        y_pos = np.arange(len(departments))
        bars = ax.barh(y_pos, salaries, color=ChartGenerator.COLORS[:len(departments)],
                      alpha=0.8, edgecolor='white', linewidth=2)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(departments)
        ax.set_xlabel('Average Salary ($)', fontsize=12, color='white')
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'${width:,.0f}',
                   ha='left', va='center', fontsize=11,
                   color='white', fontweight='bold')
        
        ChartGenerator._setup_glass_style(ax, title)
        plt.tight_layout()
        
        return ChartGenerator._get_base64_image(fig)
    
    @staticmethod
    def generate_stacked_bar(employees: list, deals: list, title: str) -> str:
        """Generate stacked bar chart for complex data"""
        departments = ['Sales', 'Marketing', 'Engineering', 'HR']
        categories = ['Q1', 'Q2', 'Q3', 'Q4']
        
        # Generate sample data using numpy arrays
        data = np.random.randint(10, 100, size=(len(departments), len(categories)))
        
        fig, ax = plt.subplots(figsize=(12, 6), facecolor='none')
        ax.set_facecolor('none')
        
        x = np.arange(len(categories))
        width = 0.6
        bottom = np.zeros(len(categories))
        
        for i, dept in enumerate(departments):
            ax.bar(x, data[i], width, label=dept, bottom=bottom,
                  color=ChartGenerator.COLORS[i], alpha=0.8,
                  edgecolor='white', linewidth=1)
            bottom += data[i]
        
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.set_ylabel('Performance Score', fontsize=12, color='white')
        ax.legend(loc='upper left', framealpha=0.3)
        
        ChartGenerator._setup_glass_style(ax, title)
        plt.tight_layout()
        
        return ChartGenerator._get_base64_image(fig)