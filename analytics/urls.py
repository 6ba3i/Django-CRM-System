# Analytics URL patterns
from django.urls import path
from . import views

urlpatterns = [
    path('', views.analytics_dashboard, name='analytics_dashboard'),
    path('api/metrics/', views.metrics_api, name='analytics_metrics_api'),
    path('api/trends/', views.trends_api, name='analytics_trends_api'),
    path('export/', views.export_report, name='analytics_export'),
    path('chart/<str:chart_type>/', views.chart_image, name='analytics_chart'),
    path('custom-report/', views.custom_report, name='custom_report'),
    path('realtime/', views.realtime_dashboard, name='realtime_dashboard'),
]