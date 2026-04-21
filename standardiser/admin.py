"""
Admin configuration for standardiser app.
"""

from django.contrib import admin
from .models import StandardisationJob, JobResult, SchemaMappingEdit, DatasetVersion, ProcessingLog


@admin.register(StandardisationJob)
class StandardisationJobAdmin(admin.ModelAdmin):
    list_display = ('job_id', 'dataset_name', 'domain', 'status', 'created_at', 'user')
    list_filter = ('status', 'domain', 'created_at')
    search_fields = ('dataset_name', 'job_id')
    readonly_fields = ('job_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(JobResult)
class JobResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'used_cached_schema', 'created_at')
    list_filter = ('created_at', 'used_cached_schema')
    search_fields = ('job__dataset_name', 'job__job_id')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(SchemaMappingEdit)
class SchemaMappingEditAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'edited_at', 'edited_by')
    list_filter = ('edited_at', 'applied')
    search_fields = ('job__dataset_name', 'original_column_name')
    readonly_fields = ('edited_at',)
    ordering = ('-edited_at',)


@admin.register(DatasetVersion)
class DatasetVersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'version_number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('job__dataset_name',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'level', 'step', 'created_at')
    list_filter = ('level', 'created_at')
    search_fields = ('job__dataset_name', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
