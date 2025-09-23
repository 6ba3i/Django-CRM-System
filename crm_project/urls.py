from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # Main pages
    path('', views.dashboard_view, name='dashboard'),
    path('customers/', views.customers_view, name='customers'),
    path('employees/', views.employees_view, name='employees'),
    path('deals/', views.deals_view, name='deals'),
    path('tasks/', views.tasks_view, name='tasks'),
    path('analytics/', views.analytics_view, name='analytics'),
    
    # CRUD operations
    path('api/customer/add/', views.add_customer, name='add_customer'),
    path('api/employee/add/', views.add_employee, name='add_employee'),
    path('api/deal/add/', views.add_deal, name='add_deal'),
    path('api/task/add/', views.add_task, name='add_task'),
    
    # Generic update and delete
    path('api/<str:collection>/<str:doc_id>/update/', views.update_record, name='update_record'),
    path('api/<str:collection>/<str:doc_id>/delete/', views.delete_record, name='delete_record'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)