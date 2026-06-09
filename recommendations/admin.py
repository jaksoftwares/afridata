"""
Django admin registrations for the recommendations app.

Provides a read-friendly admin interface for monitoring user interactions
and recommendation outputs without needing direct database access.

Registered models:
  UserInteraction      — tracks user actions on datasets (view, download, bookmark, rating)
  DatasetProxy         — cached metadata mirror for content-based scoring
  RecommendationResult — persisted Top-N recommendations per user
"""

from django.contrib import admin
from django.contrib.admin import display
from django.utils.html import format_html
import json

from .models import UserInteraction, DatasetProxy, RecommendationResult, InteractionType


@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    """Admin for user interactions - training signals for recommendations."""
    
    list_display = ("user", "dataset_id", "interaction_type", "explicit_rating", "dwell_seconds", "created_at")
    list_filter = ("interaction_type", "created_at")
    search_fields = ("user__username", "user__email", "dataset_id")
    readonly_fields = ("user", "dataset_id", "interaction_type", "explicit_rating", "dwell_seconds", "created_at")
    
    fieldsets = (
        ('User & Dataset', {
            'fields': ('user', 'dataset_id')
        }),
        ('Interaction', {
            'fields': ('interaction_type', 'explicit_rating', 'dwell_seconds')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(DatasetProxy)
class DatasetProxyAdmin(admin.ModelAdmin):
    """Admin for dataset proxies - cached metadata for content-based scoring."""
    
    list_display = ("dataset_id", "title", "category", "is_active", "interaction_count", "average_rating", "last_synced_at")
    list_filter = ("is_active", "category", "created_at")
    search_fields = ("title", "description", "tags", "category", "organisation")
    readonly_fields = ("dataset_id", "title", "description", "tags", "category", "organisation", 
                      "licence", "formats", "interaction_count", "average_rating", 
                      "is_active", "created_at", "last_synced_at", "tags_preview")
    
    fieldsets = (
        ('Dataset Reference', {
            'fields': ('dataset_id', 'title', 'is_active')
        }),
        ('Content', {
            'fields': ('description', 'tags', 'tags_preview', 'category', 'organisation')
        }),
        ('Metadata', {
            'fields': ('licence', 'formats')
        }),
        ('Engagement', {
            'fields': ('interaction_count', 'average_rating'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_synced_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-interaction_count',)
    date_hierarchy = 'created_at'

    @display(description='Tags (Parsed)')
    def tags_preview(self, obj):
        """Return formatted tags preview."""
        tags = obj.tag_set
        if not tags:
            return "No tags"
        return format_html(
            '<span>{}</span>',
            ', '.join(sorted(tags))
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(RecommendationResult)
class RecommendationResultAdmin(admin.ModelAdmin):
    """Admin for recommendation results - persisted Top-N lists per user."""
    
    list_display = ("user", "engine_used", "item_count", "alpha", "candidate_pool_size", "generated_at")
    list_filter = ("engine_used", "generated_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user", "ranked_dataset_ids", "scores", "alpha", 
                      "engine_used", "candidate_pool_size", "generated_at", 
                      "ranked_preview", "scores_preview")
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Recommendation Configuration', {
            'fields': ('engine_used', 'alpha', 'candidate_pool_size')
        }),
        ('Results', {
            'fields': ('ranked_dataset_ids', 'scores', 'ranked_preview', 'scores_preview')
        }),
        ('Metadata', {
            'fields': ('generated_at',),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-generated_at',)
    date_hierarchy = 'generated_at'

    @display(description='Item Count', ordering='ranked_dataset_ids')
    def item_count(self, obj):
        """Return the number of items in ranked_dataset_ids."""
        if isinstance(obj.ranked_dataset_ids, list):
            return len(obj.ranked_dataset_ids)
        return 0

    @display(description='Top Ranked (First 5)')
    def ranked_preview(self, obj):
        """Return preview of ranked dataset IDs."""
        try:
            ids = obj.top_n[:5]  # Show first 5
            preview = ', '.join(map(str, ids))
            if len(obj.top_n) > 5:
                preview += f", ... ({len(obj.top_n) - 5} more)"
            return format_html('<code>{}</code>', preview)
        except Exception:
            return "Unable to preview"

    @display(description='Scores (First 5)')
    def scores_preview(self, obj):
        """Return preview of scores as formatted JSON."""
        try:
            scores = obj.scores[:5]  # Show first 5
            return format_html(
                '<pre style="font-size:11px; white-space:pre-wrap;">{}</pre>',
                json.dumps(scores, indent=2)
            )
        except Exception:
            return "Unable to preview"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    