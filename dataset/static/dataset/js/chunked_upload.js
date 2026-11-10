/*
 * Resumable, parallel upload of one large file, in parts.
 *
 * Several parts are sent at once. A part that fails with a dropped connection
 * or a server error is retried with a growing pause. The upload id is kept for
 * this browser tab, so reloading the page continues the same upload rather than
 * starting again. The server already holds the parts that arrived.
 *
 * Exposes window.ChunkedUpload:
 *   upload(file, options) -> Promise<uploadId>
 *     options.startUrl            POST endpoint that begins an upload
 *     options.statusUrl(id)       GET endpoint listing the parts that arrived
 *     options.partUrl(id, index)  PUT endpoint for one part
 *     options.onProgress(loaded, total)
 *     options.signal              AbortSignal, to cancel (parts already sent are kept)
 *   forget(file)                  forget the remembered upload id (after a successful save)
 */
(function (global) {
    'use strict';

    const MAX_PARALLEL = 4;
    // Text formats compress well in the browser; binary formats (Excel, Parquet, ZIP) don't.
    const COMPRESSIBLE = /\.(csv|tsv|txt|json|jsonl|ndjson|xml|ya?ml)$/i;
    const MAX_ATTEMPTS = 5;
    const STORE_PREFIX = 'afridata-upload:';

    // An error whose message is written for the user. `retryable` marks problems
    // that a second try may fix (a dropped connection, a server restart).
    class UploadProblem extends Error {
        constructor(message, retryable) {
            super(message);
            this.name = 'UploadProblem';
            this.retryable = !!retryable;
        }
    }

    function abortError() {
        return new DOMException('Upload cancelled', 'AbortError');
    }

    function isAbort(err) {
        return err && err.name === 'AbortError';
    }

    function csrfToken() {
        const el = document.querySelector('[name=csrfmiddlewaretoken]');
        return el ? el.value : '';
    }

    function messageFor(status) {
        if (status === 0) return 'The connection was lost.';
        if (status === 413) return 'A part of the file was too large to send.';
        if (status >= 500) return "The server couldn't receive the file right now.";
        return "The file couldn't be sent. Please try again.";
    }

    // Keyed by name, size and date, so a different file never picks up an old upload id.
    function storeKey(file) {
        return STORE_PREFIX + [file.name, file.size, file.lastModified].join(':');
    }

    function remember(file, uploadId) {
        try { sessionStorage.setItem(storeKey(file), uploadId); } catch (e) { /* private mode: no resume */ }
    }

    function recall(file) {
        try { return sessionStorage.getItem(storeKey(file)); } catch (e) { return null; }
    }

    function forget(file) {
        try { sessionStorage.removeItem(storeKey(file)); } catch (e) { /* nothing to clear */ }
    }

    async function readJson(response) {
        let data = null;
        try { data = await response.json(); } catch (e) { data = null; }
        if (!response.ok || !data || data.success === false) {
            const retryable = response.status === 0 || response.status >= 500;
            throw new UploadProblem((data && data.message) || messageFor(response.status), retryable);
        }
        return data;
    }

    function getJson(url, signal) {
        return fetch(url, {
            method: 'GET',
            credentials: 'same-origin',
            signal: signal,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        }).then(readJson, networkFailure);
    }

    function postJson(url, body, signal) {
        return fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            signal: signal,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify(body),
        }).then(readJson, networkFailure);
    }

    function networkFailure(err) {
        if (isAbort(err)) throw err;
        throw new UploadProblem(messageFor(0), true);
    }

    // Send one part. Reports the bytes sent so far. Resolves once the server has the part.
    function sendPart(url, blob, signal, onBytes) {
        return new Promise(function (resolve, reject) {
            const xhr = new XMLHttpRequest();
            xhr.open('PUT', url);
            xhr.setRequestHeader('X-CSRFToken', csrfToken());
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.setRequestHeader('Content-Type', 'application/octet-stream');
            xhr.upload.onprogress = function (e) {
                if (e.lengthComputable) onBytes(e.loaded);
            };
            xhr.onload = function () {
                let data = null;
                try { data = JSON.parse(xhr.responseText); } catch (e) { data = null; }
                if (xhr.status === 200 && data && data.success) {
                    resolve();
                } else {
                    const retryable = xhr.status === 0 || xhr.status >= 500;
                    reject(new UploadProblem((data && data.message) || messageFor(xhr.status), retryable));
                }
            };
            xhr.onerror = function () { reject(new UploadProblem(messageFor(0), true)); };
            xhr.onabort = function () { reject(abortError()); };
            if (signal) {
                if (signal.aborted) { xhr.abort(); return; }
                signal.addEventListener('abort', function () { xhr.abort(); }, { once: true });
            }
            xhr.send(blob);
        });
    }

    // Compress one part as its own gzip member, so the server can rebuild the file part by part.
    async function gzipBlob(blob) {
        const compressed = blob.stream().pipeThrough(new CompressionStream('gzip'));
        return new Response(compressed).blob();
    }

    function wait(ms, signal) {
        return new Promise(function (resolve, reject) {
            if (signal && signal.aborted) { reject(abortError()); return; }
            const timer = setTimeout(resolve, ms);
            if (signal) {
                signal.addEventListener('abort', function () {
                    clearTimeout(timer);
                    reject(abortError());
                }, { once: true });
            }
        });
    }

    async function upload(file, options) {
        const signal = options.signal;

        // Resume an earlier attempt at this same file, if this tab has one.
        let uploadId = recall(file);
        let info = null;
        if (uploadId) {
            try {
                info = await getJson(options.statusUrl(uploadId), signal);
            } catch (err) {
                if (isAbort(err)) throw err;
                uploadId = null; // the server no longer has it: start again
            }
        }
        if (!uploadId) {
            const wantGzip = typeof CompressionStream === 'function' && COMPRESSIBLE.test(file.name);
            info = await postJson(
                options.startUrl,
                { filename: file.name, size: file.size, encoding: wantGzip ? 'gzip' : 'raw' },
                signal
            );
            uploadId = info.upload_id;
            remember(file, uploadId);
        }

        const partSize = info.part_size;
        const gzip = info.encoding === 'gzip';
        const total = info.total_parts;
        const arrived = new Set(info.received);
        const partBytes = function (index) {
            return Math.min(partSize, file.size - index * partSize);
        };

        // Progress counts finished parts, plus whatever the parts in flight have sent so far.
        const inFlight = new Map();
        let finished = 0;
        arrived.forEach(function (index) { finished += partBytes(index); });
        function report() {
            let loaded = finished;
            inFlight.forEach(function (bytes) { loaded += bytes; });
            options.onProgress(Math.min(loaded, file.size), file.size);
        }
        report();

        const pending = [];
        for (let i = 0; i < total; i++) {
            if (!arrived.has(i)) pending.push(i);
        }

        // A failure in one part stops the others, so the user isn't left with half-sent work.
        const stop = new AbortController();
        if (signal) signal.addEventListener('abort', function () { stop.abort(); }, { once: true });

        async function sendOne(index) {
            const blob = file.slice(index * partSize, index * partSize + partBytes(index));
            // Compress once, so a retry doesn't compress the part again.
            const body = gzip ? await gzipBlob(blob) : blob;
            // Progress counts the original file's bytes, so the speed and time left are real
            // for the user. Bytes actually sent are scaled to match.
            const ratio = body.size ? blob.size / body.size : 1;
            for (let attempt = 1; ; attempt++) {
                inFlight.set(index, 0);
                report();
                try {
                    await sendPart(options.partUrl(uploadId, index), body, stop.signal, function (bytes) {
                        inFlight.set(index, bytes * ratio);
                        report();
                    });
                    inFlight.delete(index);
                    finished += partBytes(index);
                    report();
                    return;
                } catch (err) {
                    inFlight.delete(index);
                    report();
                    if (isAbort(err)) throw err;
                    if (!err.retryable) throw err;
                    if (attempt >= MAX_ATTEMPTS) {
                        throw new UploadProblem(
                            'The connection keeps dropping. Your progress is saved: press Upload again to continue.',
                            true
                        );
                    }
                    await wait(Math.min(1000 * Math.pow(2, attempt - 1), 15000), stop.signal);
                }
            }
        }

        let next = 0;
        async function worker() {
            while (next < pending.length) {
                const index = pending[next++];
                try {
                    await sendOne(index);
                } catch (err) {
                    stop.abort();
                    throw err;
                }
            }
        }

        const workers = [];
        for (let w = 0; w < Math.min(MAX_PARALLEL, pending.length); w++) workers.push(worker());
        await Promise.all(workers);
        report();
        return uploadId;
    }

    global.ChunkedUpload = {
        upload: upload,
        forget: forget,
        UploadProblem: UploadProblem,
    };
})(window);
