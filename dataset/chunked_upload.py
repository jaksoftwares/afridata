"""
Resumable, parallel uploads for large dataset files.

A large file is sent as numbered parts, several at a time. Each part is written
straight into its place in one staging file, so nothing is copied when the
upload completes. Parts that arrive are recorded by marker files, so an upload
can resume after a dropped connection or a page reload.

Staging layout (under FILE_UPLOAD_TEMP_DIR/chunked/<upload_id>/):
    meta.json     owner, filename, size, part size, creation time
    data.part     the file, pre-sized, filled in place
    received/<n>  an empty marker for each part that has arrived

Every message raised here is written for the user, so it can be shown as is.
"""
import json
import re
import shutil
import uuid
from datetime import datetime, timedelta, timezone as dt_timezone
from math import ceil
from pathlib import Path

from django.conf import settings
from django.core.files import File

_UPLOAD_ID = re.compile(r"[0-9a-f]{32}")
NOT_FOUND = "This upload could not be found. Please choose the file again."
STALE_AFTER = timedelta(hours=48)


class ChunkedUploadError(Exception):
    """The message is safe to show to the user."""


def _root() -> Path:
    root = Path(settings.FILE_UPLOAD_TEMP_DIR) / "chunked"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _dir(upload_id: str) -> Path:
    if not _UPLOAD_ID.fullmatch(upload_id or ""):
        raise ChunkedUploadError(NOT_FOUND)
    return _root() / upload_id


def _load_meta(folder: Path, user) -> dict:
    try:
        meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ChunkedUploadError(NOT_FOUND)
    if meta.get("owner_id") != user.pk:
        # Same message as a missing upload, so one user can't probe another's uploads.
        raise ChunkedUploadError(NOT_FOUND)
    return meta


def _remove_stale_uploads() -> None:
    cutoff = datetime.now(dt_timezone.utc) - STALE_AFTER
    for folder in _root().iterdir():
        try:
            meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
            created = datetime.fromisoformat(meta["created_at"])
        except (OSError, ValueError, KeyError):
            continue
        if created < cutoff:
            shutil.rmtree(folder, ignore_errors=True)


def start(user, filename: str, size: int, part_size: int) -> dict:
    """Begin an upload. Returns the id and the part layout the browser should follow."""
    filename = (filename or "").strip()
    if not filename:
        raise ChunkedUploadError("Please choose a file to upload.")
    max_size = settings.MAX_DATASET_UPLOAD_SIZE
    if size <= 0:
        raise ChunkedUploadError("The file is empty. Please choose a different file.")
    if size > max_size:
        raise ChunkedUploadError(
            f"File is too large. The maximum dataset size is {max_size // (1024 ** 3)} GB."
        )

    _remove_stale_uploads()
    upload_id = uuid.uuid4().hex
    folder = _root() / upload_id
    (folder / "received").mkdir(parents=True)
    with open(folder / "data.part", "wb") as fh:
        fh.truncate(size)  # reserve the space up front; parts fill it in any order
    total = ceil(size / part_size)
    meta = {
        "owner_id": user.pk,
        "filename": filename,
        "size": size,
        "part_size": part_size,
        "total_parts": total,
        "created_at": datetime.now(dt_timezone.utc).isoformat(),
    }
    (folder / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return {"upload_id": upload_id, "part_size": part_size, "total_parts": total}


def status(user, upload_id: str) -> dict:
    folder = _dir(upload_id)
    meta = _load_meta(folder, user)
    received = sorted(int(p.name) for p in (folder / "received").iterdir() if p.name.isdigit())
    return {
        "upload_id": upload_id,
        "part_size": meta["part_size"],
        "total_parts": meta["total_parts"],
        "received": received,
    }


def write_part(user, upload_id: str, index: int, data: bytes) -> None:
    folder = _dir(upload_id)
    meta = _load_meta(folder, user)
    total, part_size, size = meta["total_parts"], meta["part_size"], meta["size"]
    if not 0 <= index < total:
        raise ChunkedUploadError("That part of the file doesn't belong to this upload.")
    expected = min(part_size, size - index * part_size)
    if len(data) != expected:
        raise ChunkedUploadError("A part of the file arrived incomplete. It will be sent again.")
    with open(folder / "data.part", "r+b") as fh:
        fh.seek(index * part_size)
        fh.write(data)
    (folder / "received" / str(index)).touch()


class StagedUpload(File):
    """
    An uploaded file backed by the assembled upload on disk. It is a Django File,
    so the dataset model accepts it like any upload.

    When the dataset is saved, Django calls temporary_file_path() and moves the
    file into place, rather than copying all of it.
    """

    def __init__(self, path: Path, name: str, size: int):
        super().__init__(None, name=name)
        self.path = Path(path)
        self._size = size
        self.content_type = "application/octet-stream"
        self._fh = None

    @property
    def size(self) -> int:
        return self._size

    def _handle(self):
        if self._fh is None:
            self._fh = open(self.path, "rb")
        return self._fh

    def chunks(self, chunk_size: int = 65536):
        with open(self.path, "rb") as fh:
            while True:
                block = fh.read(chunk_size)
                if not block:
                    break
                yield block

    def read(self, size: int = -1) -> bytes:
        return self._handle().read(size)

    def seek(self, pos: int, whence: int = 0) -> int:
        return self._handle().seek(pos, whence)

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def temporary_file_path(self) -> str:
        self.close()  # release the handle so the file can be moved (required on Windows)
        return str(self.path)


def open_completed(user, upload_id: str) -> StagedUpload:
    """Return the finished file, or explain which parts are still missing."""
    folder = _dir(upload_id)
    meta = _load_meta(folder, user)
    received = {p.name for p in (folder / "received").iterdir()}
    missing = meta["total_parts"] - len(received)
    if missing > 0:
        raise ChunkedUploadError(
            f"{missing} part{'s' if missing != 1 else ''} of the file didn't arrive. "
            "Press Upload again and the transfer will continue from where it stopped."
        )
    return StagedUpload(folder / "data.part", meta["filename"], meta["size"])


def discard(upload_id: str) -> None:
    """Remove an upload's staging files, once it has been saved (or is no longer wanted)."""
    try:
        folder = _dir(upload_id)
    except ChunkedUploadError:
        return
    shutil.rmtree(folder, ignore_errors=True)
