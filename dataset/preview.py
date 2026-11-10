"""
Bounded reads of dataset files for previews and charts.

A dataset can be gigabytes, and the detail and preview pages must answer within
the proxy's time limit. So these functions never load a large file whole. They
read a sample of at most PREVIEW_ROWS rows. Formats that can only be parsed whole
(Excel, a plain JSON array) are refused above MAX_WHOLE_PARSE_BYTES, with a
message that tells the user to download the file instead.
"""
import io
import json

import pandas as pd

from pipeline_lib.json_reader import JsonReadError, read_json_frame, records_to_frame

PREVIEW_ROWS = 2000
MAX_WHOLE_PARSE_BYTES = 25 * 1024 * 1024  # 25 MB


class PreviewUnavailable(Exception):
    """The message is written for the user."""


def _too_large(kind):
    return PreviewUnavailable(
        f"This {kind} file is too large to preview here. "
        "You can download it and open it on your computer."
    )


def _read_csv_sample(fh):
    last_error = None
    for encoding in ("utf-8", "latin-1"):
        fh.seek(0)
        try:
            return pd.read_csv(fh, nrows=PREVIEW_ROWS, encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    fh.seek(0)
    if last_error:
        return pd.read_csv(fh, nrows=PREVIEW_ROWS)
    raise PreviewUnavailable("This file could not be read as a table.")


def _read_jsonl_sample(fh):
    records = []
    for lineno, raw in enumerate(fh, start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except (ValueError, UnicodeDecodeError) as exc:
            # Name the line, so the owner knows exactly what to fix.
            raise JsonReadError(
                f"Line {lineno} is not valid JSON ({exc}). "
                "JSON Lines files need one complete object per line."
            ) from exc
        if len(records) >= PREVIEW_ROWS:
            break
    if not records:
        raise PreviewUnavailable("No rows could be read from this file.")
    return records_to_frame(records)


def _read_json(fh, size):
    fh.seek(0)
    head = fh.read(4096).lstrip()
    fh.seek(0)
    first_line = head.split(b"\n", 1)[0].strip()
    looks_like_jsonl = head[:1] == b"{" and _parses(first_line)
    if looks_like_jsonl:
        # Each line is a record: read only the first few rows.
        return _read_jsonl_sample(fh)
    if size > MAX_WHOLE_PARSE_BYTES:
        raise _too_large("JSON")
    return read_json_frame(fh.read())


def _parses(line):
    try:
        json.loads(line)
        return True
    except (ValueError, UnicodeDecodeError):
        return False


def _read_parquet(fh):
    try:
        import pyarrow.parquet as pq
    except ImportError:
        raise PreviewUnavailable("Parquet previews are not available on this server.")
    fh.seek(0)
    parquet = pq.ParquetFile(fh)
    for batch in parquet.iter_batches(batch_size=PREVIEW_ROWS):
        return batch.to_pandas()
    return pd.DataFrame()


def read_preview_frame(dataset):
    """
    Return (dataframe, is_sample). The frame holds at most PREVIEW_ROWS rows.
    is_sample is True when the file has more rows than were read.
    Raises PreviewUnavailable with a user message when the file cannot be previewed.
    """
    if dataset.dataset_type == "unstructured":
        return pd.DataFrame(), False

    size = dataset.file.size or 0
    with dataset.file.open("rb") as fh:
        if dataset.dataset_type == "excel":
            if size > MAX_WHOLE_PARSE_BYTES:
                raise _too_large("Excel")
            fh.seek(0)
            df = pd.read_excel(io.BytesIO(fh.read()))
        elif dataset.dataset_type == "json":
            df = _read_json(fh, size)
        elif dataset.dataset_type == "parquet":
            df = _read_parquet(fh)
        else:
            df = _read_csv_sample(fh)

    if len(df) > PREVIEW_ROWS:
        df = df.head(PREVIEW_ROWS)
    return df, len(df) >= PREVIEW_ROWS
