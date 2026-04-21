# =============================================================================
# pipeline_loader.py — MULTI-FORMAT FILE LOADER
# =============================================================================
"""
Handles loading various file formats and converting them to Polars DataFrames.
Keeps the pipeline format-agnostic.
"""

import logging
import os
import json
import polars as pl
from pathlib import Path

logger = logging.getLogger(__name__)

# =============================================================================
# SUPPORTED FORMATS
# =============================================================================
SUPPORTED_FORMATS = {
    '.csv': 'CSV',
    '.xlsx': 'Excel (XLSX)',
    '.xls': 'Excel (XLS)',
    '.json': 'JSON',
    '.parquet': 'Parquet',
    '.txt': 'Text (TSV/Delimited)',
    '.xml': 'XML',
    '.yaml': 'YAML',
    '.yml': 'YAML'
}

# =============================================================================
# FORMAT DETECTION
# =============================================================================
def detect_format(file_path):
    """
    Detect file format from extension.
    
    Args:
        file_path (str): Path to the file
    
    Returns:
        tuple: (format_key, format_name) or (None, None) if unsupported
    """
    ext = Path(file_path).suffix.lower()
    
    if ext in SUPPORTED_FORMATS:
        return ext, SUPPORTED_FORMATS[ext]
    
    logger.warning(f"Unsupported file format: {ext}")
    return None, None

# =============================================================================
# FORMAT-SPECIFIC LOADERS
# =============================================================================
def load_csv(file_path):
    """Load CSV file"""
    try:
        df = pl.read_csv(file_path, infer_schema_length=0)
        logger.info(f"Loaded CSV: {os.path.basename(file_path)}")
        return df
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        raise

def load_excel(file_path):
    """Load Excel file (XLSX or XLS)"""
    try:
        df = pl.read_excel(file_path, infer_schema_length=0)
        logger.info(f"Loaded Excel: {os.path.basename(file_path)}")
        return df
    except Exception as e:
        logger.error(f"Error loading Excel: {e}")
        raise

def load_json(file_path):
    """Load JSON file"""
    try:
        # Handle both JSON files and JSONL (newline-delimited JSON)
        with open(file_path, 'r') as f:
            first_char = f.read(1)
        
        if first_char == '[':
            # Array of objects: [{...}, {...}]
            df = pl.read_json(file_path)
        else:
            # Newline-delimited JSON: {...}\n{...}
            df = pl.read_ndjson(file_path)
        
        logger.info(f"Loaded JSON: {os.path.basename(file_path)}")
        return df
    except Exception as e:
        logger.error(f"Error loading JSON: {e}")
        raise

def load_parquet(file_path):
    """Load Parquet file"""
    try:
        df = pl.read_parquet(file_path)
        logger.info(f"Loaded Parquet: {os.path.basename(file_path)}")
        return df
    except Exception as e:
        logger.error(f"Error loading Parquet: {e}")
        raise

def load_text(file_path, delimiter='\t'):
    """
    Load delimited text file (TSV, pipe-delimited, comma-delimited, etc.).
    
    Args:
        file_path (str): Path to file
        delimiter (str): Column delimiter (default: tab)
    
    Returns:
        pl.DataFrame: Loaded data
    """
    try:
        df = pl.read_csv(file_path, separator=delimiter, infer_schema_length=0)
        logger.info(f"Loaded Text file: {os.path.basename(file_path)}")
        return df
    except Exception as e:
        logger.error(f"Error loading Text file: {e}")
        raise

def load_xml(file_path, root_element=None):
    """
    Load XML file by converting to DataFrame.
    Note: XML loading requires parsing and structure definition.
    
    Args:
        file_path (str): Path to XML file
        root_element (str): Root element name to extract (optional)
    
    Returns:
        pl.DataFrame: Loaded data
    """
    try:
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Extract element specified or use root
        target = root if not root_element else root.find(root_element)
        
        # Convert XML elements to dictionaries
        data = []
        for child in target:
            row = {elem.tag: elem.text for elem in child}
            data.append(row)
        
        if not data:
            raise ValueError("No data found in XML file")
        
        df = pl.DataFrame(data)
        logger.info(f"Loaded XML: {os.path.basename(file_path)}")
        return df
    
    except Exception as e:
        logger.error(f"Error loading XML: {e}")
        raise

def load_yaml(file_path):
    """
    Load YAML file.
    Requires: pip install pyyaml
    
    Args:
        file_path (str): Path to YAML file
    
    Returns:
        pl.DataFrame: Loaded data
    """
    try:
        import yaml
        
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Convert to list of dicts if it's a dict
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise ValueError("YAML must contain list or dict")
        
        df = pl.DataFrame(data)
        logger.info(f"Loaded YAML: {os.path.basename(file_path)}")
        return df
    
    except ImportError:
        logger.error("PyYAML not installed. Install with: pip install pyyaml")
        raise
    except Exception as e:
        logger.error(f"Error loading YAML: {e}")
        raise

# =============================================================================
# UNIFIED LOADER
# =============================================================================
def load_file(file_path, **kwargs):
    """
    Universal file loader - detects format and loads accordingly.
    
    Args:
        file_path (str): Path to file
        **kwargs: Format-specific options:
            - delimiter (str): For text files (default: tab)
            - root_element (str): For XML files
            - sheet (str/int): For Excel files
    
    Returns:
        tuple: (dataframe, filename, format_name)
    
    Raises:
        ValueError: If format not supported or file not found
    """
    
    # Check file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    filename = os.path.basename(file_path)
    format_key, format_name = detect_format(file_path)
    
    if not format_key:
        raise ValueError(f"Unsupported file format for: {filename}")
    
    logger.info(f"Loading {format_name} file: {filename}")
    
    # Route to appropriate loader
    if format_key == '.csv':
        df = load_csv(file_path)
    
    elif format_key in ['.xlsx', '.xls']:
        try:
            sheet = kwargs.get('sheet', 0)
            df = pl.read_excel(file_path, sheet_id=sheet, infer_schema_length=0)
        except Exception as e:
            logger.error(f"Error loading Excel: {e}")
            raise
    
    elif format_key == '.json':
        df = load_json(file_path)
    
    elif format_key == '.parquet':
        df = load_parquet(file_path)
    
    elif format_key == '.txt':
        delimiter = kwargs.get('delimiter', '\t')
        df = load_text(file_path, delimiter=delimiter)
    
    elif format_key == '.xml':
        root_element = kwargs.get('root_element', None)
        df = load_xml(file_path, root_element=root_element)
    
    elif format_key in ['.yaml', '.yml']:
        df = load_yaml(file_path)
    
    else:
        raise ValueError(f"Format handler not implemented: {format_key}")
    
    return df, filename, format_name

# =============================================================================
# VALIDATION & PREVIEW
# =============================================================================
def preview_file(file_path, rows=5, **kwargs):
    """
    Load and preview a file without full processing.
    
    Args:
        file_path (str): Path to file
        rows (int): Number of rows to preview
        **kwargs: Format-specific options
    
    Returns:
        dict: Preview information
    """
    try:
        df, filename, format_name = load_file(file_path, **kwargs)
        
        preview = {
            'filename': filename,
            'format': format_name,
            'shape': {
                'rows': df.height,
                'columns': df.width
            },
            'column_names': df.columns,
            'column_types': {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)},
            'sample_rows': df.head(rows).to_dicts()
        }
        
        return preview
    
    except Exception as e:
        logger.error(f"Error previewing file: {e}")
        return {
            'error': str(e),
            'filename': os.path.basename(file_path)
        }

def get_supported_formats():
    """Return list of supported formats for UI"""
    return list(SUPPORTED_FORMATS.values())

def get_format_help():
    """Return help text for each format"""
    return {
        'CSV': 'Comma-separated values. Standard tabular format.',
        'Excel (XLSX)': 'Microsoft Excel format. Supports multiple sheets.',
        'Excel (XLS)': 'Legacy Excel format.',
        'JSON': 'Array of objects or newline-delimited JSON.',
        'Parquet': 'Columnar storage format. Efficient for large datasets.',
        'Text (TSV/Delimited)': 'Tab-separated or custom delimiter. Specify delimiter in options.',
        'XML': 'XML format. Specify root element to extract data.',
        'YAML': 'YAML format. Requires pyyaml package.'
    }
