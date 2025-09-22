# Main URL routing
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication URLs (Google OAuth)
    path('accounts/', include('allauth.urls')),
    
    # Main dashboard
    path('', views.dashboard_view, name='dashboard'),
    
    # App URLs
    path('customers/', include('customers.urls')),
    path('sales/', include('sales.urls')),
    path('analytics/', include('analytics.urls')),
    
    # API endpoints
    path('api/dashboard-metrics/', views.dashboard_metrics_api, name='dashboard_metrics_api'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('api/init/', views.initialize_system, name='initialize_system'),
    
    # Profile management
    path('profile/', views.profile_view, name='profile'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)