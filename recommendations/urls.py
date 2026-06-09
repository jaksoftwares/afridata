"""
URL configuration for the recommendations app.

The recommendations app routes are configured through its API module:
    - recommendations/api/urls.py contains the REST API routes

All recommendations endpoints are prefixed with /api/recommendations/
(as configured in the main afridata/urls.py)

This file is kept for future template-based routes or dashboard pages.
"""
from django.urls import path

app_name = 'recommendations'

urlpatterns = [
    # All routes are in recommendations.api.urls
    # This file is reserved for template-based views if needed
]

