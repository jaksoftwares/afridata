#dataset/urls.py
from django.urls import path
from . import views
from . import chunked_views

urlpatterns = [
    # Dataset listing and browsing
    path('', views.dataset_list, name='dataset_list'),
    
    # Dataset upload
    path('upload/', views.upload_dataset, name='upload_dataset'),
    path('upload/chunks/start/', chunked_views.chunked_upload_start, name='chunked_upload_start'),
    path('upload/chunks/<str:upload_id>/', chunked_views.chunked_upload_status, name='chunked_upload_status'),
    path('upload/chunks/<str:upload_id>/<int:index>/', chunked_views.chunked_upload_part, name='chunked_upload_part'),

    # User profile tokens
    path('tokens/history/', views.token_history, name='token_history'),
    
    # Comment functionality
    path('comment/<slug:slug>/post/', views.post_comment, name='post_comment'),
    path('comment/<int:comment_id>/upvote/', views.upvote_comment, name='upvote_comment'),

    # Dataset detail and related pages (must be at the bottom to avoid catching specific routes)
    path('<slug:slug>/', views.dataset_detail, name='dataset_detail'),
    path('<slug:slug>/generate-metadata/', views.generate_metadata, name='generate_metadata'),
    path('<slug:slug>/preview/', views.dataset_preview, name='dataset_preview'),
    path('<slug:slug>/download/', views.download_dataset, name='download_dataset'),
    path('<slug:slug>/edit/', views.edit_dataset, name='edit_dataset'),
    path('<slug:slug>/delete/', views.delete_dataset, name='delete_dataset'),
    path('<slug:slug>/comments/', views.dataset_comments, name='dataset_comments'),
]