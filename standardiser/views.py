"""
Django Views for Data Standardisation Workflow
Handles internal dataset processing, results display, and downloads
"""
import os
import uuid
import tempfile
import json
import pandas as pd
import polars as pl
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.files.storage import default_storage
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib.auth import get_user_model
from datetime import datetime

def get_test_user():
    """
    Get or create a test user for development without authentication
    """
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    return user

# Import pipeline modules from pipeline_lib package
from pipeline_lib.pipeline import process_dataset
from pipeline_lib.export import export_to_csv, export_to_parquet

# Import Django models and forms
from .models import StandardisationJob, JobResult, SchemaMappingEdit
from .forms import SchemaMappingForm, ExportFormatForm

# Import Dataset model from dataset app
from dataset.models import Dataset

logger = logging.getLogger(__name__)


def index(request):
    """
    Home page - Redirect to dataset library
    """
    return redirect('dataset_list')


@require_http_methods(["GET"])
def initiate_standardization(request, dataset_slug):
    """
    Initiate standardization for an existing dataset in the system.
    This replaces the upload step for datasets already in our library.
    """
    user = request.user if request.user.is_authenticated else get_test_user()
    dataset = get_object_or_404(Dataset, slug=dataset_slug)

    # Check if user has permission to download/standardize (tokens check)
    if not dataset.can_user_download(user):
        return redirect('dataset_detail', slug=dataset_slug)

    try:
        # Determine domain from topics (take first one)
        topics = dataset.get_topics_list()
        domain = topics[0] if topics else 'other'
        dataset_name = dataset.title
        
        # Create StandardisationJob record
        job_id = str(uuid.uuid4())
        file_ext = dataset.file.name.split('.')[-1].lower()
        
        job = StandardisationJob(
            job_id=job_id,
            user=user,
            original_filename=os.path.basename(dataset.file.name),
            file_format=file_ext,
            file_size=dataset.file.size,
            domain=domain,
            dataset_name=dataset_name,
            status='pending'
        )
        job.save()
        
        # Mark as processing started
        job.mark_processing_started()
        
        try:
            # Run pipeline processing using the existing file path
            result = process_dataset(
                file_path=dataset.file.path,
                domain=domain,
                dataset_name=dataset_name
            )
            
            # Extract metrics from result
            job.rows_original = result.get('report', {}).get('summary', {}).get('original_rows', 0)
            job.rows_processed = result.get('rows_processed', 0)
            raw_cols = result.get('raw_columns', [])
            job.columns_count = len(raw_cols)
            
            # Count mapped columns
            schema = result.get('schema', {})
            mapping_instructions = schema.get('mapping_instructions', {})
            mapped_cols = sum(1 for v in mapping_instructions.values() if v != '__DROP__')
            job.columns_mapped = mapped_cols
            
            # Calculate score
            total_cols = len(mapping_instructions) if mapping_instructions else 1
            mapping_percentage = (mapped_cols / total_cols * 100) if total_cols > 0 else 0
            pipeline_score = result.get('mapping_score', 0)
            job.mapping_score = (mapping_percentage * 0.6) + (pipeline_score * 0.4)
            
            job.ai_confidence = result.get('ai_confidence', 0)
            job.completeness = result.get('completeness', 0)
            job.save()
            
            # Save processed data to disk
            processed_df = result.get('data')
            processed_data_path = ''
            if processed_df is not None:
                temp_dir = os.path.join(settings.MEDIA_ROOT, 'processed')
                os.makedirs(temp_dir, exist_ok=True)
                processed_data_path = os.path.join(temp_dir, f"{job.job_id}_processed.parquet")
                processed_df.write_parquet(processed_data_path)
            
            # Store job result
            job_result = JobResult(
                job=job,
                schema_generated=result.get('schema', {}),
                column_mappings=result.get('schema', {}).get('mapping_instructions', {}),
                data_quality_report=result.get('report', {}),
                validation_errors=result.get('cleaning_results', {}).get('validation', {}).get('validation_errors', {}),
                outliers_detected=result.get('cleaning_results', {}).get('outliers', {}).get('outlier_stats', {}),
                normalization_stats=result.get('normalization_stats', {}),
                normalization_summary=result.get('normalization_summary', []),
                registry_key=result.get('registry_key') or '',
                processed_data_path=processed_data_path,
            )
            job_result.save()
            
            # Mark job as ready for review
            job.status = 'review'
            job.mark_processing_completed()
            
            # Redirect to results page
            return redirect('standardiser:standardisation_ready', job_id=job_id)
            
        except Exception as e:
            job.mark_failed(str(e))
            return render(request, 'standardiser/error.html', {
                'error': f'Standardization failed: {str(e)}'
            }, status=500)
            
    except Exception as e:
        return render(request, 'standardiser/error.html', {
            'error': f'Initialization failed: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def standardisation_ready(request, job_id):
    """
    View showing standardisation results and metrics
    Allows user to review mappings or proceed to download
    """
    # Get test user for development
    user = request.user if request.user.is_authenticated else get_test_user()
    
    job = get_object_or_404(StandardisationJob, job_id=job_id, user=user)
    
    if job.status not in ['review', 'completed']:
        return render(request, 'standardiser/error.html', {
            'error': f'Job is in {job.get_status_display()} status, cannot review yet'
        }, status=400)
    
    result = job.get_result()
    if not result:
        return render(request, 'standardiser/error.html', {
            'error': 'Job result not found'
        }, status=404)
    
    summary = job.get_summary_for_display()
    
    return render(request, 'standardiser/standardisation_ready.html', {
        'job': job,
        'summary': summary,
        'result': result,
        'quality_report': result.data_quality_report,
        'validation_errors': result.validation_errors,
        'columns_with_issues': result.get_columns_with_issues(),
    })


@require_http_methods(["GET", "POST"])
def review_mappings(request, job_id):
    """
    View for reviewing and editing column name mappings
    GET: Display mapping form
    POST: Store edits and trigger re-processing
    """
    # Get test user for development
    user = request.user if request.user.is_authenticated else get_test_user()
    
    job = get_object_or_404(StandardisationJob, job_id=job_id, user=user)
    result = get_object_or_404(JobResult, job=job)
    
    column_mappings = result.column_mappings
    
    if request.method == 'GET':
        form = SchemaMappingForm(column_mappings)
        return render(request, 'standardiser/review_mappings.html', {
            'job': job,
            'result': result,
            'form': form,
            'original_mappings': column_mappings,
        })
    
    # POST request - process edits
    form = SchemaMappingForm(column_mappings, request.POST)
    
    if not form.is_valid():
        return render(request, 'standardiser/review_mappings.html', {
            'job': job,
            'result': result,
            'form': form,
            'error': 'Please fix the errors below'
        }, status=400)
    
    try:
        # Get changed mappings for history tracking
        edited_mappings = form.get_edited_mappings()
        # Get full mappings for the updated job result
        full_mappings = form.get_full_mappings()
        
        # Store edits in database for audit trail
        with transaction.atomic():
            for original_col, new_col in edited_mappings.items():
                edit, _ = SchemaMappingEdit.objects.update_or_create(
                    job=job,
                    original_column_name=original_col,
                    defaults={
                        'edited_column_name': new_col,
                        'edited_by': user,
                        'reason': request.POST.get('edit_reason', ''),
                    }
                )
            
            # Update the JobResult with the COMPLETE set of mappings
            result.column_mappings = full_mappings
            # Also update the schema's mapping_instructions
            if result.schema_generated and 'mapping_instructions' in result.schema_generated:
                result.schema_generated['mapping_instructions'] = full_mappings
            result.save()
        
        # Mark job as reviewed
        job.user_reviewed = True
        job.save()
        
        # TODO: Schedule async task to re-run silver layer with edited mappings
        
        return redirect('standardiser:standardisation_ready', job_id=job_id)
    
    except Exception as e:
        return render(request, 'standardiser/review_mappings.html', {
            'job': job,
            'result': result,
            'form': form,
            'error': f'Failed to save edits: {str(e)}'
        }, status=500)


@require_http_methods(["GET", "POST"])
def download_file(request, job_id):
    """
    Export standardized data with mappings applied
    GET parameters: ?format=csv|parquet|excel|json
    """
    user = request.user if request.user.is_authenticated else get_test_user()
    
    job = get_object_or_404(StandardisationJob, job_id=job_id, user=user)
    result = get_object_or_404(JobResult, job=job)
    
    export_format = request.GET.get('format', 'csv').lower()
    
    if export_format not in ['csv', 'parquet', 'excel', 'json']:
        export_format = 'csv'
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        base_filename = f"standardised_{job.domain}_{job.dataset_name}_{timestamp}"
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Load processed data if available
        processed_data = None
        if result.processed_data_path and os.path.exists(result.processed_data_path):
            try:
                processed_data = pl.read_parquet(result.processed_data_path)
                
                # Sort the cleaned data for consistent output
                # Try to sort by date-related columns first, then by ID-like columns
                sort_columns = []
                available_cols = processed_data.columns
                
                # Preferred sort order
                preferred_sort = ['transaction_date', 'transaction_time', 'transaction_hour', 'date', 'time', 'created_at', 'id']
                for col in preferred_sort:
                    if col in available_cols:
                        sort_columns.append(col)
                        break
                
                # If no date column found, sort by first two columns
                if not sort_columns and len(available_cols) > 0:
                    sort_columns = [available_cols[0]]
                    if len(available_cols) > 1:
                        sort_columns.append(available_cols[1])
                
                if sort_columns:
                    processed_data = processed_data.sort(sort_columns)
                    logger.info(f"Sorted data by columns: {sort_columns}")
                    
            except Exception as e:
                logger.warning(f"Could not load processed data: {e}")
        
        # Get mappings (reverse them: standard_column -> original_column for renaming)
        mappings = result.column_mappings
        
        if export_format == 'json':
            # Export schema, mappings, and sample data
            output_path = os.path.join(temp_dir, f"{base_filename}.json")
            export_data = {
                'job_id': str(job.job_id),
                'domain': job.domain,
                'dataset_name': job.dataset_name,
                'schema': result.schema_generated,
                'mappings': mappings,
                'quality_report': result.data_quality_report,
            }
            
            # Add sample data if available
            if processed_data is not None:
                export_data['sample_data'] = processed_data.head(10).to_dicts()
                export_data['total_rows'] = len(processed_data)
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            content_type = 'application/json'
        
        elif export_format == 'excel':
            output_path = os.path.join(temp_dir, f"{base_filename}.xlsx")
            with pd.ExcelWriter(output_path) as writer:
                # Sheet 1: Standardized Data
                if processed_data is not None:
                    df = processed_data.to_pandas()
                    df.to_excel(writer, sheet_name='Data', index=False)
                
                # Sheet 2: Column Mappings
                mappings_df = pd.DataFrame([
                    {'Original Column': k, 'Standard Column': v}
                    for k, v in mappings.items()
                ])
                mappings_df.to_excel(writer, sheet_name='Mappings', index=False)
                
                # Sheet 3: Schema
                schema = result.schema_generated
                if schema.get('official_standard'):
                    schema_df = pd.DataFrame([
                        {'Column': k, 'Type': v}
                        for k, v in schema['official_standard'].items()
                    ])
                    schema_df.to_excel(writer, sheet_name='Schema', index=False)
            
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        elif export_format == 'parquet':
            output_path = os.path.join(temp_dir, f"{base_filename}.parquet")
            if processed_data is not None:
                processed_data.write_parquet(output_path)
            else:
                # Fallback: export mappings if no data available
                mappings_df = pd.DataFrame([
                    {'original_column': k, 'standard_column': v}
                    for k, v in mappings.items()
                ])
                pl.from_pandas(mappings_df).write_parquet(output_path)
            content_type = 'application/octet-stream'
        
        else:  # csv
            output_path = os.path.join(temp_dir, f"{base_filename}.csv")
            if processed_data is not None:
                processed_data.write_csv(output_path)
            else:
                # Fallback: export mappings if no data available
                mappings_df = pd.DataFrame([
                    {'original_column': k, 'standard_column': v}
                    for k, v in mappings.items()
                ])
                mappings_df.to_csv(output_path, index=False)
            content_type = 'text/csv'
        
        # Update download metadata
        job.export_format = export_format
        job.status = 'completed'
        job.downloaded_at = timezone.now()
        job.download_count += 1
        job.save()
        
        # Serve file
        return FileResponse(
            open(output_path, 'rb'),
            content_type=content_type,
            as_attachment=True,
            filename=f"{base_filename}.{export_format}"
        )
    
    except Exception as e:
        logger.error(f"Download error: {e}")
        return render(request, 'standardiser/error.html', {
            'error': f'Download failed: {str(e)}'
        }, status=500)
        return render(request, 'standardiser/download_choice.html', {
            'job': job,
            'form': form,
            'error': f'Download failed: {str(e)}'
        }, status=500)




@require_http_methods(["GET"])
def job_list(request):
    """
    View for displaying list of user's standardisation jobs
    """
    # Get test user for development
    user = request.user if request.user.is_authenticated else get_test_user()
    jobs = StandardisationJob.objects.filter(user=user).order_by('-created_at')
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    
    # Filter by domain if requested
    domain_filter = request.GET.get('domain')
    if domain_filter:
        jobs = jobs.filter(domain=domain_filter)
    
    return render(request, 'standardiser/job_list.html', {
        'jobs': jobs,
        'status_filter': status_filter,
        'domain_filter': domain_filter,
    })


@require_http_methods(["GET"])
def job_detail(request, job_id):
    """
    View for detailed job history and metrics
    """
    # Get test user for development
    user = request.user if request.user.is_authenticated else get_test_user()
    
    job = get_object_or_404(StandardisationJob, job_id=job_id, user=user)
    result = job.get_result()
    mapping_edits = job.mapping_edits.all()
    versions = job.versions.all()
    logs = job.logs.all()[:50]  # Latest 50 logs
    
    return render(request, 'standardiser/job_detail.html', {
        'job': job,
        'result': result,
        'mapping_edits': mapping_edits,
        'versions': versions,
        'logs': logs,
    })


@require_http_methods(["POST"])
def delete_job(request, job_id):
    """
    Delete a standardisation job
    """
    # Get test user for development
    user = request.user if request.user.is_authenticated else get_test_user()
    
    job = get_object_or_404(StandardisationJob, job_id=job_id, user=user)
    job.delete()
    return redirect('standardiser:job_list')


@require_http_methods(["GET"])
def get_supported_formats_api(request):
    """
    API endpoint providing list of supported file formats
    """
    formats = get_supported_formats()
    return JsonResponse({
        'success': True,
        'formats': formats,
    })


@require_http_methods(["GET"])
def job_status_api(request, job_id):
    """
    API endpoint for checking job processing status
    Returns JSON with status and completion info
    """
    # Get test user for development
    user = request.user if request.user.is_authenticated else get_test_user()
    
    try:
        job = StandardisationJob.objects.get(job_id=job_id, user=user)
        
        return JsonResponse({
            'success': True,
            'job_id': job_id,
            'status': job.status,
            'completed': job.status in ['review', 'completed'],
            'failed': job.status == 'failed',
            'processing': job.status == 'processing',
            'domain': job.domain,
            'dataset_name': job.dataset_name,
            'created_at': job.created_at.isoformat() if job.created_at else None,
        })
    except StandardisationJob.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Job not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error checking job status: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

