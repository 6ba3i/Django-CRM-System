 # Sales URL patterns
from django.urls import path
from . import views

urlpatterns = [
    path('pipeline/', views.pipeline_view, name='pipeline_view'),
    path('deals/', views.deal_list, name='deal_list'),
    path('deals/create/', views.deal_create, name='deal_create'),
    path('deals/<int:deal_id>/', views.deal_detail, name='deal_detail'),
    path('deals/<int:deal_id>/edit/', views.deal_update, name='deal_update'),
    path('deals/<int:deal_id>/delete/', views.deal_delete, name='deal_delete'),
    path('deals/<int:deal_id>/activity/add/', views.activity_add, name='activity_add'),
    path('api/deal/<int:deal_id>/move/', views.deal_move_stage, name='deal_move_stage'),
    path('api/activity/<int:activity_id>/complete/', views.activity_complete, name='activity_complete'),
    path('api/pipeline/', views.pipeline_api, name='pipeline_api'),
    path('forecast/', views.sales_forecast, name='sales_forecast'),
    path('team/', views.team_performance, name='team_performance'),
]