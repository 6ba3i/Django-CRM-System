 # Main URL routing
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup_view, name='signup'),
    
    # Main dashboard
    path('', views.dashboard_view, name='dashboard'),
    
    # App URLs
    path('customers/', include('customers.urls')),
    path('sales/', include('sales.urls')),
    path('analytics/', include('analytics.urls')),
    
    # API endpoints
    path('api/dashboard-metrics/', views.dashboard_metrics_api, name='dashboard_metrics_api'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)