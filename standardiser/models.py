"""
Django Models for Data Standardisation Pipeline Integration
Handles job tracking, result caching, and user interactions with the pipeline
"""
from django.db import models
from django.utils import timezone
from django.conf import settings
import json
from datetime import datetime


class StandardisationJob(models.Model):
    """
    Represents a standardisation job in the pipeline
    Tracks status, metrics, and user interactions
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('review', 'Review Required'),
    ]
    
    # Job identification
    job_id = models.CharField(max_length=36, unique=True, db_index=True)
    
    # User and metadata
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='standardisation_jobs')
    dataset = models.ForeignKey('dataset.Dataset', on_delete=models.SET_NULL, null=True, blank=True, related_name='standardisation_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # File information
    original_filename = models.CharField(max_length=255)
    file_format = models.CharField(max_length=20, default='csv')  # csv, xlsx, json, etc.
    file_size = models.BigIntegerField(default=0)  # bytes
    
    # Domain and dataset context
    domain = models.CharField(max_length=100, db_index=True)
    dataset_name = models.CharField(max_length=255)
    
    # Pipeline status and results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Metrics from pipeline
    rows_original = models.IntegerField(default=0)
    rows_processed = models.IntegerField(default=0)
    columns_count = models.IntegerField(default=0)
    columns_mapped = models.IntegerField(default=0)
    
    # Quality scores
    ai_confidence = models.FloatField(default=0.0)  # 0-100%
    completeness = models.FloatField(default=0.0)  # 0-100%
    mapping_score = models.FloatField(default=0.0)  # 0-100%
    
    # Processing metadata
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    processing_duration_seconds = models.IntegerField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True, null=True)
    
    # User decisions
    user_reviewed = models.BooleanField(default=False)
    user_skipped_mapping_review = models.BooleanField(default=False)
    export_format = models.CharField(max_length=20, choices=[('csv', 'CSV'), ('parquet', 'Parquet')], 
                                     null=True, blank=True)
    
    # Download tracking
    downloaded_at = models.DateTimeField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['domain']),
        ]
    
    def __str__(self):
        return f"{self.domain}/{self.dataset_name} - {self.job_id}"
    
    def mark_processing_started(self):
        """Mark when processing started"""
        self.status = 'processing'
        self.processing_started_at = timezone.now()
        self.save(update_fields=['status', 'processing_started_at', 'updated_at'])
    
    def mark_processing_completed(self):
        """Mark when processing completed"""
        self.processing_completed_at = timezone.now()
        if self.processing_started_at:
            duration = (self.processing_completed_at - self.processing_started_at).total_seconds()
            self.processing_duration_seconds = int(duration)
        if self.status != 'failed':
            self.status = 'completed'
        self.save(update_fields=['status', 'processing_completed_at', 'processing_duration_seconds', 'updated_at'])
    
    def mark_failed(self, error_message):
        """Mark job as failed with error message"""
        self.status = 'failed'
        self.error_message = error_message
        self.mark_processing_completed()
    
    def get_result(self):
        """Get associated job result with pipeline outputs"""
        try:
            return self.result
        except JobResult.DoesNotExist:
            return None
    
    def get_summary_for_display(self):
        """Return summary dict for template display"""
        return {
            'job_id': self.job_id,
            'original_filename': self.original_filename,
            'domain': self.domain,
            'dataset_name': self.dataset_name,
            'status': self.get_status_display(),
            'rows_original': self.rows_original,
            'rows_processed': self.rows_processed,
            'columns_count': self.columns_count,
            'columns_mapped': self.columns_mapped,
            'ai_confidence': round(self.ai_confidence, 2),
            'completeness': round(self.completeness, 2),
            'mapping_score': round(self.mapping_score, 2),
            'processing_duration': self.processing_duration_seconds,
            'created_at': self.created_at.isoformat(),
        }


class JobResult(models.Model):
    """
    Caches pipeline results for a standardisation job
    Stores full pipeline output including schema, mappings, and validation results
    """
    job = models.OneToOneField(StandardisationJob, on_delete=models.CASCADE, related_name='result')
    
    # Pipeline results (JSON)
    schema_generated = models.JSONField(default=dict)  # Generated schema from Gemini
    column_mappings = models.JSONField(default=dict)   # Column name mappings
    data_quality_report = models.JSONField(default=dict)  # Quality report
    
    # Validation results
    validation_errors = models.JSONField(default=list)  # List of validation errors
    outliers_detected = models.JSONField(default=dict)  # Outlier info by column
    
    # Normalization results
    normalization_stats = models.JSONField(default=dict)  # Z-score, log transform, encoding stats
    normalization_summary = models.JSONField(default=list)  # Human-readable summary
    
    # Registry information
    registry_key = models.CharField(max_length=255, db_index=True)  # domain_dataset_name key
    used_cached_schema = models.BooleanField(default=False)
    
    # Processed data (metadata only, not the actual data)
    processed_data_path = models.CharField(max_length=500, null=True, blank=True)
    exported_csv_path = models.CharField(max_length=500, null=True, blank=True)
    exported_parquet_path = models.CharField(max_length=500, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['registry_key']),
        ]
    
    def __str__(self):
        return f"Result for {self.job.job_id}"
    
    def get_validation_error_count(self):
        """Get total count of validation errors"""
        return len(self.validation_errors) if self.validation_errors else 0
    
    def get_columns_with_issues(self):
        """Get list of columns that have quality issues"""
        columns_with_issues = set()
        
        for error in self.validation_errors:
            if 'column' in error:
                columns_with_issues.add(error['column'])
        
        for column, outlier_info in self.outliers_detected.items():
            if outlier_info.get('outlier_count', 0) > 0:
                columns_with_issues.add(column)
        
        return sorted(list(columns_with_issues))
    
    @property
    def schema_generated_json(self):
        """Return schema as formatted JSON string for display"""
        return json.dumps(self.schema_generated, indent=2)


class SchemaMappingEdit(models.Model):
    """
    Tracks user edits to schema column mappings
    Allows reverting to original and applying edits to processing
    """
    job = models.ForeignKey(StandardisationJob, on_delete=models.CASCADE, related_name='mapping_edits')
    
    # Column mapping edit details
    original_column_name = models.CharField(max_length=255)
    edited_column_name = models.CharField(max_length=255)
    
    # Edit metadata
    edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    edited_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)
    
    # Status
    applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['job', 'original_column_name']
        ordering = ['-edited_at']
    
    def __str__(self):
        return f"{self.original_column_name} → {self.edited_column_name}"
    
    def mark_applied(self):
        """Mark edit as applied"""
        self.applied = True
        self.applied_at = timezone.now()
        self.save(update_fields=['applied', 'applied_at'])


class DatasetVersion(models.Model):
    """
    Tracks different versions of standardised datasets
    Allows rollback and version comparison
    """
    job = models.ForeignKey(StandardisationJob, on_delete=models.CASCADE, related_name='versions')
    
    # Version tracking
    version_number = models.IntegerField()
    version_name = models.CharField(max_length=255, blank=True)
    
    # Data storage
    csv_path = models.CharField(max_length=500, null=True, blank=True)
    parquet_path = models.CharField(max_length=500, null=True, blank=True)
    
    # Schema snapshot
    schema_snapshot = models.JSONField()  # Snapshot of schema at this version
    
    # Versioning metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    change_description = models.TextField(blank=True)
    
    # Statistics
    row_count = models.IntegerField(default=0)
    column_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['job', 'version_number']
        ordering = ['-version_number']
    
    def __str__(self):
        return f"{self.job.dataset_name} v{self.version_number}"


class ProcessingLog(models.Model):
    """
    Detailed log of pipeline processing steps for debugging
    """
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
    ]
    
    job = models.ForeignKey(StandardisationJob, on_delete=models.CASCADE, related_name='logs')
    
    # Log content
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='INFO')
    step = models.CharField(max_length=100)  # e.g., 'schema_generation', 'data_cleaning'
    message = models.TextField()
    details = models.JSONField(default=dict)
    
    # Logging metadata
    created_at = models.DateTimeField(auto_now_add=True)
    duration_ms = models.IntegerField(null=True, blank=True)  # How long this step took
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['job', '-created_at']),
            models.Index(fields=['level']),
        ]
    
    def __str__(self):
        return f"[{self.level}] {self.step} - {self.job.job_id}"
