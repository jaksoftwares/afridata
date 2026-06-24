# admin_dashboard/urls.py
from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Dashboard home
    path('', views.dashboard_home, name='dashboard_home'),
    
    # User management
    path('users/', views.user_management, name='user_management'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('users/<int:user_id>/verify/', views.verify_user, name='verify_user'),
    path('users/<int:user_id>/moderate/', views.moderate_user, name='moderate_user'),
    path('users/<int:user_id>/adjust-tokens/', views.adjust_user_tokens, name='adjust_user_tokens'),
    
    # Dataset management
    path('datasets/', views.dataset_management, name='dataset_management'),
    path('datasets/<int:dataset_id>/action/', views.dataset_action, name='dataset_action'),
    path('datasets/bulk-action/', views.dataset_bulk_action, name='dataset_bulk_action'),
    path('moderation-queue/', views.moderation_queue, name='moderation_queue'),
    path('moderation-queue/<int:queue_id>/moderate/', views.moderate_dataset, name='moderate_dataset'),
    
    # Token management
    path('tokens/', views.token_management, name='token_management'),
    
    # User moderation
    path('user-moderation/', views.user_moderation, name='user_moderation'),
    
    # Bulk actions
    path('bulk-actions/', views.bulk_actions, name='bulk_actions'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/create/', views.create_notification, name='create_notification'),
    
    # System settings
    path('settings/', views.system_settings, name='system_settings'),
    
    # System metrics
    path('metrics/', views.system_metrics, name='system_metrics'),
    
    # Community management
    path('community/', views.community_management, name='community_management'),
    path('community/topics/create/', views.community_create_topic, name='community_create_topic'),
    path('community/topics/<int:topic_id>/delete/', views.community_delete_topic, name='community_delete_topic'),
    path('community/threads/<int:thread_id>/delete/', views.community_delete_thread, name='community_delete_thread'),
    path('community/posts/<int:post_id>/delete/', views.community_delete_post, name='community_delete_post'),
    
    # API management
    path('api/', views.api_management, name='api_management'),
    path('api/update-rate-limits/', views.update_rate_limits, name='update_rate_limits'),
    
    # System logs
    path('logs/', views.system_logs, name='system_logs'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/generate/', views.generate_report, name='generate_report'),
    path('reports/<int:report_id>/delete/', views.delete_report, name='delete_report'),
    
    # Data export
    path('export/', views.export_data, name='export_data'),
    
    # Analytics APIs & Pages
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('api/analytics/', views.analytics_api, name='analytics_api'),
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    
    # Newsletters
    path('newsletters/', views.newsletter_campaigns, name='newsletter_campaigns'),
]