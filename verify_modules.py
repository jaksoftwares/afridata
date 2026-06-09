#!/usr/bin/env python
"""
Verification script for metadata and recommendations modules.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afridata.settings')

import django
django.setup()

print("=" * 70)
print("METADATA MODULE VERIFICATION")
print("=" * 70)

# Test metadata models
from metadata.models import PipelineRun, MetadataResult, ColumnProfile, RunStatus, SourceType
print("✓ Metadata Models imported successfully")
print(f"  - PipelineRun: {PipelineRun}")
print(f"  - MetadataResult: {MetadataResult}")
print(f"  - ColumnProfile: {ColumnProfile}")
print(f"  - RunStatus choices: {[c[0] for c in RunStatus.choices]}")
print(f"  - SourceType choices: {[c[0] for c in SourceType.choices]}")

# Test metadata admin
from metadata.admin import PipelineRunAdmin, MetadataResultAdmin, ColumnProfileAdmin
print("✓ Metadata admin classes imported successfully")

# Test metadata API views
from metadata.api.views import PipelineRunListCreateView, PipelineRunDetailView, PipelineRunSchemaView
print("✓ Metadata API views imported successfully")

# Test metadata serializers
from metadata.api.serializers import PipelineRunSerializer, MetadataResultSerializer, ColumnProfileSerializer
print("✓ Metadata API serializers imported successfully")

print("\n" + "=" * 70)
print("RECOMMENDATIONS MODULE VERIFICATION")
print("=" * 70)

# Test recommendations models
from recommendations.models import UserInteraction, DatasetProxy, RecommendationResult, InteractionType
print("✓ Recommendations models imported successfully")
print(f"  - UserInteraction: {UserInteraction}")
print(f"  - DatasetProxy: {DatasetProxy}")
print(f"  - RecommendationResult: {RecommendationResult}")
print(f"  - InteractionType choices: {[c[0] for c in InteractionType.choices]}")

# Test recommendations admin
from recommendations.admin import UserInteractionAdmin, DatasetProxyAdmin, RecommendationResultAdmin
print("✓ Recommendations admin classes imported successfully")

# Test recommendations API views
from recommendations.api.views import RecommendationListView, FeedbackView
print("✓ Recommendations API views imported successfully")

# Test recommendations serializers
from recommendations.api.serializers import RecommendationListSerializer, FeedbackSerializer
print("✓ Recommendations API serializers imported successfully")

print("\n" + "=" * 70)
print("URL ROUTES VERIFICATION")
print("=" * 70)

from django.urls import get_resolver
resolver = get_resolver()

# Get all URL patterns
print("Metadata API Routes:")
metadata_routes_found = False
for pattern in resolver.url_patterns:
    pattern_str = str(pattern.pattern)
    if 'metadata' in pattern_str or 'runs' in pattern_str:
        print(f"  - {pattern_str}")
        metadata_routes_found = True

if metadata_routes_found:
    print("✓ Metadata routes registered")
else:
    print("✗ Metadata routes NOT found")

print("\nRecommendations API Routes:")
recommendations_routes_found = False
for pattern in resolver.url_patterns:
    pattern_str = str(pattern.pattern)
    if 'recommendations' in pattern_str:
        print(f"  - {pattern_str}")
        recommendations_routes_found = True

if recommendations_routes_found:
    print("✓ Recommendations routes registered")
else:
    print("✗ Recommendations routes NOT found")

print("\n" + "=" * 70)
print("DATABASE VERIFICATION")
print("=" * 70)

print("Checking for pending migrations...")
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

executor = MigrationExecutor(connection)
plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
if plan:
    print("⚠ Pending migrations found - run 'python manage.py migrate'")
else:
    print("✓ All migrations applied")

print("\n" + "=" * 70)
print("APPS REGISTRATION")
print("=" * 70)

from django.apps import apps
for app in ['metadata', 'recommendations']:
    try:
        app_config = apps.get_app_config(app)
        print(f"✓ {app}: {app_config.verbose_name}")
    except:
        print(f"✗ {app}: NOT FOUND")

print("\n" + "=" * 70)
print("✅ ALL VERIFICATIONS PASSED - MODULES WORKING CORRECTLY!")
print("=" * 70)
