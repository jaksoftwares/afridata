# =============================================================================
# pipeline_validation.py — DATA VALIDATION & INTEGRITY CHECKS
# =============================================================================

import logging
import polars as pl
from pipeline_lib.config import ISO_COUNTRY_CODES, ISO_CURRENCY_CODES

logger = logging.getLogger(__name__)

# =============================================================================
# OUTLIER DETECTION
# =============================================================================
def apply_outlier_detection(df, schema):
    """Detect outliers using IQR method for numeric columns"""
    outlier_stats = {}
    
    for col in df.columns:
        dtype = schema.get(col, df[col].dtype)
        
        # Only check numeric columns
        if dtype in [pl.Int32, pl.Int64, pl.Float32, pl.Float64]:
            try:
                # Calculate Q1, Q3, IQR
                q1 = df[col].drop_nulls().quantile(0.25)
                q3 = df[col].drop_nulls().quantile(0.75)
                iqr = q3 - q1
                
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                # Find outliers
                outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
                outlier_count = outlier_mask.sum()
                
                if outlier_count > 0:
                    outlier_stats[col] = {
                        'outlier_count': int(outlier_count),
                        'outlier_pct': round(outlier_count / df.height * 100, 2),
                        'lower_bound': float(lower_bound),
                        'upper_bound': float(upper_bound)
                    }
                    
            except Exception as e:
                logger.warning(f"Could not calculate outliers for column {col}: {e}")
    
    return {
        'outlier_stats': outlier_stats,
        'total_outliers': sum(s['outlier_count'] for s in outlier_stats.values())
    }

# =============================================================================
# DATA TYPE VALIDATION
# =============================================================================
def apply_data_type_validation(df, schema):
    """Validate that column values conform to expected data types"""
    validation_errors = {}
    
    for col in df.columns:
        if col == '_source_file':
            continue
            
        expected_dtype = schema.get(col)
        actual_dtype = df[col].dtype
        
        # Check type mismatch
        if actual_dtype != expected_dtype:
            validation_errors[col] = {
                'expected': str(expected_dtype),
                'actual': str(actual_dtype),
                'issue': 'Type mismatch'
            }
        
        # Validate specific patterns for date columns
        if expected_dtype == pl.Date or 'date' in col.lower():
            try:
                invalid_dates = df.filter(
                    ~df[col].is_null() & 
                    ~df[col].str.contains(r'^\d{4}-\d{2}-\d{2}$')
                ).height if actual_dtype == pl.Utf8 else 0
                
                if invalid_dates > 0:
                    validation_errors[col] = {
                        'issue': f'Invalid date format (expected YYYY-MM-DD)',
                        'invalid_count': invalid_dates
                    }
            except:
                pass
    
    return {
        'validation_errors': validation_errors,
        'invalid_rows': len(validation_errors)
    }

# =============================================================================
# PATTERN VALIDATION (ISO CODES, FORMATS)
# =============================================================================
def apply_pattern_validation(df):
    """Validate common patterns: ISO codes, currencies, etc."""
    pattern_stats = {}
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Check country codes
        if 'country' in col_lower or 'code' in col_lower:
            try:
                unique_vals = df[col].drop_nulls().unique().to_list()
                invalid_codes = [v for v in unique_vals if v and v.upper() not in ISO_COUNTRY_CODES]
                
                if invalid_codes:
                    pattern_stats[col] = {
                        'type': 'country_code',
                        'invalid_count': len(invalid_codes),
                        'sample_invalid': invalid_codes[:5]
                    }
            except Exception as e:
                logger.warning(f"Error validating country codes in {col}: {e}")
        
        # Check currency codes
        if 'currency' in col_lower or 'curr' in col_lower:
            try:
                unique_vals = df[col].drop_nulls().unique().to_list()
                invalid_currencies = [v for v in unique_vals if v and v.upper() not in ISO_CURRENCY_CODES]
                
                if invalid_currencies:
                    pattern_stats[col] = {
                        'type': 'currency_code',
                        'invalid_count': len(invalid_currencies),
                        'sample_invalid': invalid_currencies[:5]
                    }
            except Exception as e:
                logger.warning(f"Error validating currencies in {col}: {e}")
    
    return {
        'pattern_issues': pattern_stats,
        'total_pattern_issues': len(pattern_stats)
    }

# =============================================================================
# REFERENTIAL INTEGRITY CHECKS
# =============================================================================
def apply_referential_integrity(df):
    """Check data consistency and relationships"""
    integrity_stats = {}
    
    # Check for duplicate IDs if ID column exists
    if 'id' in df.columns:
        try:
            total_rows = df.height
            unique_ids = df.select('id').unique().height
            duplicates = total_rows - unique_ids
            
            if duplicates > 0:
                integrity_stats['duplicate_ids'] = {
                    'duplicate_count': duplicates,
                    'duplicate_pct': round(duplicates / total_rows * 100, 2)
                }
        except Exception as e:
            logger.warning(f"Error checking duplicate IDs: {e}")
    
    # Check date consistency (reporting_year matches date)
    if 'reporting_year' in df.columns and 'date' in df.columns:
        try:
            mismatches = df.filter(
                (pl.col('reporting_year').cast(pl.Utf8) != 
                 pl.col('date').cast(pl.Utf8).str.slice(0, 4))
            ).height
            
            if mismatches > 0:
                integrity_stats['date_year_mismatch'] = {
                    'mismatch_count': mismatches,
                    'mismatch_pct': round(mismatches / df.height * 100, 2)
                }
        except Exception as e:
            logger.warning(f"Error checking date/year consistency: {e}")
    
    return {
        'integrity_issues': integrity_stats,
        'total_integrity_issues': len(integrity_stats)
    }
