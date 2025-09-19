# Analytics views
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import json

from .chart_generator import ChartGenerator
from .data_processor import DataProcessor
from core.decorators import role_required, log_activity, cache_result
from customers.models import Customer
from sales.models import Deal

@login_required
@log_activity('view_analytics')
def analytics_dashboard(request):
    """Main analytics dashboard view"""
    # Get period from request
    period = request.GET.get('period', 'month')
    user_filter = request.user if not request.user.is_staff else None
    
    # Get dashboard metrics
    metrics = DataProcessor.get_dashboard_metrics(user=user_filter, period=period)
    
    # Get sales trends
    trends = DataProcessor.get_sales_trends(period=period, user=user_filter)
    
    # Get pipeline analytics
    pipeline_analytics = DataProcessor.get_pipeline_analytics()
    
    # Generate charts
    pipeline_chart = ChartGenerator.generate_pipeline_funnel()
    revenue_chart = ChartGenerator.generate_revenue_forecast()
    performance_chart = ChartGenerator.generate_performance_metrics()
    acquisition_chart = ChartGenerator.generate_customer_acquisition_chart()
    
    context = {
        'metrics': metrics,
        'trends': trends,
        'pipeline_analytics': pipeline_analytics,
        'pipeline_chart': pipeline_chart,
        'revenue_chart': revenue_chart,
        'performance_chart': performance_chart,
        'acquisition_chart': acquisition_chart,
        'period': period,
        'active_tab': 'analytics'
    }
    
    return render(request, 'analytics/dashboard.html', context)

@login_required
@require_http_methods(["GET"])
@cache_result(timeout=300)
def metrics_api(request):
    """API endpoint for dashboard metrics"""
    period = request.GET.get('period', 'month')
    user_filter = request.user if not request.user.is_staff else None
    
    metrics = DataProcessor.get_dashboard_metrics(user=user_filter, period=period)
    
    return JsonResponse(metrics)

@login_required
@require_http_methods(["GET"])
def trends_api(request):
    """API endpoint for sales trends"""
    period = request.GET.get('period', 'month')
    metric_type = request.GET.get('type', 'revenue')
    user_filter = request.user if not request.user.is_staff else None
    
    trends = DataProcessor.get_sales_trends(period=period, user=user_filter)
    
    # Format for Chart.js
    formatted_data = {
        'labels': trends['labels'],
        'datasets': [{
            'label': metric_type.title(),
            'data': trends[metric_type],
            'borderColor': '#50c878' if metric_type == 'revenue' else '#4a90e2',
            'backgroundColor': 'rgba(80, 200, 120, 0.1)' if metric_type == 'revenue' else 'rgba(74, 144, 226, 0.1)',
            'tension': 0.4
        }]
    }
    
    return JsonResponse(formatted_data)

@login_required
@role_required('Admin', 'Manager')
def export_report(request):
    """Export analytics report"""
    format_type = request.GET.get('format', 'pdf')
    period = request.GET.get('period', 'month')
    
    # Generate comprehensive report
    report_data = DataProcessor.export_analytics_report(format=format_type)
    
    if format_type == 'pdf':
        # Generate PDF using ReportLab or similar
        # For now, return JSON
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="analytics_report_{datetime.now().strftime("%Y%m%d")}.pdf"'
        # PDF generation would go here
        return response
    
    elif format_type == 'excel':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="analytics_report_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        # Excel generation would go here
        return response
    
    elif format_type == 'json':
        return JsonResponse(report_data)
    
    else:
        return JsonResponse({'error': 'Invalid format'}, status=400)

@login_required
def chart_image(request, chart_type):
    """Generate and return chart as image"""
    if chart_type == 'pipeline':
        image_data = ChartGenerator.generate_pipeline_funnel()
    elif chart_type == 'revenue':
        image_data = ChartGenerator.generate_revenue_forecast()
    elif chart_type == 'performance':
        image_data = ChartGenerator.generate_performance_metrics()
    elif chart_type == 'acquisition':
        image_data = ChartGenerator.generate_customer_acquisition_chart()
    else:
        return HttpResponse(status=404)
    
    # Return as base64 encoded image
    import base64
    image_binary = base64.b64decode(image_data)
    
    response = HttpResponse(image_binary, content_type='image/png')
    response['Content-Disposition'] = f'inline; filename="{chart_type}_chart.png"'
    
    return response

@login_required
@role_required('Admin', 'Manager')
def custom_report(request):
    """Custom report builder"""
    if request.method == 'POST':
        # Get report parameters
        data = json.loads(request.body)
        report_type = data.get('type')
        date_range = data.get('date_range')
        filters = data.get('filters', {})
        
        # Generate custom report based on parameters
        if report_type == 'sales':
            report = generate_sales_report(date_range, filters)
        elif report_type == 'customer':
            report = generate_customer_report(date_range, filters)
        elif report_type == 'pipeline':
            report = generate_pipeline_report(date_range, filters)
        else:
            return JsonResponse({'error': 'Invalid report type'}, status=400)
        
        return JsonResponse(report)
    
    # GET request - show report builder form
    return render(request, 'analytics/custom_report.html', {
        'active_tab': 'analytics'
    })

def generate_sales_report(date_range, filters):
    """Generate sales report"""
    start_date, end_date = parse_date_range(date_range)
    
    deals = Deal.objects.filter(
        created_date__range=(start_date, end_date)
    )
    
    # Apply filters
    if filters.get('status'):
        deals = deals.filter(status=filters['status'])
    if filters.get('stage'):
        deals = deals.filter(stage=filters['stage'])
    if filters.get('assigned_to'):
        deals = deals.filter(assigned_to_id=filters['assigned_to'])
    
    # Generate report data
    from django.db.models import Sum, Count, Avg
    
    report = {
        'period': date_range,
        'total_deals': deals.count(),
        'total_value': deals.aggregate(Sum('value'))['value__sum'] or 0,
        'average_value': deals.aggregate(Avg('value'))['value__avg'] or 0,
        'by_stage': {},
        'by_status': {},
        'top_deals': []
    }
    
    # Group by stage
    for stage in ['Lead', 'Qualified', 'Proposal', 'Negotiation']:
        stage_deals = deals.filter(stage=stage)
        report['by_stage'][stage] = {
            'count': stage_deals.count(),
            'value': stage_deals.aggregate(Sum('value'))['value__sum'] or 0
        }
    
    # Group by status
    for status in ['Active', 'Won', 'Lost', 'On Hold']:
        status_deals = deals.filter(status=status)
        report['by_status'][status] = {
            'count': status_deals.count(),
            'value': status_deals.aggregate(Sum('value'))['value__sum'] or 0
        }
    
    # Top deals
    top_deals = deals.order_by('-value')[:10]
    report['top_deals'] = [{
        'title': deal.title,
        'customer': deal.customer.name,
        'value': float(deal.value),
        'stage': deal.stage,
        'probability': deal.probability
    } for deal in top_deals]
    
    return report

def generate_customer_report(date_range, filters):
    """Generate customer report"""
    start_date, end_date = parse_date_range(date_range)
    
    customers = Customer.objects.filter(
        created_date__range=(start_date, end_date)
    )
    
    # Apply filters
    if filters.get('status'):
        customers = customers.filter(status=filters['status'])
    if filters.get('assigned_to'):
        customers = customers.filter(assigned_to_id=filters['assigned_to'])
    
    # Generate report data
    from django.db.models import Sum, Count
    
    report = {
        'period': date_range,
        'total_customers': customers.count(),
        'by_status': {},
        'top_customers': [],
        'acquisition_trend': []
    }
    
    # Group by status
    for status in ['Lead', 'Prospect', 'Active', 'Inactive']:
        report['by_status'][status] = customers.filter(status=status).count()
    
    # Top customers by deal value
    top_customers = customers.annotate(
        total_value=Sum('deals__value')
    ).order_by('-total_value')[:10]
    
    report['top_customers'] = [{
        'name': customer.name,
        'company': customer.company,
        'total_value': float(customer.total_value or 0),
        'deal_count': customer.deals.count()
    } for customer in top_customers]
    
    return report

def generate_pipeline_report(date_range, filters):
    """Generate pipeline report"""
    from sales.pipeline_logic import PipelineManager
    
    start_date, end_date = parse_date_range(date_range)
    
    # Get pipeline data
    pipeline_data = PipelineManager.get_pipeline_data(
        date_range=(start_date, end_date)
    )
    
    # Get conversion rates
    conversion_rates = PipelineManager.calculate_conversion_rates()
    
    # Get velocity metrics
    velocity_metrics = PipelineManager.calculate_velocity_metrics()
    
    report = {
        'period': date_range,
        'pipeline_data': pipeline_data,
        'conversion_rates': conversion_rates,
        'velocity_metrics': velocity_metrics,
        'forecast': PipelineManager.get_pipeline_forecast('quarter')
    }
    
    return report

def parse_date_range(date_range):
    """Parse date range string into start and end dates"""
    today = datetime.now().date()
    
    if date_range == 'today':
        return today, today
    elif date_range == 'week':
        return today - timedelta(days=7), today
    elif date_range == 'month':
        return today - timedelta(days=30), today
    elif date_range == 'quarter':
        return today - timedelta(days=90), today
    elif date_range == 'year':
        return today - timedelta(days=365), today
    else:
        # Custom date range (format: "YYYY-MM-DD to YYYY-MM-DD")
        try:
            start_str, end_str = date_range.split(' to ')
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
            return start_date, end_date
        except:
            return today - timedelta(days=30), today

@login_required
def realtime_dashboard(request):
    """Real-time analytics dashboard using WebSocket"""
    context = {
        'active_tab': 'analytics',
        'websocket_url': f'ws://localhost:8000/ws/analytics/'
    }
    return render(request, 'analytics/realtime.html', context)