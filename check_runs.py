import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "afridata.settings")
django.setup()

from metadata.models import PipelineRun
from dataset.models import Dataset

print("=== RECENT PIPELINE RUNS ===")
for run in PipelineRun.objects.order_by('-created_at')[:5]:
    print(f"Run ID: {run.id} | Status: {run.status} | Dataset: {run.dataset.title if run.dataset else 'None'} | Error: {run.error_message}")

print("\n=== RECENT DATASETS ===")
for ds in Dataset.objects.order_by('-created_at')[:5]:
    print(f"Dataset ID: {ds.id} | Title: {ds.title}")
    print(f"  - Author: {ds.original_author}")
    print(f"  - Source: {ds.data_source}")
    print(f"  - Date: {ds.collection_date}")
    print(f"  - Language: {ds.language}")
    print(f"  - License: {ds.dataset_license}")
    print(f"  - Frequency: {ds.update_frequency}")
    print(f"  - Geo: {ds.geographic_coverage}")
    print(f"  - Temporal: {ds.temporal_coverage}")
    print(f"  - Notes: {ds.usage_notes}")
