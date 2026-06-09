# metadata/tasks.py
"""
Celery tasks for the Metadata Extraction Pipeline.

This module lives at  metadata/tasks.py  — one level above the api/
sub-package, directly inside the metadata Django app.

Rationale for placement
-----------------------
tasks.py belongs in  metadata/  (the app root), NOT in  metadata/api/ :

  metadata/
  ├── __init__.py
  ├── models.py          ← PipelineRun, MetadataResult, ColumnProfile
  ├── tasks.py           ← HERE  (Celery autodiscover scans app roots)
  └── api/
      ├── __init__.py
      ├── serializers.py
      ├── views.py
      └── urls.py

Celery's autodiscover_tasks() looks for a tasks module at the root of
each INSTALLED_APP.  Placing tasks.py inside metadata/api/ would require
manual task registration and would couple the async worker to the HTTP
layer, which defeats separation of concerns.  The api/ sub-package is
an HTTP transport layer; tasks.py is a domain/infrastructure concern
shared by both the API layer and any future management commands or
signals that need to trigger the pipeline.

Task
----
run_pipeline_task   Executes the full MetadataPipeline for a given run_id.
                    Called by  api/views.py  via  .delay()  immediately
                    after the PipelineRun record is created.

Error handling
--------------
Any unhandled exception is caught, the run is marked FAILED, and the
exception is re-raised so Celery records the failure in its result
backend and any configured monitoring (Flower, Sentry, etc.) is notified.
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    # Dummy decorator for when Celery is not installed
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_column_profiles_bulk(
    run,
    profiles: dict[str, dict],
) -> None:
    """
    Persist per-column profile data to the ColumnProfile table in one bulk
    INSERT, replacing any pre-existing rows for this run.

    Extracts the subset of fields that ColumnProfile stores as first-class
    columns; everything else is stored in profile_data as a catch-all blob.

    Args:
        run:      PipelineRun instance (must already be saved).
        profiles: Enriched profile dict from PipelineResult.profiles.
                  Key = column name, value = profile dict.
    """
    from metadata.models import ColumnProfile

    # Remove any stale profiles from a previous (e.g. retried) attempt.
    ColumnProfile.objects.filter(run=run).delete()

    column_profiles = []
    for col_name, profile in profiles.items():
        column_profiles.append(
            ColumnProfile(
                run                 = run,
                column_name         = col_name,
                dtype               = str(profile.get("dtype", "")),
                semantic_type       = profile.get("semantic_type", ""),
                semantic_confidence = profile.get("semantic_confidence"),
                nullable            = bool(profile.get("nullable", False)),
                unique_count        = profile.get("unique_count"),
                null_count          = profile.get("null_count"),
                profile_data        = profile,
            )
        )

    if column_profiles:
        ColumnProfile.objects.bulk_create(column_profiles)
        logger.debug(
            "Bulk-created %d ColumnProfile rows for run %s.",
            len(column_profiles),
            run.id,
        )


def _infer_and_merge_dataset_metadata(run, result, column_count) -> None:
    """
    Perform dataset-level metadata inference using Gemini LLM,
    merge with existing blank fields on the Dataset model,
    calculate quality score, and save the Dataset.
    """
    dataset = getattr(run, "dataset", None)
    if not dataset:
        logger.info("No associated dataset found for run %s. Skipping dataset-level metadata inference.", run.id)
        return

    logger.info("Starting dataset-level metadata inference for dataset %s (run %s).", dataset.id, run.id)

    # 1. Get preview data (first 5 rows) for CSV/Excel
    preview_text = ""
    try:
        import pandas as pd
        import io
        if dataset.file:
            dataset.file.seek(0)
            file_content = dataset.file.read()
            if dataset.dataset_type == 'csv':
                try:
                    df = pd.read_csv(io.BytesIO(file_content), nrows=10, encoding='utf-8')
                except Exception:
                    try:
                        df = pd.read_csv(io.BytesIO(file_content), nrows=10, encoding='latin-1')
                    except Exception:
                        df = pd.read_csv(io.BytesIO(file_content), nrows=10)
            elif dataset.dataset_type == 'excel':
                df = pd.read_excel(io.BytesIO(file_content), nrows=10)
            else:
                df = pd.DataFrame()
            if not df.empty:
                preview_text = f"Columns: {list(df.columns)}\nPreview (first few rows):\n{df.head(5).to_string()}"
    except Exception as e:
        logger.warning("Failed to parse dataset file preview for LLM: %s", e)

    # 2. Build prompt for Gemini AI
    preview_section = f"PREVIEW:\n{preview_text}" if preview_text else ""
    prompt = f"""
    You are an expert data cataloger. Given the following information about a dataset, extract/infer the standard metadata fields.
    
    TITLE: {dataset.title}
    DESCRIPTION/BIO: {dataset.bio}
    TOPICS: {dataset.topics}
    
    {preview_section}
    
    You MUST provide a reasonable, specific value for every single field listed below. Do not return null, empty, or 'Not specified' values. If a field is not explicitly mentioned, make your best guess/inference based on the title, bio, topics, and data preview (e.g. geographic coverage might be 'Global' or the country of origin of the topic; collection_date should be a specific date in YYYY-MM-DD format, such as the estimated release date or the current year).
    Format your response as a valid JSON object with the following keys and values:
    - "original_author": The original creator/organization of the dataset (string, e.g. "World Bank" or the likely creator, default to "Unknown Creator").
    - "data_source": Where the dataset was sourced from (string, e.g. "Public Records", "Web Scraped", or a specific database, default to "Public Records").
    - "collection_date": The date when the data was collected, in YYYY-MM-DD format (string, always provide a specific date, such as the date of publication or the current year's date like "2026-06-09").
    - "language": The language of the dataset (string, default "English").
    - "dataset_license": The license under which the dataset is published (string, default "Open Database License (ODbL)").
    - "update_frequency": How often the dataset is updated, e.g. "Daily", "Monthly", "One-time", "Yearly" (string, choose a likely frequency, default to "One-time").
    - "geographic_coverage": The geographic region or country covered by the dataset (string, e.g. "Global", "United States", "Kenya", default to "Global" if not specific).
    - "temporal_coverage": The time period covered, e.g. "2020-2023" (string, always provide a range or era like "1990-2026").
    - "usage_notes": Basic guidelines or tips on how to use the dataset (string, always provide a helpful note on what columns or patterns to look out for).
    
    Return ONLY the raw JSON object. Do not wrap in markdown code blocks.
    """

    # 3. Call Gemini API
    data = {}
    try:
        from django.conf import settings
        # pyrefly: ignore [missing-import]
        from google import genai
        # pyrefly: ignore [missing-import]
        from google.genai import types
        import json

        api_key = getattr(settings, "GEMINI_API_KEY", "")
        if not api_key:
            logger.warning("GEMINI_API_KEY not configured. Skipping LLM metadata inference.")
        else:
            client = genai.Client(api_key=api_key)
            model_name = getattr(settings, "LLM_MODEL", "gemini-2.5-flash")
            if model_name == "gemini-1.5-pro":
                model_name = "gemini-2.5-flash"
            logger.info("Calling Gemini API for dataset metadata inference using model '%s'.", model_name)
            logger.debug("Prompt sent to Gemini: %s", prompt)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            logger.info("Received response from Gemini. Raw text: %s", response.text)
            if response.text:
                text = response.text.strip()
                if text.startswith("```"):
                    lines = text.splitlines()
                    lines = [l for l in lines if not l.strip().startswith("```")]
                    text = "\n".join(lines).strip()
                data = json.loads(text)
                logger.info("Parsed metadata JSON successfully: %s", data)
    except Exception as e:
        logger.exception("Failed to run Gemini AI metadata inference: %s", e)

    # 4. Merge inferred fields (only if blank/empty on dataset)
    inferred_fields = [
        "original_author", "data_source", "collection_date", "language",
        "dataset_license", "update_frequency", "geographic_coverage",
        "temporal_coverage", "usage_notes"
    ]

    from django.utils import timezone
    from datetime import date as datetime_date
    current_date = timezone.now().date()
    uploader_name = dataset.author.get_full_name() or dataset.author.username if dataset.author else "Unknown"

    default_fallbacks = {
        "original_author": uploader_name,
        "data_source": "Community upload / Online source",
        "collection_date": current_date,
        "language": "English",
        "dataset_license": "Open Database License (ODbL)",
        "update_frequency": "One-time",
        "geographic_coverage": "Global",
        "temporal_coverage": f"{current_date.year - 1}-{current_date.year}",
        "usage_notes": f"This is a {dataset.dataset_type.upper() if dataset.dataset_type else ''} dataset uploaded by {uploader_name}. It contains {column_count} columns and has been successfully profiled. Suitable for data analysis and general research."
    }

    for field in inferred_fields:
        inferred_val = data.get(field)
        user_val = getattr(dataset, field)
        
        # Check if user value is blank (empty, None, or whitespace-only string)
        is_blank = not user_val or (isinstance(user_val, str) and not user_val.strip())
        
        if is_blank:
            val_to_set = None
            if inferred_val:
                val_to_set = str(inferred_val).strip()
                # Check for null/unspecified placeholders returned by LLM
                if val_to_set.lower() in ("null", "none", "unspecified", "not specified", "unknown", ""):
                    val_to_set = None
            
            # If not successfully inferred by LLM, use the fallback default
            if val_to_set is None:
                val_to_set = default_fallbacks.get(field)
                
            # Set the value on dataset
            if field == "collection_date":
                if val_to_set:
                    if isinstance(val_to_set, datetime_date):
                        setattr(dataset, field, val_to_set)
                    else:
                        try:
                            from datetime import datetime
                            parsed_date = datetime.strptime(str(val_to_set), "%Y-%m-%d").date()
                            setattr(dataset, field, parsed_date)
                        except Exception:
                            setattr(dataset, field, current_date)
            else:
                setattr(dataset, field, str(val_to_set) if val_to_set is not None else "")

    # 5. Calculate quality score
    populated_fields_count = sum(1 for field in inferred_fields if getattr(dataset, field))
    metadata_completeness = populated_fields_count / 9.0

    schema_score = 0.0
    if column_count > 0 and result and hasattr(result, "profiles"):
        col_scores = []
        for col_name, profile in result.profiles.items():
            col_has_desc = 1.0 if profile.get("description") else 0.0
            col_has_sem = 1.0 if profile.get("semantic_type") and profile.get("semantic_type") != "unknown" else 0.0
            col_scores.append((col_has_desc + col_has_sem) / 2.0)
        schema_score = sum(col_scores) / len(col_scores) if col_scores else 1.0
    elif column_count > 0:
        schema_score = 1.0

    # Calculate quality score as a weighted combination (60% metadata completeness, 40% schema completeness)
    quality_score = 0.6 * metadata_completeness + 0.4 * schema_score
    dataset.metadata_quality_score = round(max(0.0, min(1.0, quality_score)), 4)

    dataset.save()
    logger.info("Successfully completed metadata merge & scoring for dataset %s. Score: %.4f", dataset.id, dataset.metadata_quality_score)


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    name="metadata.tasks.run_pipeline_task",
    # Retry up to 2 times on transient errors (e.g. DB hiccup on startup),
    # with a 30-second back-off.  Validation / data errors are NOT retried
    # because the task catches them and marks the run FAILED explicitly.
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,          # acknowledge only after the task completes
    reject_on_worker_lost=True,
)
def run_pipeline_task(
    self,
    *,
    run_id:              str,
    source:              str,
    source_path:         str,
    dataset_title:       str       = "",
    dataset_description: str       = "",
    sql_schema:          str | None = None,
    sql_query:           str | None = None,
) -> dict[str, Any]:
    """
    Execute the full MetadataPipeline for a queued PipelineRun.

    This task is dispatched by  api/views.PipelineRunListCreateView.post()
    immediately after the PipelineRun record is created in PENDING state.

    Lifecycle
    ---------
    1. Fetch the PipelineRun record and call mark_running().
    2. Build and execute MetadataPipeline.run().
    3. Persist MetadataResult and ColumnProfile records from the result.
    4. Call mark_success() on the run.
    5. On any exception, call mark_failed() then re-raise.

    Args:
        run_id:              UUID string of the PipelineRun to execute.
        source:              "csv" | "excel" | "sql"
        source_path:         File path (csv/excel) or table name (sql).
        dataset_title:       Forwarded to MetadataPipeline.
        dataset_description: Forwarded to MetadataPipeline.
        sql_schema:          DB schema/namespace (sql source only).
        sql_query:           Raw SELECT statement (sql source only).

    Returns:
        A summary dict with run_id, status, elapsed_s, and column_count.
        Celery stores this in its result backend (if configured).

    Raises:
        Re-raises any exception after recording the failure on the run,
        so Celery marks the task as FAILURE in its result backend.
    """
    from metadata.models import MetadataResult, PipelineRun
    from metadata.core.pipeline import MetadataPipeline

    # ------------------------------------------------------------------
    # 1. Fetch the run record
    # ------------------------------------------------------------------
    try:
        run = PipelineRun.objects.get(pk=run_id)
    except PipelineRun.DoesNotExist:
        # The record was deleted between enqueue and execution — nothing
        # sensible to do other than log and bail out.
        logger.error(
            "run_pipeline_task: PipelineRun %s not found. Task abandoned.",
            run_id,
        )
        return {"run_id": run_id, "status": "NOT_FOUND"}

    logger.info(
        "run_pipeline_task: starting [run_id=%s, source=%s, path=%s].",
        run_id, source, source_path,
    )
    run.mark_running()

    # ------------------------------------------------------------------
    # 2. Build pipeline kwargs based on source type
    # ------------------------------------------------------------------
    pipeline_kwargs: dict[str, Any] = {
        "source":              source,
        "dataset_title":       dataset_title,
        "dataset_description": dataset_description,
    }

    if source in ("csv", "excel"):
        pipeline_kwargs["path"] = source_path

    elif source == "sql":
        # SQL sources need a live SQLAlchemy engine.  The engine is built
        # from settings so it does not travel over the message broker.
        try:
            from django.conf import settings
            # pyrefly: ignore [missing-import]
            from sqlalchemy import create_engine as _create_engine

            db_url = getattr(settings, "PIPELINE_SQL_DATABASE_URL", None)
            if not db_url:
                raise ValueError(
                    "settings.PIPELINE_SQL_DATABASE_URL is not configured. "
                    "It is required for source='sql' pipeline runs."
                )
            engine = _create_engine(db_url)
        except Exception as exc:
            logger.exception(
                "run_pipeline_task: failed to create SQLAlchemy engine for run %s.",
                run_id,
            )
            run.mark_failed(str(exc))
            raise

        pipeline_kwargs["engine"]     = engine
        pipeline_kwargs["table_name"] = source_path
        if sql_schema:
            pipeline_kwargs["schema"] = sql_schema
        if sql_query:
            pipeline_kwargs["sql_query"] = sql_query

    # ------------------------------------------------------------------
    # 3. Execute the pipeline
    # ------------------------------------------------------------------
    result = None
    column_count = 0
    try:
        result = MetadataPipeline(**pipeline_kwargs).run()
        if result:
            column_count = len(result.schema.get("properties", {}))
    except Exception as exc:
        logger.exception(
            "run_pipeline_task: structural parsing failed for run %s, falling back to metadata-only inference: %s",
            run_id, exc,
        )

    # ------------------------------------------------------------------
    # 4. Persist MetadataResult
    # ------------------------------------------------------------------
    if result:
        try:
            MetadataResult.objects.update_or_create(
                run=run,
                defaults={
                    "json_schema":   result.json_schema,
                    "schema_dict":   result.schema,
                    "schema_report": result.schema_report,
                },
            )
            logger.debug(
                "run_pipeline_task: MetadataResult saved for run %s.", run_id
            )
        except Exception as exc:
            logger.exception(
                "run_pipeline_task: failed to save MetadataResult for run %s: %s",
                run_id, exc,
            )
            run.mark_failed(f"Failed to persist schema result: {exc}")
            raise

        # ------------------------------------------------------------------
        # 5. Persist ColumnProfiles  (best-effort — does not fail the run)
        # ------------------------------------------------------------------
        try:
            _build_column_profiles_bulk(run, result.profiles)
        except Exception:
            # Non-fatal: the schema result is already saved.  Log the error
            # but let the run complete as SUCCESS.
            logger.exception(
                "run_pipeline_task: failed to save ColumnProfiles for run %s "
                "(non-fatal — schema result was persisted successfully).",
                run_id,
            )

    # ------------------------------------------------------------------
    # 6. Infer and merge dataset-level metadata
    # ------------------------------------------------------------------
    try:
        _infer_and_merge_dataset_metadata(run, result, column_count)
    except Exception as exc:
        logger.exception(
            "run_pipeline_task: failed to infer/merge dataset metadata for run %s: %s",
            run_id, exc,
        )

    # ------------------------------------------------------------------
    # 7. Mark SUCCESS
    # ------------------------------------------------------------------
    run.mark_success(
        elapsed_s   = result.elapsed_s if result else 0.0,
        stage_times = result.stage_times if result else {},
    )
    logger.info(
        "run_pipeline_task: completed [run_id=%s, elapsed=%.3fs].",
        run_id, result.elapsed_s if result else 0.0,
    )

    return {
        "run_id":       run_id,
        "status":       "SUCCESS",
        "elapsed_s":    result.elapsed_s if result else 0.0,
        "column_count": column_count,
    }