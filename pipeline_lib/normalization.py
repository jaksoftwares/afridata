# =============================================================================
# STATISTICAL NORMALIZATION & ENCODING
# =============================================================================
"""
Automatic statistical normalization:
- Z-score normalization for numeric data
- Log transformation for skewed distributions
- Categorical encoding (one-hot / label)
"""

import polars as pl
import numpy as np
import logging
from scipy import stats

logger = logging.getLogger(__name__)

# =============================================================================
# STATISTICAL NORMALIZATION
# =============================================================================
def detect_numeric_columns(df):
    """Detect numeric columns that need normalization"""
    numeric_cols = []
    for col in df.columns:
        if df[col].dtype in [pl.Int32, pl.Int64, pl.Float32, pl.Float64]:
            if df[col].null_count() < df.height * 0.5:  # At least 50% non-null
                numeric_cols.append(col)
    return numeric_cols

def detect_skewed_columns(df, numeric_cols, threshold=1.5):
    """Detect columns with skewed distributions (|skewness| > threshold)"""
    skewed_cols = []
    
    for col in numeric_cols:
        try:
            values = df[col].drop_nulls().to_numpy()
            if len(values) > 3:
                skewness = float(stats.skew(values))
                if abs(skewness) > threshold:
                    skewed_cols.append({
                        'column': col,
                        'skewness': round(skewness, 2),
                        'needs_log': abs(skewness) > threshold
                    })
        except Exception as e:
            logger.warning(f"Could not calculate skewness for {col}: {e}")
    
    return skewed_cols

def detect_categorical_columns(df):
    """Detect categorical/string columns"""
    categorical_cols = []
    for col in df.columns:
        if df[col].dtype == pl.Utf8:
            unique_count = df[col].n_unique()
            # Categorical if string with reasonable unique values
            if unique_count < (df.height * 0.5):
                categorical_cols.append({
                    'column': col,
                    'unique_values': unique_count,
                    'cardinality': round(unique_count / df.height * 100, 1)
                })
    
    return categorical_cols

# =============================================================================
# Z-SCORE NORMALIZATION
# =============================================================================
def apply_zscore_normalization(df, columns):
    """Apply Z-score normalization: (x - mean) / std"""
    normalized_cols = []
    
    for col in columns:
        try:
            mean = df[col].mean()
            std = df[col].std()
            
            if std is not None and std > 0:
                # Z-score: (x - mean) / std
                df = df.with_columns(
                    ((pl.col(col) - mean) / std).alias(f"{col}_zscore")
                )
                normalized_cols.append({
                    'column': col,
                    'method': 'zscore',
                    'output_column': f"{col}_zscore",
                    'mean': round(float(mean), 4) if mean else 0,
                    'std': round(float(std), 4) if std else 0
                })
        except Exception as e:
            logger.warning(f"Could not apply Z-score to {col}: {e}")
    
    return df, normalized_cols

# =============================================================================
# LOG TRANSFORMATION
# =============================================================================
def apply_log_transformation(df, columns):
    """Apply log transformation for skewed data"""
    transformed_cols = []
    
    for col in columns:
        try:
            # Check if all values are positive (required for log)
            min_val = df[col].min()
            if min_val is not None and min_val > 0:
                df = df.with_columns(
                    pl.col(col).log().alias(f"{col}_log")
                )
                transformed_cols.append({
                    'column': col,
                    'method': 'log_transformation',
                    'output_column': f"{col}_log",
                    'reason': 'Skewed distribution detected'
                })
            else:
                # For non-positive values, shift then log
                shift = abs(min_val) + 1 if min_val is not None else 1
                df = df.with_columns(
                    (pl.col(col) + shift).log().alias(f"{col}_log")
                )
                transformed_cols.append({
                    'column': col,
                    'method': 'log_transformation_shifted',
                    'output_column': f"{col}_log",
                    'shift_value': shift,
                    'reason': 'Skewed distribution (shifted)'
                })
        except Exception as e:
            logger.warning(f"Could not apply log transformation to {col}: {e}")
    
    return df, transformed_cols

# =============================================================================
# CATEGORICAL ENCODING
# =============================================================================
def apply_categorical_encoding(df, columns):
    """
    Smart categorical encoding:
    - One-hot if <= 10 unique values
    - Label encoding if > 10 unique values
    """
    encoded_cols = []
    
    for col_info in columns:
        col = col_info['column']
        unique_count = col_info['unique_values']
        
        try:
            if unique_count <= 10:
                # One-hot encoding
                df = df.with_columns(
                    pl.col(col).cast(pl.Categorical)
                )
                
                # Get dummy variables
                dummies = pl.get_dummies(df.select(col), separator='_')
                df = df.drop(col).hstack(dummies)
                
                encoded_cols.append({
                    'column': col,
                    'method': 'one_hot_encoding',
                    'unique_values': unique_count,
                    'reason': 'Few categories (≤10)'
                })
            else:
                # Label encoding for high cardinality
                unique_vals = df[col].unique().sort()
                encoding_map = {val: idx for idx, val in enumerate(unique_vals)}
                
                df = df.with_columns(
                    pl.col(col).map_elements(
                        lambda x: encoding_map.get(x, -1),
                        return_dtype=pl.Int64
                    ).alias(f"{col}_encoded")
                )
                
                encoded_cols.append({
                    'column': col,
                    'method': 'label_encoding',
                    'unique_values': unique_count,
                    'output_column': f"{col}_encoded",
                    'reason': 'High cardinality (>10)'
                })
        except Exception as e:
            logger.warning(f"Could not encode {col}: {e}")
    
    return df, encoded_cols

# =============================================================================
# MAIN NORMALIZATION PIPELINE
# =============================================================================
def apply_automatic_normalization(df):
    """
    Automatically detect and apply all normalizations
    Returns: normalized_df, summary_report
    """
    logger.info("Starting automatic statistical normalization...")
    
    all_stats = {
        'numeric_detected': [],
        'skewed_detected': [],
        'categorical_detected': [],
        'normalizations_applied': {
            'zscore': [],
            'log_transform': [],
            'categorical_encoding': []
        }
    }
    
    # 1. Detect numeric columns
    numeric_cols = detect_numeric_columns(df)
    all_stats['numeric_detected'] = numeric_cols
    logger.info(f"Detected {len(numeric_cols)} numeric columns: {numeric_cols}")
    
    if numeric_cols:
        # Apply Z-score normalization
        df, zscore_results = apply_zscore_normalization(df, numeric_cols)
        all_stats['normalizations_applied']['zscore'] = zscore_results
        logger.info(f"Applied Z-score normalization to {len(zscore_results)} columns")
    
    # 2. Detect skewed columns
    skewed_cols = detect_skewed_columns(df, numeric_cols)
    all_stats['skewed_detected'] = skewed_cols
    logger.info(f"Detected {len(skewed_cols)} skewed columns")
    
    if skewed_cols:
        skewed_col_names = [s['column'] for s in skewed_cols]
        df, log_results = apply_log_transformation(df, skewed_col_names)
        all_stats['normalizations_applied']['log_transform'] = log_results
        logger.info(f"Applied log transformation to {len(log_results)} columns")
    
    # 3. Detect categorical columns
    categorical_cols = detect_categorical_columns(df)
    all_stats['categorical_detected'] = categorical_cols
    logger.info(f"Detected {len(categorical_cols)} categorical columns")
    
    if categorical_cols:
        df, encoding_results = apply_categorical_encoding(df, categorical_cols)
        all_stats['normalizations_applied']['categorical_encoding'] = encoding_results
        logger.info(f"Applied categorical encoding to {len(encoding_results)} columns")
    
    logger.info("Automatic normalization complete")
    
    return df, all_stats

# =============================================================================
# SUMMARY REPORT GENERATION
# =============================================================================
def generate_normalization_summary(stats):
    """Create human-readable summary of applied normalizations"""
    summary = []
    
    # Numeric normalization
    if stats['normalizations_applied']['zscore']:
        count = len(stats['normalizations_applied']['zscore'])
        cols = ', '.join([r['column'] for r in stats['normalizations_applied']['zscore'][:3]])
        if count > 3:
            cols += f" +{count-3} more"
        summary.append(f"✓ Z-score normalized {count} numeric columns ({cols})")
    
    # Log transformation
    if stats['normalizations_applied']['log_transform']:
        count = len(stats['normalizations_applied']['log_transform'])
        cols = ', '.join([r['column'] for r in stats['normalizations_applied']['log_transform'][:3]])
        if count > 3:
            cols += f" +{count-3} more"
        summary.append(f"✓ Log transformation applied to {count} skewed columns ({cols})")
    
    # Categorical encoding
    if stats['normalizations_applied']['categorical_encoding']:
        count = len(stats['normalizations_applied']['categorical_encoding'])
        one_hot = sum(1 for r in stats['normalizations_applied']['categorical_encoding'] if r['method'] == 'one_hot_encoding')
        label = count - one_hot
        
        methods = []
        if one_hot > 0:
            methods.append(f"{one_hot} one-hot")
        if label > 0:
            methods.append(f"{label} label-encoded")
        
        summary.append(f"✓ Categorical encoding applied: {', '.join(methods)}")
    
    return summary
