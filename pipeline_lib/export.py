# =============================================================================
# pipeline_export.py — DATA EXPORT & DJANGO INTEGRATION
# =============================================================================
"""
Helper module for exporting processed data to different formats.
Designed for Django integration with the download workflow.
"""

import logging
import os
from datetime import datetime
import polars as pl

logger = logging.getLogger(__name__)

# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================
def export_to_csv(df, output_path, dataset_name="standardised_data"):
    """
    Export Polars DataFrame to CSV format.
    
    Args:
        df (pl.DataFrame): The processed dataframe
        output_path (str): Directory where file will be saved
        dataset_name (str): Name for the file
    
    Returns:
        str: Full path to exported file
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{dataset_name}_{timestamp}.csv"
        filepath = os.path.join(output_path, filename)
        
        df.write_csv(filepath)
        logger.info(f"Exported CSV: {filepath}")
        return filepath
    
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise

def export_to_parquet(df, output_path, dataset_name="standardised_data"):
    """
    Export Polars DataFrame to Parquet format.
    
    Args:
        df (pl.DataFrame): The processed dataframe
        output_path (str): Directory where file will be saved
        dataset_name (str): Name for the file
    
    Returns:
        str: Full path to exported file
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{dataset_name}_{timestamp}.parquet"
        filepath = os.path.join(output_path, filename)
        
        df.write_parquet(filepath)
        logger.info(f"Exported Parquet: {filepath}")
        return filepath
    
    except Exception as e:
        logger.error(f"Error exporting Parquet: {e}")
        raise

def export_schema_mapping(schema, output_path, dataset_name="schema_mapping"):
    """
    Export schema mapping as JSON for review page.
    
    Args:
        schema (dict): The schema dict from pipeline
        output_path (str): Directory where file will be saved
        dataset_name (str): Name for the file
    
    Returns:
        str: Full path to exported file
    """
    import json
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{dataset_name}_{timestamp}.json"
        filepath = os.path.join(output_path, filename)
        
        mapping_data = {
            "domain": schema.get("domain"),
            "alignment_confidence": schema.get("alignment_confidence"),
            "mapping_instructions": schema.get("mapping_instructions"),
            "official_standard": schema.get("official_standard")
        }
        
        with open(filepath, 'w') as f:
            json.dump(mapping_data, f, indent=2)
        
        logger.info(f"Exported schema mapping: {filepath}")
        return filepath
    
    except Exception as e:
        logger.error(f"Error exporting schema mapping: {e}")
        raise

# =============================================================================
# DJANGO HELPER CLASS
# =============================================================================
class StandardisationJobResult:
    """
    Wrapper class for pipeline results, designed for Django models.
    Makes it easy to pass data between pipeline and templates.
    """
    
    def __init__(self, pipeline_result):
        """
        Initialize from pipeline result dictionary.
        
        Args:
            pipeline_result (dict): Return value from process_dataset()
        """
        self.data = pipeline_result.get('data')
        self.schema = pipeline_result.get('schema')
        self.cleaning_results = pipeline_result.get('cleaning_results')
        self.report = pipeline_result.get('report')
        self.domain = pipeline_result.get('domain')
        self.dataset_name = pipeline_result.get('dataset_name')
        self.registry_key = pipeline_result.get('registry_key')
        
        # UI Metrics (for standardisation_ready.html)
        self.ai_confidence = pipeline_result.get('ai_confidence', 0)
        self.completeness = pipeline_result.get('completeness', 0)
        self.mapping_score = pipeline_result.get('mapping_score', 0)
        self.rows_processed = pipeline_result.get('rows_processed', 0)
        self.columns_mapped = pipeline_result.get('columns_mapped', 0)
    
    @property
    def mapping_instructions(self):
        """Get raw → standard mapping for review page"""
        return self.schema.get('mapping_instructions', {})
    
    @property
    def official_standard(self):
        """Get official standard schema"""
        return self.schema.get('official_standard', {})
    
    @property
    def validation_issues(self):
        """Get validation issues for display"""
        return self.report.get('issues_found', {})
    
    def get_summary_for_display(self):
        """
        Get summary metrics formatted for UI display.
        
        Returns:
            dict: Metrics ready for template context
        """
        return {
            'domain': self.domain,
            'dataset_name': self.dataset_name,
            'ai_confidence_pct': round(self.ai_confidence * 100, 1),
            'completeness_pct': round(self.completeness, 1),
            'mapping_score_pct': round(self.mapping_score, 1),
            'rows_processed': f"{self.rows_processed:,}",
            'columns_mapped': self.columns_mapped,
            'registry_key': self.registry_key
        }
