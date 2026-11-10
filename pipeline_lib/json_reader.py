"""
Shared reader for JSON and JSON Lines (JSONL / NDJSON) files.

Every part of AfriData that reads a JSON-type dataset goes through this module:
the upload check, the dataset preview, the chart on the detail page, the
metadata pipeline and the standardiser loader. That keeps them in agreement.

The layout is detected from the content, never from the file extension, so
``.json`` and ``.jsonl`` files are both accepted in any of these layouts:

* a JSON array of objects           ``[{"a": 1}, {"a": 2}]``
* a single JSON object              ``{"a": 1}``
* an object wrapping a list         ``{"results": [{"a": 1}, {"a": 2}]}``
* JSON Lines, one object per line   ``{"a": 1}\\n{"a": 2}``

Nested objects are flattened into dotted column names (``address.city``), so
the result is always a flat, tabular DataFrame.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd


class JsonReadError(ValueError):
    """Raised with a message a user can act on when the content isn't readable JSON."""


def decode_json_bytes(content: bytes) -> str:
    """Decode the raw bytes, handling UTF-8 (with or without BOM), UTF-16 and Latin-1."""
    if content.startswith((b"\xff\xfe", b"\xfe\xff")):
        return content.decode("utf-16")
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("latin-1")


def _as_records(items: list[Any]) -> list[dict]:
    if not items:
        raise JsonReadError("The file contains no records.")
    # Scalars (e.g. a list of numbers) become a single 'value' column.
    return [item if isinstance(item, dict) else {"value": item} for item in items]


def _records_from_document(doc: Any) -> list[dict]:
    if isinstance(doc, list):
        return _as_records(doc)
    if isinstance(doc, dict):
        # Common API wrapper: {"data": [...]}, {"results": [...]}. Use the first
        # list whose items are all objects. Otherwise the object is one record.
        for value in doc.values():
            if isinstance(value, list) and value and all(isinstance(v, dict) for v in value):
                return value
        return [doc]
    raise JsonReadError("JSON must be an object or an array of objects.")


def read_json_records(content: bytes) -> list[dict]:
    """Return the records in a JSON or JSONL payload as a list of dicts."""
    text = decode_json_bytes(content).strip()
    if not text:
        raise JsonReadError("The file is empty.")

    # 1. One JSON document (array or object).
    if text[0] in "[{":
        try:
            doc = json.loads(text)
        except json.JSONDecodeError:
            doc = None  # More than one top-level value: JSON Lines, handled below.
        if doc is not None:
            return _records_from_document(doc)

    # 2. JSON Lines: one JSON value per non-blank line.
    records: list[Any] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise JsonReadError(
                f"Line {lineno} is not valid JSON ({exc.msg}). "
                "JSON Lines files need one complete object per line."
            ) from exc
    return _as_records(records)


def records_to_frame(records: list[dict]) -> pd.DataFrame:
    """Flatten nested records into a DataFrame with dotted column names."""
    df = pd.json_normalize(records, sep=".")
    # Lists left in a cell (e.g. "tags": ["a", "b"]) aren't hashable, so charts
    # and group-bys would fail on them. Store those cells as JSON text instead.
    for col in df.columns:
        if df[col].map(lambda v: isinstance(v, (list, dict))).any():
            df[col] = df[col].map(
                lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
            )
    return df


def read_json_frame(content: bytes) -> pd.DataFrame:
    """Read a JSON or JSONL payload straight into a DataFrame."""
    return records_to_frame(read_json_records(content))


def check_json_head(head: bytes) -> str | None:
    """
    Cheap upload-time check on the first chunk of a file.

    Returns an error message, or None if the start of the file looks like JSON or JSONL.
    A full parse would be too slow for a 2GB upload, so this checks only the first byte.
    """
    text = decode_json_bytes(head).lstrip()
    if not text:
        return "The file is empty."
    if text[0] not in "[{":
        return (
            "This doesn't look like JSON. A JSON file must start with '[' or '{', "
            "and a JSON Lines file must start each line with '{'."
        )
    return None
