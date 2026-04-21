# =============================================================================
# pipeline_registry.py — REGISTRY MANAGEMENT
# =============================================================================

import json
import logging
from datetime import datetime
from pipeline_lib.config import get_registry_path

logger = logging.getLogger(__name__)

# =============================================================================
# REGISTRY OPERATIONS
# =============================================================================
def load_registry():
    """Load the schema registry from disk"""
    try:
        with open(get_registry_path(), 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info("No existing registry found. Starting fresh.")
        return {}

def save_registry(registry):
    """Save the schema registry to disk"""
    try:
        with open(get_registry_path(), 'w') as f:
            json.dump(registry, f, indent=2)
        logger.info(f"Registry saved successfully")
    except Exception as e:
        logger.error(f"Failed to save registry: {e}")
        raise

def generate_registry_key(domain, dataset_name):
    """Generate registry key from domain + dataset_name"""
    domain_clean = domain.lower().replace(' ', '_') if domain else 'unknown'
    name_clean = dataset_name.lower().replace(' ', '_') if dataset_name else 'default'
    return f"{domain_clean}_{name_clean}"

def find_existing_schema(domain, raw_columns, registry):
    """
    Find existing schema in registry by domain + raw column matching.
    
    Args:
        domain (str): Domain from upload
        raw_columns (list): Raw column names from incoming dataset
        registry (dict): The schema registry
    
    Returns:
        tuple: (schema_dict, registry_key) if found, else (None, None)
    """
    if not domain:
        return None, None
    
    domain_lower = domain.lower()
    raw_cols_set = set(raw_columns)
    
    # Filter registry entries by domain
    for key, entry in registry.items():
        entry_domain = entry.get("domain", "").lower() if entry.get("domain") else None
        
        if entry_domain != domain_lower:
            continue
        
        # Get raw columns stored in registry
        stored_raw_cols = set(entry.get("raw_columns", []))
        
        # Exact match
        if stored_raw_cols == raw_cols_set:
            logger.info(f"Found exact match in registry: {key}")
            return entry.get("schema"), key
        
        # Fuzzy match (90% similar)
        if len(stored_raw_cols) > 0:
            intersection = len(stored_raw_cols & raw_cols_set)
            similarity = intersection / len(stored_raw_cols)
            
            if similarity >= 0.9:
                logger.info(f"Found fuzzy match in registry: {key} (similarity: {similarity:.2%})")
                return entry.get("schema"), key
    
    logger.info(f"No existing schema found for domain: {domain}")
    return None, None

def store_schema(registry, schema, raw_columns, domain, dataset_name):
    """
    Store a schema in the registry with domain + dataset_name key.
    
    Args:
        registry (dict): The schema registry
        schema (dict): The schema from AI or loaded
        raw_columns (list): Raw column names from source file
        domain (str): Domain name from user
        dataset_name (str): Dataset name (maize, wheat, arabica, etc)
    
    Returns:
        dict: Updated registry
    """
    # Use AI-generated domain if available, otherwise use user-provided domain
    ai_domain = schema.get('domain', domain) if isinstance(schema, dict) else domain
    
    # Generate key from domain + dataset_name
    key = generate_registry_key(ai_domain, dataset_name)
    
    registry[key] = {
        "domain": ai_domain.lower() if ai_domain else None,
        "dataset_name": dataset_name.lower() if dataset_name else None,
        "raw_columns": raw_columns,
        "schema": schema,
        "created_at": datetime.now().isoformat()
    }

    save_registry(registry)
    logger.info(f"Schema stored in registry with key: {key} (domain: {ai_domain}, dataset: {dataset_name})")
    return registry
