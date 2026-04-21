# =============================================================================
# pipeline_cleaning.py — DATA TRANSFORMATION & CLEANING
# =============================================================================

import polars as pl
import logging
from pipeline_lib.config import CRITICAL_COLUMNS

logger = logging.getLogger(__name__)

# =============================================================================
# BRONZE LAYER — DATA LOADING
# =============================================================================
def load_dataset(file_path: str):
    """Load CSV file and add source file tracking"""
    import os
    filename = os.path.basename(file_path)
    df = pl.read_csv(file_path, infer_schema_length=0)
    df = df.with_columns(pl.lit(filename).alias('_source_file'))
    return df, filename

# =============================================================================
# SILVER LAYER — SCHEMA TRANSFORMATION
# =============================================================================
def apply_silver_layer(df, mapping, schema, transforms):
    """Apply column renaming and schema transformation"""
    rename_map = {
        k: v for k, v in mapping.items() if v != "__DROP__"
    }

    df = df.rename(rename_map)

    exprs = []
    for col, dtype in schema.items():
        if col in df.columns:
            exprs.append(pl.col(col))
        else:
            exprs.append(pl.lit(None).alias(col))

    return df.select(exprs)

# =============================================================================
# VALUE STANDARDIZATION
# =============================================================================
def apply_value_standardisation(df):
    """Trim whitespace from string columns"""
    df = df.clone()

    for c in df.columns:
        if df[c].dtype == pl.Utf8:
            df = df.with_columns(pl.col(c).str.strip_chars().alias(c))

    return df

# =============================================================================
# NULL VALUE HANDLING
# =============================================================================
def apply_null_handling(df, schema):
    """Handle null values - remove critical rows or fill with defaults"""
    before_height = df.height
    null_stats = {}
    
    # Calculate null percentages before
    for col in df.columns:
        null_count = df[col].null_count()
        null_pct = round(null_count / df.height * 100, 1) if df.height > 0 else 0
        null_stats[col] = {
            'before_null_count': null_count,
            'before_null_pct': null_pct
        }
    
    # Remove rows where critical columns are null
    for col in CRITICAL_COLUMNS:
        if col in df.columns:
            df = df.filter(pl.col(col).is_not_null())
    
    # For non-critical columns, fill nulls with defaults based on dtype
    for col in df.columns:
        if df[col].null_count() > 0:
            dtype = schema.get(col, df[col].dtype)
            
            if dtype in [pl.Int32, pl.Int64]:
                df = df.with_columns(pl.col(col).fill_null(0).alias(col))
            elif dtype in [pl.Float32, pl.Float64]:
                df = df.with_columns(pl.col(col).fill_null(0.0).alias(col))
            elif dtype == pl.Utf8:
                df = df.with_columns(pl.col(col).fill_null("Unknown").alias(col))
            elif dtype in [pl.Date, pl.Datetime]:
                df = df.with_columns(pl.col(col).fill_null(pl.lit(None)).alias(col))
    
    # Calculate null percentages after
    for col in df.columns:
        null_count = df[col].null_count()
        null_pct = round(null_count / df.height * 100, 1) if df.height > 0 else 0
        null_stats[col]['after_null_count'] = null_count
        null_stats[col]['after_null_pct'] = null_pct
    
    rows_removed = before_height - df.height
    
    return df, {
        'rows_removed': rows_removed,
        'null_stats': null_stats
    }

# =============================================================================
# DEDUPLICATION
# =============================================================================
def apply_deduplication(df):
    """Remove duplicate rows"""
    before = df.height
    df = df.unique()
    return df, {"removed": before - df.height}

# =============================================================================
# GOLD LAYER — QUALITY METRICS
# =============================================================================
def apply_gold_layer(df):
    """Calculate final dataset metrics"""
    return {
        "row_count": df.height,
        "column_count": len(df.columns)
    }

def generate_quality_report(df, schema):
    """Generate completeness report for each column"""
    report = []
    for col in schema.keys():
        if col not in df.columns:
            continue
        nulls = df[col].null_count()
        total = df.height
        report.append({
            "column": col,
            "completeness": round((total - nulls) / total * 100, 1)
        })
    return report
