# =============================================================================
# pipeline.py — MAIN ENTRY POINT & ORCHESTRATION
# =============================================================================
# AFRIDATA Schema Fingerprint Standardisation Engine
# Version 4.0 — Modular Architecture
# =============================================================================

import os
import logging

# Import all pipeline modules
from pipeline_config import get_registry_path
from pipeline_registry import load_registry, store_schema, find_existing_schema, generate_registry_key
from pipeline_schema import fingerprint_columns, jaccard_similarity, generate_schema_with_ai
from pipeline_loader import load_file, preview_file, get_supported_formats, detect_format
from pipeline_cleaning import (
    apply_silver_layer,
    apply_value_standardisation,
    apply_null_handling,
    apply_deduplication,
    apply_gold_layer,
    generate_quality_report
)
from pipeline_validation import (
    apply_outlier_detection,
    apply_data_type_validation,
    apply_pattern_validation,
    apply_referential_integrity
)
from pipeline_reporting import generate_data_quality_report, print_data_quality_report

logger = logging.getLogger(__name__)

# =============================================================================
# MAPPING SCORE CALCULATION
# =============================================================================
def calculate_mapping_score(schema, cleaning_results, total_columns):
    """
    Calculate mapping quality score (0-100) based on validation results.
    Uses Option 2: Calculate from validation results.
    
    Formula: 100 - (errors/total_columns * 100)
    """
    validation_errors = cleaning_results.get('validation', {}).get('invalid_rows', 0)
    pattern_issues = cleaning_results.get('patterns', {}).get('total_pattern_issues', 0)
    integrity_issues = cleaning_results.get('integrity', {}).get('total_integrity_issues', 0)
    
    total_issues = validation_errors + pattern_issues + integrity_issues
    
    if total_columns == 0:
        return 100.0
    
    mapping_score = 100.0 - (total_issues / total_columns * 100)
    return max(0.0, min(100.0, mapping_score))  # Clamp between 0-100

# =============================================================================
# PIPELINE ENTRY POINT
# =============================================================================
def process_dataset(file_path, domain=None, dataset_name=None, **loader_kwargs):
    """
    Main pipeline function that orchestrates the entire data processing workflow.
    Supports multiple file formats (CSV, Excel, JSON, Parquet, XML, YAML, etc.)
    
    Process:
    1. Load dataset from any supported format (Bronze layer)
    2. Check registry by domain + raw columns
    3. Match or generate schema
    4. Apply schema transformations (Silver layer)
    5. Clean data (null handling, deduplication)
    6. Validate data (outliers, types, patterns, integrity)
    7. Generate quality metrics (Gold layer)
    8. Calculate mapping score
    9. Create comprehensive report
    
    Args:
        file_path (str): Path to the dataset file (CSV, Excel, JSON, Parquet, XML, YAML)
        domain (str, optional): Domain name for schema registry (e.g., "agriculture")
        dataset_name (str, optional): Dataset name for key generation (e.g., "maize")
        **loader_kwargs: Format-specific options:
            - delimiter (str): For text files (default: tab)
            - root_element (str): For XML files
            - sheet (int/str): For Excel files (sheet index or name)
    
    Returns:
        dict: Contains processed data, schema, cleaning results, report, and metrics
    
    Raises:
        FileNotFoundError: If file not found
        ValueError: If file format not supported
    """
    
    print(f"\n🚀 Starting data processing pipeline for: {os.path.basename(file_path)}")
    print(f"   Domain: {domain}, Dataset: {dataset_name}")
    print("="*80)
    
    # =========================================================================
    # STEP 1: BRONZE LAYER - LOAD DATASET (Multi-Format Support)
    # =========================================================================
    try:
        df_original, filename, format_name = load_file(file_path, **loader_kwargs)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load file: {e}")
        raise
    
    df = df_original.clone()
    raw_columns = df_original.columns
    
    print(f"📥 Loaded {format_name} file: {filename}")
    print(f"   Rows: {df.height:,} | Columns: {len(df.columns)}")
    print(f"   Raw columns: {list(raw_columns)}")

    # =========================================================================
    # STEP 2: SCHEMA MATCHING & GENERATION (Domain + Raw Column Based)
    # =========================================================================
    print("\n📋 Step 1: Schema Matching & Generation...")
    registry = load_registry()
    
    # FAST PATH: Check registry by domain + raw columns
    existing_schema, registry_key = find_existing_schema(domain, raw_columns, registry)
    
    if existing_schema:
        schema = existing_schema
        mapping = schema["mapping_instructions"]
        transforms = schema.get("transformation_needed", {})
        print(f"  ✅ Found cached schema in registry (key: {registry_key})")
        print(f"     Confidence: {schema.get('alignment_confidence', 'N/A')}")
        
    else:
        # NO MATCH: Generate new schema with AI
        print(f"  🤖 No matching schema found. Generating with AI...")
        schema = generate_schema_with_ai(df, filename, domain)
        mapping = schema["mapping_instructions"]
        transforms = schema.get("transformation_needed", {})
        print(f"  ✅ Schema generated (confidence: {schema.get('alignment_confidence', 0)})")

    # Store schema in registry with domain + dataset_name key
    if dataset_name:
        registry = store_schema(registry, schema, raw_columns, domain, dataset_name)
    else:
        logger.warning("dataset_name not provided - schema not stored in registry")

    # =========================================================================
    # STEP 3: SILVER LAYER - SCHEMA TRANSFORMATION
    # =========================================================================
    print("\n🔵 Step 2: Schema Transformation (Silver Layer)...")
    df = apply_silver_layer(df, mapping, schema["official_standard"], transforms)
    df = apply_value_standardisation(df)
    print(f"  ✅ Applied transformations")

    # =========================================================================
    # STEP 4: DATA CLEANING OPERATIONS
    # =========================================================================
    print("\n🧹 Step 3: Data Cleaning Operations...")
    
    # Null handling
    print("  → Handling null values...")
    df, null_results = apply_null_handling(df, schema["official_standard"])
    print(f"    ✓ {null_results['rows_removed']} rows removed (critical nulls)")
    
    # Deduplication
    print("  → Removing duplicates...")
    df, dedup_results = apply_deduplication(df)
    print(f"    ✓ {dedup_results['removed']} duplicate rows removed")

    # =========================================================================
    # STEP 5: DATA VALIDATION
    # =========================================================================
    print("\n✔️ Step 4: Data Validation...")
    
    # Outlier detection
    print("  → Detecting outliers...")
    outlier_results = apply_outlier_detection(df, schema["official_standard"])
    print(f"    ✓ {outlier_results['total_outliers']} outliers detected")
    
    # Data type validation
    print("  → Validating data types...")
    validation_results = apply_data_type_validation(df, schema["official_standard"])
    print(f"    ✓ {validation_results['invalid_rows']} validation issues found")
    
    # Pattern validation
    print("  → Validating patterns (ISO codes, formats)...")
    pattern_results = apply_pattern_validation(df)
    print(f"    ✓ {pattern_results['total_pattern_issues']} pattern issues found")
    
    # Integrity checks
    print("  → Checking referential integrity...")
    integrity_results = apply_referential_integrity(df)
    print(f"    ✓ {integrity_results['total_integrity_issues']} integrity issues found")

    # =========================================================================
    # STEP 6: GOLD LAYER - QUALITY METRICS
    # =========================================================================
    print("\n🏆 Step 5: Final Quality Metrics (Gold Layer)...")
    quality = generate_quality_report(df, schema["official_standard"])
    gold = apply_gold_layer(df)
    print(f"  ✅ {df.height:,} rows × {len(df.columns)} columns (final)")

    # =========================================================================
    # STEP 7: GENERATE COMPREHENSIVE REPORT
    # =========================================================================
    print("\n📊 Generating Data Quality Report...")
    cleaning_results = {
        'null_handling': null_results,
        'deduplication': dedup_results,
        'outliers': outlier_results,
        'validation': validation_results,
        'patterns': pattern_results,
        'integrity': integrity_results,
        'quality': quality
    }
    
    report = generate_data_quality_report(df_original, df, schema["official_standard"], cleaning_results)
    print_data_quality_report(report)

    # =========================================================================
    # STEP 8: CALCULATE MAPPING SCORE
    # =========================================================================
    mapping_score = calculate_mapping_score(schema, cleaning_results, len(schema["official_standard"]))
    print(f"\n📈 Mapping Quality Score: {mapping_score:.1f}%")

    # =========================================================================
    # RETURN RESULTS
    # =========================================================================
    return {
        "data": df,
        "schema": schema,
        "cleaning_results": cleaning_results,
        "quality": quality,
        "gold": gold,
        "report": report,
        "registry_key": registry_key,
        "domain": domain,
        "dataset_name": dataset_name,
        "raw_columns": list(raw_columns),
        "mapping_score": mapping_score,
        "ai_confidence": schema.get('alignment_confidence', 0),
        "completeness": report.get('data_quality', {}).get('avg_completeness', 0),
        "rows_processed": report['summary']['final_rows'],
        "columns_mapped": report['summary']['columns'],
        "file_format": format_name
    }

# =============================================================================
# DEBUGGING HELPER
# =============================================================================
if __name__ == "__main__":
    # Example usage
    print("Pipeline modules loaded successfully!")
    print("Available functions:")
    print("  - process_dataset(file_path, domain=None, dataset_name=None, **loader_kwargs)")
    print("  - calculate_mapping_score(schema, cleaning_results, total_columns)")
    print("  - preview_file(file_path, rows=5, **loader_kwargs)")
    print("  - get_supported_formats()")
    print("\nSupported File Formats:")
    from pipeline_loader import get_supported_formats
    for fmt in get_supported_formats():
        print(f"  - {fmt}")
    print("\nUsage Examples:")
    print("\n1. CSV file:")
    print("  result = process_dataset('data/coffee.csv', 'agriculture', 'coffee')")
    print("\n2. Excel file (specific sheet):")
    print("  result = process_dataset('data/data.xlsx', 'agriculture', 'maize', sheet=0)")
    print("\n3. JSON file:")
    print("  result = process_dataset('data/harvest.json', 'agriculture', 'wheat')")
    print("\n4. Parquet file:")
    print("  result = process_dataset('data/sales.parquet', 'commerce', 'goods')")
    print("\n5. Tab-separated text:")
    print("  result = process_dataset('data/data.txt', 'agriculture', 'corn', delimiter='\\t')")
    print("\n6. Preview before processing:")
    print("  preview = preview_file('data/unknown.xlsx')")
    print("  print(preview['shape'], preview['column_names'])")
    print("\nResult contains:")
    print("  - data: Cleaned Polars DataFrame")
    print("  - schema: Full schema dict with mappings")
    print("  - ai_confidence: AI alignment confidence (0-1)")
    print("  - completeness: Data completeness % (0-100)")
    print("  - mapping_score: Quality score of mappings (0-100)")
    print("  - rows_processed: Final row count")
    print("  - columns_mapped: Number of columns in schema")
    print("  - file_format: Detected file format")
    print("  - registry_key: Key where schema was stored (domain_dataset)")
    print("  - report: Comprehensive quality report")
