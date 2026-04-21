# =============================================================================
# pipeline_schema.py — SCHEMA GENERATION & FINGERPRINTING
# =============================================================================

import re
import hashlib
import json
import logging
import tenacity
from google.api_core import exceptions as google_exceptions
from pipeline_lib.config import get_model

logger = logging.getLogger(__name__)

# =============================================================================
# COLUMN NORMALIZATION & FINGERPRINTING
# =============================================================================
def normalize_columns(cols):
    """Normalize column names for comparison"""
    cleaned = []
    for c in cols:
        c = c.strip().lower()
        c = re.sub(r'\s+', '_', c)
        c = re.sub(r'[^a-z0-9_]', '', c)
        cleaned.append(c)
    return sorted(cleaned)

def fingerprint_columns(cols):
    """Generate a fingerprint hash and normalized columns list"""
    normalized = normalize_columns(cols)
    signature = "|".join(normalized)
    return hashlib.sha256(signature.encode()).hexdigest(), normalized

def jaccard_similarity(a, b):
    """Calculate Jaccard similarity between two sets"""
    set_a, set_b = set(a), set(b)
    if not set_a and not set_b:
        return 1.0
    return len(set_a & set_b) / len(set_a)

# =============================================================================
# SCHEMA MATCHING
# =============================================================================
def find_best_schema(incoming_cols, registry, threshold=0.7):
    """Find the best matching schema in registry based on column structure"""
    best = None
    best_score = 0

    for key, entry in registry.items():
        stored_cols = entry.get("fingerprint_columns", [])
        score = jaccard_similarity(incoming_cols, stored_cols)

        if score > best_score:
            best = entry
            best_score = score

    if best_score >= threshold:
        return best, best_score

    return None, best_score

# =============================================================================
# AI SCHEMA GENERATION
# =============================================================================
@tenacity.retry(
    wait=tenacity.wait_fixed(2),
    stop=tenacity.stop_after_attempt(2),
    retry=tenacity.retry_if_exception_type(
        (google_exceptions.ServiceUnavailable, google_exceptions.DeadlineExceeded, Exception)
    ),
    reraise=True
)
def _call_gemini_api(model, prompt_text):
    """Call Gemini API with retry logic"""
    return model.generate_content(
        prompt_text,
        generation_config={'response_mime_type': 'application/json', 'temperature': 0.0},
        request_options={'timeout': 60}
    )

def generate_schema_with_ai(raw_df, filename, domain=None):
    """Generate a schema using Gemini AI based on data analysis"""
    
    columns_list = raw_df.columns
    
    # Exclude _source_file from AI analysis
    profile_df = raw_df.select([c for c in columns_list if c != '_source_file'])
    sample_rows = profile_df.head(5).to_pandas().values.tolist()

    # Calculate column statistics
    col_stats = {}
    for col in profile_df.columns:
        col_stats[col] = {
            'null_pct': round(profile_df[col].null_count() / profile_df.height * 100, 1),
            'unique_count': profile_df[col].n_unique(),
            'sample_values': profile_df[col].drop_nulls().head(3).to_list()
        }

    prompt = f"""
You are a Senior Data Architect specializing in African Union (AU) interoperability frameworks and pan-African data governance standards.

## YOUR MISSION
Analyze the raw dataset columns below and produce a harmonized schema that aligns with African Union data standards. Your output will be used programmatically, so JSON validity is critical.

## CONTEXT
- DATASET: {filename}
- RAW COLUMNS: {columns_list}
- SAMPLE ROWS (5 records for pattern recognition): {sample_rows}
- COLUMN STATISTICS (null %, unique count, sample values): {col_stats}

## AFRICAN UNION ALIGNMENT GUIDELINES
- Use snake_case for all column names (e.g., country_code, reporting_year)
- Country identifiers must follow ISO 3166-1 alpha-3 (e.g., KEN, NGA, ZAF)
- Date fields must follow ISO 8601 format (YYYY-MM-DD)
- Currency fields must reference ISO 4217 codes and be stored as Float64
- Administrative divisions should align with AU region groupings (ECOWAS, SADC, EAC, AMU, ECCAS)
- Population and quantity fields should use Int64
- Percentage/ratio fields should use Float64
- Categorical fields (gender, status, region_bloc) should use Utf8

## VALID POLARS DATA TYPES (use ONLY these exact strings)
Utf8, Int32, Int64, Float32, Float64, Boolean, Date, Datetime

## CRITICAL DATA INTEGRITY RULES
- YOU MUST NOT modify, nullify, drop, or replace any existing data values.
- Your ONLY permitted actions are: RENAMING columns and RECASTING their data type.
- transformation_needed refers ONLY to type casting. Nothing else.
- If no type cast is needed, set transformation_needed for that column to null.
- NEVER introduce nulls where values already exist.

## TRANSFORMATION FORMULA CONVENTIONS (type casting ONLY)
- No cast needed: null
- Type cast: cast(Float64), cast(Int64), cast(Utf8), etc.
- Date string parsing: strptime('%Y-%m-%d')
- Nothing else is permitted

## OUTPUT RULES
- Return ONLY a single valid JSON object. No markdown, no explanation, no code fences.
- If a raw column has no clear AU-standard equivalent, map it to __DROP__ in mapping_instructions.
- alignment_confidence: float 0.0 to 1.0 reflecting mapping quality.
- Every column in official_standard must appear in transformation_needed (null if no cast needed).
- Do NOT include _source_file in the mapping_instructions.

## REQUIRED JSON STRUCTURE
{{
  "domain": "String or null",
  "alignment_confidence": 0.0,
  "official_standard": {{"standard_col_name": "Polars_Type"}},
  "mapping_instructions": {{"raw_col_name": "standard_col_name_or___DROP__"}},
  "transformation_needed": {{"standard_col_name": "cast(Type)_or_null"}}
}}
"""

    try:
        model = get_model()
        response = _call_gemini_api(model, prompt)
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        schema_data = json.loads(clean_text)
        
        logger.info(f"Schema generated for {filename}")
        return schema_data

    except Exception as e:
        logger.error(f"AI Error generating schema for {filename}: {e}")
        raise
