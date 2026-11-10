"""Compressed (gzip) chunked uploads: part by part, damaged parts, and cleanup."""
import gzip
import json
import os
from math import ceil
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from dataset.models import Dataset

User = get_user_model()
PART = 64 * 1024
CONTENT = b"region,sales\n" + b"".join(f"Row{i},{i * 3}\n".encode() for i in range(20000))
XHR = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


def compressed_parts(content=CONTENT, part=PART):
    """Each part as its own gzip member, the way the browser sends them."""
    return [gzip.compress(content[i:i + part]) for i in range(0, len(content), part)]


@mock.patch("dataset.views.threading", new=mock.MagicMock())
@override_settings(CHUNKED_UPLOAD_PART_SIZE=PART)
class GzipChunkedUploadTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="ada", email="ada@example.com", password="pw-test-123", is_verified=True)
        self.client.force_login(self.user)
        self.upload_id = None

    def tearDown(self):
        from dataset import chunked_upload
        if self.upload_id:
            chunked_upload.discard(self.upload_id)

    def start(self, content=CONTENT):
        response = self.client.post(
            reverse("chunked_upload_start"),
            json.dumps({"filename": "sales.csv", "size": len(content), "encoding": "gzip"}),
            content_type="application/json", **XHR,
        )
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(data["encoding"], "gzip")
        self.upload_id = data["upload_id"]
        return data

    def put(self, index, body):
        return self.client.put(
            reverse("chunked_upload_part", args=[self.upload_id, index]),
            data=body, content_type="application/octet-stream", **XHR,
        )

    def finish(self):
        return self.client.post(reverse("upload_dataset"), {
            "title": "Regional sales",
            "bio": "Regional sales records sent compressed, in parts, for the test.",
            "topics": "sales",
            "dataset_type": "csv",
            "upload_id": self.upload_id,
        }, **XHR)

    def test_compressed_parts_sent_out_of_order_rebuild_the_exact_file(self):
        self.start()
        parts = compressed_parts()
        for index in reversed(range(len(parts))):
            self.assertEqual(self.put(index, parts[index]).status_code, 200)

        response = self.finish()
        self.assertEqual(response.status_code, 200, response.content)
        dataset = Dataset.objects.get(title="Regional sales")
        with dataset.file.open("rb") as fh:
            self.assertEqual(fh.read(), CONTENT)

    def test_far_fewer_bytes_are_sent_than_the_file_holds(self):
        self.start()
        parts = compressed_parts()
        sent = sum(len(p) for p in parts)
        self.assertLess(sent, len(CONTENT) // 2, "CSV text should compress to well under half")

    def test_a_damaged_part_is_named_and_sent_again(self):
        self.start()
        parts = compressed_parts()
        for index, body in enumerate(parts):
            if index == 2:
                body = body[:10] + b"\x00" * (len(body) - 10)  # starts like gzip, then breaks
            self.assertEqual(self.put(index, body).status_code, 200)

        response = self.finish()
        self.assertEqual(response.status_code, 400)
        self.assertIn("damaged in transit", response.json()["message"])

        # Only the damaged part is missing now, so sending it again completes the upload.
        status = self.client.get(reverse("chunked_upload_status", args=[self.upload_id]), **XHR).json()
        self.assertNotIn(2, status["received"])
        self.assertEqual(self.put(2, parts[2]).status_code, 200)
        self.assertEqual(self.finish().status_code, 200)

    def test_a_part_that_is_not_gzip_is_refused_at_once(self):
        self.start()
        response = self.put(0, b"plain text, not compressed")
        self.assertEqual(response.status_code, 400)
        self.assertIn("damaged", response.json()["message"])

    def test_a_part_far_larger_than_expected_is_refused(self):
        self.start()
        oversized = gzip.compress(os.urandom(PART * 3))  # random data doesn't compress
        response = self.put(0, oversized)
        self.assertIn(response.status_code, (400, 413))

    def test_staging_is_removed_after_the_dataset_is_saved(self):
        self.start()
        for index, body in enumerate(compressed_parts()):
            self.put(index, body)
        self.assertEqual(self.finish().status_code, 200)

        from dataset import chunked_upload
        self.assertFalse(os.path.exists(chunked_upload._root() / self.upload_id))
        self.upload_id = None

    def test_resuming_a_compressed_upload_reports_its_encoding(self):
        self.start()
        status = self.client.get(reverse("chunked_upload_status", args=[self.upload_id]), **XHR).json()
        self.assertEqual(status["encoding"], "gzip")
        self.assertEqual(status["total_parts"], ceil(len(CONTENT) / PART))
