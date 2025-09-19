# Customer URL patterns
from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('create/', views.customer_create, name='customer_create'),
    path('<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('<int:customer_id>/edit/', views.customer_update, name='customer_update'),
    path('<int:customer_id>/delete/', views.customer_delete, name='customer_delete'),
    path('<int:customer_id>/interaction/add/', views.interaction_add, name='interaction_add'),
    path('api/search/', views.customer_search_api, name='customer_search_api'),
    path('api/quick-add/', views.customer_quick_add_api, name='customer_quick_add_api'),
    path('export/', views.customer_export, name='customer_export'),
    path('analytics/', views.customer_analytics, name='customer_analytics'),
]