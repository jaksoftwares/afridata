import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "afridata.settings")
django.setup()

from metadata.models import PipelineRun, MetadataResult, ColumnProfile
from dataset.models import Dataset

print("=== DETAILED INSPECTION ===")
for run in PipelineRun.objects.order_by('-created_at')[:5]:
    print(f"Run ID: {run.id} | Status: {run.status}")
    print(f"  Dataset: {run.dataset.title if run.dataset else 'None'} (ID: {run.dataset_id})")
    
    # Check MetadataResult
    try:
        res = MetadataResult.objects.get(run=run)
        print(f"  MetadataResult exists: Yes")
        print(f"    Schema keys: {list(res.schema_dict.keys()) if res.schema_dict else 'Empty'}")
    except MetadataResult.DoesNotExist:
        print(f"  MetadataResult exists: No")
        
    # Check ColumnProfiles
    cols = ColumnProfile.objects.filter(run=run)
    print(f"  Column profiles count: {cols.count()}")
    for col in cols[:3]:
         print(f"    - {col.column_name}: dtype={col.dtype}, semantic={col.semantic_type}")
         
    # Check dataset fields
    ds = run.dataset
    if ds:
         print(f"  Dataset Fields:")
         for field in ["original_author", "data_source", "collection_date", "language", "dataset_license", "update_frequency", "geographic_coverage", "temporal_coverage", "usage_notes", "metadata_quality_score"]:
             print(f"    {field}: {getattr(ds, field)}")
    print("-" * 50)
