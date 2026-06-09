"""
URL configuration for the Metadata Extraction API.

Registers all API routes using DRF's DefaultRouter and manual
path() entries. Include this file in the project's root urls.py:

    path('api/metadata/', include('metadata.api.urls')),

Route map:
    runs/                  → PipelineRunListCreateView
    runs/<pk>/             → PipelineRunDetailView
    runs/<pk>/schema/      → PipelineRunSchemaView
"""

from django.urls import path
from .views import (
    PipelineRunSchemaView,
    PipelineRunDetailView,
    PipelineRunListCreateView,
    PipelineRunColumnProfilesView,
)

app_name = "metadata"

urlpatterns = [
    path("runs/", PipelineRunListCreateView.as_view(), name="pipeline-run-list-create"),
    path("runs/<str:pk>/", PipelineRunDetailView.as_view(), name="pipeline-run-detail"),
    path("runs/<str:pk>/schema/", PipelineRunSchemaView.as_view(), name="pipeline-run-schema"),
    path("runs/<str:pk>/columns/", PipelineRunColumnProfilesView.as_view(), name="pipeline-run-columns"),
]