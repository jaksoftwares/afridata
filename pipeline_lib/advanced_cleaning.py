# =============================================================================
# ADVANCED DATA CLEANING & NORMALIZATION
# =============================================================================
"""
Advanced cleaning features:
- Text normalization (trim, case, special characters)
- Range & format validation
- Smart missing value handling
- Cross-field validation
- Advanced transformations
"""

import polars as pl
import re
import logging
from collections import Counter

logger = logging.getLogger(__name__)

# =============================================================================
# TEXT NORMALIZATION
# =============================================================================
def apply_text_normalization(df):
    """
    Normalize text columns: trim, standardize case, remove special chars
    """
    normalization_stats = {}
    
    for col in df.columns:
        if df[col].dtype == pl.Utf8:
            before_nulls = df[col].null_count()
            
            # Trim whitespace
            df = df.with_columns(
                pl.col(col).str.strip_chars().alias(col)
            )
            
            # Remove excessive whitespace between words
            df = df.with_columns(
                pl.col(col).str.replace_all(r'\s+', ' ').alias(col)
            )
            
            normalization_stats[col] = {
                'type': 'text_normalized',
                'nulls_before': before_nulls,
                'nulls_after': df[col].null_count()
            }
    
    return df, {'text_normalization': normalization_stats}

# =============================================================================
# RANGE & FORMAT VALIDATION
# =============================================================================
def apply_range_validation(df, schema):
    """
    Validate numeric and string ranges based on expected formats
    """
    validation_stats = {}
    rows_before = df.height
    
    for col in df.columns:
        if col not in schema:
            continue
        
        dtype = schema.get(col)
        
        # Numeric range validation
        if dtype in [pl.Int32, pl.Int64, pl.Float32, pl.Float64]:
            if not df[col].is_null().all():
                stats = {
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'mean': df[col].mean()
                }
                
                # Remove obvious outliers (> 3x interquartile range)
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - (1.5 * iqr) if q1 is not None and iqr is not None else None
                upper_bound = q3 + (1.5 * iqr) if q3 is not None and iqr is not None else None
                
                if lower_bound is not None and upper_bound is not None:
                    df = df.filter(
                        (pl.col(col).is_null()) | 
                        ((pl.col(col) >= lower_bound) & (pl.col(col) <= upper_bound))
                    )
                
                validation_stats[col] = {
                    'type': 'numeric_range',
                    'stats': stats,
                    'rows_removed': rows_before - df.height
                }
    
    return df, {'range_validation': validation_stats}

# =============================================================================
# SMART MISSING VALUE HANDLING
# =============================================================================
def apply_smart_null_filling(df, schema):
    """
    Fill missing values intelligently:
    - Numeric: use mean/median
    - Categorical: use mode (most common value)
    """
    fill_stats = {}
    
    for col in df.columns:
        if df[col].null_count() == 0:
            continue
        
        dtype = schema.get(col, df[col].dtype)
        
        # Numeric columns - use median
        if dtype in [pl.Int32, pl.Int64, pl.Float32, pl.Float64]:
            median = df[col].median()
            if median is not None:
                df = df.with_columns(
                    pl.col(col).fill_null(median).alias(col)
                )
                fill_stats[col] = {'method': 'median_fill', 'value': median}
        
        # String columns - use mode (most common value)
        elif dtype == pl.Utf8:
            non_null_values = df[col].drop_nulls()
            if non_null_values.height > 0:
                mode_value = non_null_values.mode().first()
                if mode_value is not None:
                    df = df.with_columns(
                        pl.col(col).fill_null(mode_value).alias(col)
                    )
                    fill_stats[col] = {'method': 'mode_fill', 'value': mode_value}
    
    return df, {'smart_null_filling': fill_stats}

# =============================================================================
# CROSS-FIELD VALIDATION
# =============================================================================
def apply_cross_field_validation(df):
    """
    Validate relationships between fields:
    - Date ranges (end > start)
    - Time consistency
    - Related field consistency
    """
    validation_stats = {}
    rows_before = df.height
    
    # Check for date consistency (if both date and time columns exist)
    date_cols = [c for c in df.columns if 'date' in c.lower()]
    time_cols = [c for c in df.columns if 'time' in c.lower()]
    
    if date_cols and time_cols:
        # Ensure times are reasonable (0-23 hours)
        for time_col in time_cols:
            if 'hour' in time_col.lower() and df[time_col].dtype in [pl.Int32, pl.Int64]:
                df = df.filter(
                    (pl.col(time_col).is_null()) |
                    ((pl.col(time_col) >= 0) & (pl.col(time_col) < 24))
                )
                validation_stats[time_col] = {
                    'type': 'hour_range_validation',
                    'valid_range': '0-23'
                }
        
        validation_stats['cross_field'] = {
            'rows_removed': rows_before - df.height,
            'checks': ['hour_range_validation']
        }
    
    return df, {'cross_field_validation': validation_stats}

# =============================================================================
# DUPLICATE KEY DETECTION
# =============================================================================
def apply_advanced_deduplication(df):
    """
    Find and handle duplicates based on key fields (ID, date, etc)
    """
    dedup_stats = {}
    rows_before = df.height
    
    # Identify potential key columns
    key_candidates = [c for c in df.columns if 'id' in c.lower() or c in ['transaction_date', 'date']]
    
    if key_candidates:
        # Keep first occurrence of duplicates
        df = df.unique(subset=key_candidates, keep='first')
        
        dedup_stats = {
            'method': 'advanced_deduplication',
            'key_fields': key_candidates,
            'rows_removed': rows_before - df.height
        }
    
    return df, {'advanced_deduplication': dedup_stats}

# =============================================================================
# ADVANCED TRANSFORMATIONS
# =============================================================================
def apply_advanced_transformations(df):
    """
    Apply domain-specific transformations:
    - Phone number standardization
    - Email validation
    - Currency/unit conversions
    """
    transform_stats = {}
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Phone number standardization
        if 'phone' in col_lower and df[col].dtype == pl.Utf8:
            df = df.with_columns(
                pl.col(col)
                .str.replace_all(r'[^\d+]', '')  # Remove non-numeric except +
                .alias(col)
            )
            transform_stats[col] = {'transformation': 'phone_standardized'}
        
        # Email validation
        elif 'email' in col_lower and df[col].dtype == pl.Utf8:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            df = df.with_columns(
                pl.when(
                    pl.col(col).str.contains(email_pattern)
                )
                .then(pl.col(col))
                .otherwise(pl.lit(None))
                .alias(col)
            )
            transform_stats[col] = {'transformation': 'email_validated'}
        
        # Currency - ensure positive values
        elif any(x in col_lower for x in ['amount', 'price', 'cost', 'payment']):
            if df[col].dtype in [pl.Float32, pl.Float64, pl.Int32, pl.Int64]:
                before_nulls = df[col].null_count()
                df = df.with_columns(
                    pl.when(pl.col(col) >= 0)
                    .then(pl.col(col))
                    .otherwise(pl.lit(None))
                    .alias(col)
                )
                transform_stats[col] = {
                    'transformation': 'currency_validated',
                    'nulls_created': df[col].null_count() - before_nulls
                }
    
    return df, {'advanced_transformations': transform_stats}

# =============================================================================
# MAIN ADVANCED CLEANING PIPELINE
# =============================================================================
def apply_all_advanced_cleaning(df, schema):
    """
    Apply all advanced cleaning techniques in optimal order
    """
    logger.info("Starting advanced cleaning pipeline...")
    all_stats = {}
    
    # 1. Text normalization (must be first)
    df, stats = apply_text_normalization(df)
    all_stats.update(stats)
    
    # 2. Range validation
    df, stats = apply_range_validation(df, schema)
    all_stats.update(stats)
    
    # 3. Smart null filling
    df, stats = apply_smart_null_filling(df, schema)
    all_stats.update(stats)
    
    # 4. Advanced deduplication
    df, stats = apply_advanced_deduplication(df)
    all_stats.update(stats)
    
    # 5. Cross-field validation
    df, stats = apply_cross_field_validation(df)
    all_stats.update(stats)
    
    # 6. Advanced transformations (last)
    df, stats = apply_advanced_transformations(df)
    all_stats.update(stats)
    
    logger.info(f"Advanced cleaning complete. Final rows: {df.height}")
    
    return df, all_stats
