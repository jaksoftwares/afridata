#dataset/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dataset listing and browsing
    path('', views.dataset_list, name='dataset_list'),
    
    # Dataset detail and related pages
    path('dataset/<slug:slug>/', views.dataset_detail, name='dataset_detail'),
    path('dataset/<slug:slug>/preview/', views.dataset_preview, name='dataset_preview'),
    path('dataset/<slug:slug>/download/', views.download_dataset, name='download_dataset'),
    path('dataset/<slug:slug>/comments/', views.dataset_comments, name='dataset_comments'),

    
    # Comment functionality
    path('comment/<slug:slug>/post/', views.post_comment, name='post_comment'),

    path('comment/<int:comment_id>/upvote/', views.upvote_comment, name='upvote_comment'),
    
    # Dataset upload
    path('datasets/upload/', views.upload_dataset, name='upload_dataset'),
    
    # User dashboard and profile pages
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('tokens/history/', views.token_history, name='token_history'),
]