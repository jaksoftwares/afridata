"""HTTP endpoints for resumable chunked uploads. The logic lives in dataset/chunked_upload.py."""
import json
import logging
import time

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from . import chunked_upload
from .chunked_upload import ChunkedUploadError

logger = logging.getLogger('afridata.uploads')


def _error(message, status=400):
    return JsonResponse({'success': False, 'message': str(message)}, status=status)


@login_required
@require_http_methods(['POST'])
def chunked_upload_start(request):
    """Begin an upload. The browser then sends the parts."""
    try:
        body = json.loads(request.body or b'{}')
        filename = str(body.get('filename', ''))
        size = int(body.get('size', 0))
        encoding = str(body.get('encoding', 'raw'))
    except (ValueError, TypeError, AttributeError):
        return _error('Please choose a file to upload.')

    try:
        result = chunked_upload.start(request.user, filename, size, settings.CHUNKED_UPLOAD_PART_SIZE, encoding)
    except ChunkedUploadError as exc:
        return _error(exc)
    return JsonResponse({'success': True, **result})


@login_required
@require_http_methods(['GET'])
def chunked_upload_status(request, upload_id):
    """Which parts have arrived. A browser that reconnects asks this before sending anything again."""
    try:
        result = chunked_upload.status(request.user, upload_id)
    except ChunkedUploadError as exc:
        return _error(exc, status=404)
    return JsonResponse({'success': True, **result})


@login_required
@require_http_methods(['PUT'])
def chunked_upload_part(request, upload_id, index):
    """Receive one part of the file as the raw request body."""
    try:
        declared = int(request.META.get('CONTENT_LENGTH') or 0)
    except ValueError:
        return _error('That part could not be read. It will be sent again.')
    if declared > settings.CHUNKED_UPLOAD_PART_SIZE + chunked_upload.GZIP_OVERHEAD:
        return _error('That part is larger than expected. It will be sent again.', status=413)

    # read() rather than request.body: body-size checks don't apply to a single part.
    started = time.monotonic()
    data = request.read()
    received = time.monotonic()
    try:
        chunked_upload.write_part(request.user, upload_id, index, data)
    except ChunkedUploadError as exc:
        return _error(exc, status=404 if 'could not be found' in str(exc) else 400)
    # Timing per part: shows whether the time goes to the network in front of the app
    # (proxy, hosting) or to the app itself (reading and writing the part).
    logger.info(
        "part upload id=%s index=%s bytes=%s read_s=%.3f write_s=%.3f",
        upload_id[:8], index, len(data), received - started, time.monotonic() - received,
    )
    return JsonResponse({'success': True, 'index': index})
