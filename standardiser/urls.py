"""
Django URL Configuration for Standardiser App
Routes for automated processing, review, and download workflows
"""
from django.urls import path
from . import views

app_name = 'standardiser'

urlpatterns = [
    # Main workflow URLs
    path('standardize/<slug:dataset_slug>/', 
         views.initiate_standardization, 
         name='standardize_dataset'),
    
    path('ready/<uuid:job_id>/', 
         views.standardisation_ready, 
         name='standardisation_ready'),
    
    path('review/<uuid:job_id>/', 
         views.review_mappings, 
         name='review_mappings'),
    
    path('download/<uuid:job_id>/', 
         views.download_file, 
         name='download_file'),
    
    # Job management URLs
    path('jobs/', 
         views.job_list, 
         name='job_list'),
    
    path('jobs/<uuid:job_id>/', 
         views.job_detail, 
         name='job_detail'),
    
    path('jobs/<uuid:job_id>/delete/', 
         views.delete_job, 
         name='delete_job'),
    
    # API endpoints
    path('api/job-status/<uuid:job_id>/', 
         views.job_status_api, 
         name='api_job_status'),
]
