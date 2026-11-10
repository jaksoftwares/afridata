"""Server side of chunked uploads: parts, resume, ownership, completion and cleanup."""
import json
import os
import uuid
from math import ceil
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from dataset.models import Dataset

User = get_user_model()
PART = 64 * 1024
CONTENT = (b"region,sales\n" + b"".join(f"Row{i},{i * 3}\n".encode() for i in range(20000)))
XHR = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


# Keep the background metadata analysis out of these tests (new=... passes no extra argument).
@mock.patch("dataset.views.threading", new=mock.MagicMock())
@override_settings(CHUNKED_UPLOAD_PART_SIZE=PART)
class ChunkedUploadServerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="ada", email="ada@example.com", password="pw-test-123", is_verified=True)
        self.client.force_login(self.user)
        self.upload_id = None

    def tearDown(self):
        from dataset import chunked_upload
        if self.upload_id:
            chunked_upload.discard(self.upload_id)

    def start(self, content=CONTENT, name="sales.csv"):
        response = self.client.post(
            reverse("chunked_upload_start"),
            json.dumps({"filename": name, "size": len(content)}),
            content_type="application/json", **XHR,
        )
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.upload_id = data["upload_id"]
        self.assertEqual(data["total_parts"], ceil(len(content) / PART))
        return data

    def send_part(self, index, content=CONTENT):
        part = content[index * PART:(index + 1) * PART]
        return self.client.put(
            reverse("chunked_upload_part", args=[self.upload_id, index]),
            data=part, content_type="application/octet-stream", **XHR,
        )

    def finish(self, extra=None):
        data = {
            "title": "Regional sales",
            "bio": "Regional sales records sent in parts for the test.",
            "topics": "sales",
            "dataset_type": "csv",
            "upload_id": self.upload_id,
        }
        data.update(extra or {})
        return self.client.post(reverse("upload_dataset"), data, **XHR)

    def test_parts_sent_out_of_order_are_assembled_into_the_exact_file(self):
        meta = self.start()
        order = list(range(meta["total_parts"]))[::-1]  # the last part first
        for index in order:
            self.assertEqual(self.send_part(index).status_code, 200)

        status = self.client.get(reverse("chunked_upload_status", args=[self.upload_id]), **XHR).json()
        self.assertEqual(status["received"], list(range(meta["total_parts"])))

        response = self.finish()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()["success"])

        dataset = Dataset.objects.get(title="Regional sales")
        with dataset.file.open("rb") as fh:
            self.assertEqual(fh.read(), CONTENT)

    def test_resume_only_needs_the_parts_that_are_missing(self):
        meta = self.start()
        total = meta["total_parts"]
        for index in range(total):  # every part except part 2 gets through
            if index != 2:
                self.send_part(index)

        status = self.client.get(reverse("chunked_upload_status", args=[self.upload_id]), **XHR).json()
        self.assertEqual(status["received"], [i for i in range(total) if i != 2])

        response = self.finish()
        self.assertEqual(response.status_code, 400)
        self.assertIn("didn't arrive", response.json()["message"])
        self.assertIn("continue from where it stopped", response.json()["message"])
        self.assertFalse(Dataset.objects.filter(title="Regional sales").exists())

        # Sending the missing part, then finishing, succeeds.
        self.send_part(2)
        final = self.finish()
        self.assertEqual(final.status_code, 200, final.content)

    def test_a_part_of_the_wrong_length_is_refused(self):
        self.start()
        response = self.client.put(
            reverse("chunked_upload_part", args=[self.upload_id, 0]),
            data=b"short", content_type="application/octet-stream", **XHR,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("arrived incomplete", response.json()["message"])

    def test_a_part_number_outside_the_file_is_refused(self):
        meta = self.start()
        response = self.send_part(meta["total_parts"])
        self.assertEqual(response.status_code, 400)
        self.assertIn("doesn't belong", response.json()["message"])

    def test_another_users_upload_cannot_be_used(self):
        self.start()
        other = User.objects.create_user(username="grace", email="grace@example.com", password="pw-test-123", is_verified=True)
        self.client.force_login(other)

        status = self.client.get(reverse("chunked_upload_status", args=[self.upload_id]), **XHR)
        self.assertEqual(status.status_code, 404)
        self.assertIn("could not be found", status.json()["message"])
        self.assertEqual(self.send_part(0).status_code, 404)

    def test_a_made_up_upload_id_is_refused_without_touching_the_disk(self):
        self.upload_id = "../../etc"  # nothing should be looked up outside the staging folder
        response = self.client.get(reverse("chunked_upload_status", args=[uuid.uuid4().hex]), **XHR)
        self.assertEqual(response.status_code, 404)
        from dataset import chunked_upload
        with self.assertRaises(chunked_upload.ChunkedUploadError):
            chunked_upload._dir("../../etc")

    def test_starting_an_empty_or_oversized_file_is_refused(self):
        empty = self.client.post(reverse("chunked_upload_start"), json.dumps({"filename": "a.csv", "size": 0}),
                                 content_type="application/json", **XHR)
        self.assertEqual(empty.status_code, 400)
        self.assertIn("empty", empty.json()["message"])

        with override_settings(MAX_DATASET_UPLOAD_SIZE=1000):
            big = self.client.post(reverse("chunked_upload_start"), json.dumps({"filename": "a.csv", "size": 5000}),
                                   content_type="application/json", **XHR)
        self.assertEqual(big.status_code, 400)
        self.assertIn("too large", big.json()["message"])

    def test_the_staging_files_are_removed_once_the_dataset_is_saved(self):
        self.start()
        for index in range(ceil(len(CONTENT) / PART)):
            self.send_part(index)
        self.assertEqual(self.finish().status_code, 200)

        from dataset import chunked_upload
        folder = chunked_upload._root() / self.upload_id
        self.assertFalse(os.path.exists(folder))
        self.upload_id = None

    def test_a_chunked_upload_still_gets_the_same_validation_as_a_normal_one(self):
        self.start(name="sales.xlsx")  # the .xlsx name doesn't match the CSV type chosen below
        for index in range(ceil(len(CONTENT) / PART)):
            self.send_part(index)
        response = self.finish()
        self.assertEqual(response.status_code, 400)  # the form rejects a .xlsx named file for the CSV type
        self.assertFalse(response.json()["success"])
        self.assertIn("__all__", response.json()["errors"])  # the extension check is a form-wide error
