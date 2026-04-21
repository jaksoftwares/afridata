"""
Pipeline Library Package
Data standardisation pipeline with multi-format support and AI schema generation
"""

from pipeline_lib.pipeline import process_dataset
from pipeline_lib.loader import load_file, preview_file, get_supported_formats, detect_format
from pipeline_lib.export import export_to_csv, export_to_parquet
from pipeline_lib.registry import load_registry, store_schema, find_existing_schema
from pipeline_lib.schema import generate_schema_with_ai, fingerprint_columns

__all__ = [
    'process_dataset',
    'load_file',
    'preview_file',
    'get_supported_formats',
    'detect_format',
    'export_to_csv',
    'export_to_parquet',
    'load_registry',
    'store_schema',
    'find_existing_schema',
    'generate_schema_with_ai',
    'fingerprint_columns',
]

__version__ = '4.0.0'
__author__ = 'AFRIDATA Team'
