"""
Django admin registration for the Metadata Extraction Pipeline.

Provides a read-friendly admin interface for monitoring pipeline
runs without needing direct database access. Useful during
development and for ops teams.

Registers: PipelineRun, MetadataResult, ColumnProfile

Admin features:
    - PipelineRunAdmin:  list_display: id, source, status, created_at, started_at
    - MetadataResultAdmin: list_display: run, column_count, created_at
    - Both are read-only (monitoring, no editing)
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count

from .models import ColumnProfile, MetadataResult, PipelineRun


@admin.register(PipelineRun)
class PipelineRunAdmin(admin.ModelAdmin):
    """Admin for pipeline runs - monitoring only, no editing."""
    
    list_display = ("id", "source", "status", "dataset_title", "elapsed_s", "created_at", "started_at")
    list_filter = ("status", "source", "created_at")
    search_fields = ("dataset_title", "dataset_description", "source_path")
    readonly_fields = ("id", "source", "source_path", "dataset_title", "dataset_description", 
                      "status", "error_message", "elapsed_s", "stage_times",
                      "created_at", "started_at", "finished_at")
    
    fieldsets = (
        ('Pipeline Configuration', {
            'fields': ('id', 'source', 'source_path', 'dataset_title', 'dataset_description')
        }),
        ('Execution Status', {
            'fields': ('status', 'error_message')
        }),
        ('Timing', {
            'fields': ('elapsed_s', 'stage_times', 'created_at', 'started_at', 'finished_at')
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


class MetadataResultInline(admin.StackedInline):
    """Inline display of MetadataResult within PipelineRun detail."""
    
    model = MetadataResult
    extra = 0
    readonly_fields = ("run", "column_count", "created_at", "schema_preview")
    fields = ("run", "column_count", "created_at", "schema_preview")
    can_delete = False

    def schema_preview(self, obj):
        """Return a truncated preview of the JSON schema."""
        import json
        
        try:
            preview_json = json.loads(obj.json_schema)
            pretty = json.dumps(preview_json, indent=2)
            preview = pretty[:500] + ("..." if len(pretty) > 500 else "")
            return format_html("<pre style='white-space:pre-wrap; font-size:11px;'>{}</pre>", preview)
        except Exception:
            return "Unable to preview schema"

    schema_preview.short_description = "JSON Schema Preview"


@admin.register(MetadataResult)
class MetadataResultAdmin(admin.ModelAdmin):
    """Admin for metadata results - monitoring only, no editing."""
    
    list_display = ("run_id", "column_count", "created_at")
    list_filter = ("run__status", "created_at")
    search_fields = ("run__dataset_title", "run__source_path")
    readonly_fields = ("run", "column_count", "created_at", "schema_dict", "schema_report", "schema_preview")
    
    fieldsets = (
        ('Run Reference', {
            'fields': ('run', 'column_count', 'created_at')
        }),
        ('Schema Data', {
            'fields': ('schema_dict', 'schema_report')
        }),
        ('Schema Preview', {
            'fields': ('schema_preview',),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    def schema_preview(self, obj):
        """Return a preview of the JSON schema."""
        import json
        
        try:
            pretty = json.dumps(json.loads(obj.json_schema), indent=2)
            preview = pretty[:1000] + ("..." if len(pretty) > 1000 else "")
            return format_html("<pre style='white-space:pre-wrap; font-size:11px;'>{}</pre>", preview)
        except Exception:
            return "Unable to preview schema"

    schema_preview.short_description = "JSON Schema Preview"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(ColumnProfile)
class ColumnProfileAdmin(admin.ModelAdmin):
    """Admin for column profiles - read-only monitoring."""
    
    list_display = ("run", "column_name", "dtype", "semantic_type", "semantic_confidence", "null_count")
    list_filter = ("run__status", "dtype", "semantic_type")
    search_fields = ("column_name", "run__dataset_title", "semantic_type")
    readonly_fields = ("run", "column_name", "dtype", "semantic_type", "semantic_confidence", 
                      "nullable", "unique_count", "null_count", "profile_data")
    
    fieldsets = (
        ('Column Information', {
            'fields': ('run', 'column_name', 'dtype', 'semantic_type', 'semantic_confidence')
        }),
        ('Profile Statistics', {
            'fields': ('nullable', 'unique_count', 'null_count'),
            'classes': ('collapse',)
        }),
        ('Full Profile Data', {
            'fields': ('profile_data',),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True