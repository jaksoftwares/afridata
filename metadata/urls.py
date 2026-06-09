"""
URL configuration for the metadata app.

The metadata app routes are configured through its API module:
    - metadata/api/urls.py contains the REST API routes

All metadata endpoints are prefixed with /api/metadata/
(as configured in the main afridata/urls.py)

This file is kept for future template-based routes or admin pages.
"""
from django.urls import path

app_name = 'metadata'

urlpatterns = [
    # All routes are in metadata.api.urls
    # This file is reserved for template-based views if needed
]
