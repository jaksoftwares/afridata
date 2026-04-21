# =============================================================================
# pipeline_config.py — CONFIGURATION & INITIALIZATION
# =============================================================================

import logging
import os
from django.conf import settings
import google.generativeai as genai

# Setup logging
logger = logging.getLogger(__name__)

# =============================================================================
# GEMINI INITIALIZATION
# =============================================================================
def init_gemini():
    """Initialize Gemini API with multiple fallback layers"""
    api_key = None
    source = None
    
    # Layer 1: Django Settings
    settings_key = getattr(settings, 'GEMINI_API_KEY', None)
    if settings_key and settings_key.strip():
        api_key = settings_key.strip()
        source = "Django Settings"
        
    # Layer 2: os.environ (Standard)
    if not api_key:
        env_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
        if env_key and env_key.strip():
            api_key = env_key.strip()
            source = "os.environ"
            
    # Layer 3: Manual .env parsing fallback
    if not api_key:
        try:
            base_dir = getattr(settings, 'BASE_DIR', None)
            if base_dir:
                env_path = os.path.join(base_dir, '.env')
                if os.path.exists(env_path):
                    with open(env_path, 'r') as f:
                        for line in f:
                            if line.startswith('GEMINI_API_KEY=') or line.startswith('GOOGLE_API_KEY='):
                                api_key = line.split('=', 1)[1].strip()
                                # Remove quotes if present
                                api_key = api_key.strip("'").strip('"')
                                if api_key:
                                    source = "Manual .env Parse"
                                    break
        except Exception as e:
            logger.debug(f"Manual .env parse failed: {e}")

    if api_key:
        # Obfuscated log for verification
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
        logger.info(f"✅ Gemini API initialized using {source} (Key: {masked_key})")
        genai.configure(api_key=api_key)
    else:
        logger.error("❌ CRITICAL: No Gemini API key found in any source (Settings, Env, .env file)")
        
    model = genai.GenerativeModel(
        'gemini-flash-latest',
        generation_config={'response_mime_type': 'application/json'}
    )
    return model

_model = None

def get_model():
    """Get the initialized Gemini model (lazy initialization)"""
    global _model
    if _model is None:
        _model = init_gemini()
    return _model

# =============================================================================
# REGISTRY CONFIGURATION
# =============================================================================
def get_registry_path():
    """Get the path to the schema registry file"""
    return str(getattr(settings, 'SCHEMA_REGISTRY_FILE', 'schema_registry.json'))

# =============================================================================
# CRITICAL COLUMNS & PATTERNS
# =============================================================================
CRITICAL_COLUMNS = ['country_code', 'reporting_year', 'id', 'date']

ISO_COUNTRY_CODES = {
    'KEN', 'NGA', 'ZAF', 'UGA', 'TZA', 'ETH', 'EGY', 'CMR', 'GHA', 'CIV',
    'SEN', 'MAR', 'DZA', 'TUN', 'AGO', 'MOZ', 'BWA', 'ZWE', 'ZMB', 'NAM',
    'LSO', 'SWZ', 'MWI', 'RWA', 'BDI', 'DRC', 'COG', 'GAB', 'CAF', 'TCD',
    'STP', 'CPV', 'GMB', 'GNB', 'LBR', 'SLE', 'BEN', 'BGD', 'BFA', 'MUS',
    'SYC', 'COM', 'MRT', 'SOM', 'JIB', 'ERI', 'SDN', 'SSD'
}

ISO_CURRENCY_CODES = {
    'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'CNY',
    'INR', 'NGN', 'ZAR', 'KES', 'GHS', 'CFA', 'EGP', 'MAD', 'TND'
}
