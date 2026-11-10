"""
End-to-end tests for JSON and JSON Lines (JSONL) datasets:
reader, upload validation, metadata loader, and the preview page.
"""
import json
import os
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from dataset.forms import DatasetUploadForm
from dataset.models import Dataset
from pipeline_lib.json_reader import (
    JsonReadError,
    check_json_head,
    read_json_frame,
    read_json_records,
)

ROWS = [
    {"region": "East", "sales": 10, "address": {"city": "Nairobi"}},
    {"region": "West", "sales": 25, "address": {"city": "Kisumu"}},
]


class ReadJsonRecordsTests(TestCase):
    def test_json_array(self):
        content = json.dumps(ROWS).encode()
        self.assertEqual(read_json_records(content), ROWS)

    def test_single_object_is_one_record(self):
        content = json.dumps(ROWS[0]).encode()
        self.assertEqual(read_json_records(content), [ROWS[0]])

    def test_object_wrapping_a_list_of_records(self):
        content = json.dumps({"meta": {"v": 1}, "results": ROWS}).encode()
        self.assertEqual(read_json_records(content), ROWS)

    def test_jsonl(self):
        content = "\n".join(json.dumps(r) for r in ROWS).encode()
        self.assertEqual(read_json_records(content), ROWS)

    def test_jsonl_with_blank_lines_and_trailing_newline(self):
        content = ("\n" + json.dumps(ROWS[0]) + "\n\n" + json.dumps(ROWS[1]) + "\n\n").encode()
        self.assertEqual(read_json_records(content), ROWS)

    def test_jsonl_starting_with_leading_whitespace(self):
        # A regression: this used to be sent to the NDJSON reader and crash.
        content = ("   \n" + "\n".join(json.dumps(r) for r in ROWS)).encode()
        self.assertEqual(read_json_records(content), ROWS)

    def test_utf8_bom(self):
        content = b"\xef\xbb\xbf" + json.dumps(ROWS).encode()
        self.assertEqual(read_json_records(content), ROWS)

    def test_scalar_items_become_value_column(self):
        df = read_json_frame(b"[1, 2, 3]")
        self.assertEqual(list(df.columns), ["value"])
        self.assertEqual(df["value"].tolist(), [1, 2, 3])

    def test_bad_jsonl_line_reports_line_number(self):
        content = (json.dumps(ROWS[0]) + "\n{not json}\n").encode()
        with self.assertRaisesMessage(JsonReadError, "Line 2 is not valid JSON"):
            read_json_records(content)

    def test_empty_file(self):
        with self.assertRaisesMessage(JsonReadError, "empty"):
            read_json_records(b"  \n ")

    def test_no_records(self):
        with self.assertRaisesMessage(JsonReadError, "no records"):
            read_json_records(b"[]")


class ReadJsonFrameTests(TestCase):
    def test_nested_objects_are_flattened(self):
        df = read_json_frame(json.dumps(ROWS).encode())
        self.assertIn("address.city", df.columns)
        self.assertEqual(df["address.city"].tolist(), ["Nairobi", "Kisumu"])

    def test_list_cells_become_text_so_group_by_works(self):
        rows = [{"k": "a", "tags": ["x", "y"]}, {"k": "b", "tags": []}]
        df = read_json_frame(json.dumps(rows).encode())
        self.assertEqual(df["tags"].tolist(), ['["x", "y"]', "[]"])
        # Hashable now, so this must not raise:
        self.assertEqual(df.groupby("tags").size().shape[0], 2)

    def test_jsonl_and_array_give_the_same_table(self):
        array_df = read_json_frame(json.dumps(ROWS).encode())
        jsonl_df = read_json_frame("\n".join(json.dumps(r) for r in ROWS).encode())
        self.assertTrue(array_df.equals(jsonl_df))


class CheckJsonHeadTests(TestCase):
    def test_accepts_json_and_jsonl_starts(self):
        self.assertIsNone(check_json_head(b'[{"a": 1}]'))
        self.assertIsNone(check_json_head(b'{"a": 1}\n{"a": 2}'))

    def test_rejects_csv_content(self):
        self.assertIn("doesn't look like JSON", check_json_head(b"name,age\nAda,30\n"))

    def test_rejects_empty(self):
        self.assertEqual(check_json_head(b"  \n"), "The file is empty.")


class LoaderTests(TestCase):
    """The standardiser's polars loader must read both layouts."""

    def _load(self, content: bytes, suffix: str):
        from pipeline_lib.loader import load_json

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            path = tmp.name
        try:
            return load_json(path)
        finally:
            os.unlink(path)

    def test_jsonl_loads_as_text_columns(self):
        content = "\n".join(json.dumps(r) for r in ROWS).encode()
        df = self._load(content, ".jsonl")
        self.assertEqual(df.height, 2)
        self.assertEqual(df["region"].to_list(), ["East", "West"])
        self.assertEqual(df["sales"].to_list(), ["10", "25"])

    def test_json_array_loads(self):
        df = self._load(json.dumps(ROWS).encode(), ".json")
        self.assertEqual(df.height, 2)
        self.assertIn("address.city", df.columns)


class UploadFormTests(TestCase):
    def _form(self, name, content, dataset_type="json"):
        upload = SimpleUploadedFile(name, content, content_type="application/octet-stream")
        return DatasetUploadForm(
            data={
                "title": "Sales figures",
                "bio": "A sample dataset used for testing the upload form.",
                "topics": "sales",
                "dataset_type": dataset_type,
            },
            files={"file": upload},
        )

    def test_jsonl_upload_is_accepted_for_json_type(self):
        form = self._form("sales.jsonl", "\n".join(json.dumps(r) for r in ROWS).encode())
        self.assertTrue(form.is_valid(), form.errors)

    def test_csv_renamed_to_json_is_refused(self):
        form = self._form("sales.json", b"region,sales\nEast,10\n")
        self.assertFalse(form.is_valid())
        self.assertIn("look like JSON", str(form.errors["file"]))

    def test_unsupported_extension_for_json_type_is_refused(self):
        form = self._form("sales.csv", json.dumps(ROWS).encode())
        self.assertFalse(form.is_valid())


class UploadViewTests(TestCase):
    """POST a JSONL file through the upload endpoint, as the page's XHR does."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="grace", email="grace@example.com", password="pw-test-123"
        )
        self.client.force_login(self.user)

    def test_jsonl_upload_succeeds_and_queues_metadata_analysis(self):
        from unittest import mock

        content = "\n".join(json.dumps(r) for r in ROWS).encode()
        upload = SimpleUploadedFile("sales.jsonl", content)
        with mock.patch("dataset.views.threading.Thread") as thread_cls:
            response = self.client.post(
                reverse("upload_dataset"),
                {
                    "title": "Regional sales",
                    "bio": "Regional sales records loaded from newline-delimited JSON.",
                    "topics": "sales, regions",
                    "dataset_type": "json",
                    "file": upload,
                },
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )

        payload = response.json()
        self.assertTrue(payload["success"], payload)
        self.assertEqual(payload["dataset_title"], "Regional sales")
        self.assertTrue(payload["metadata_queued"])
        thread_cls.assert_called_once()
        # The analysis is queued with the JSON source, not CSV.
        run_kwargs = thread_cls.call_args.kwargs["kwargs"]
        self.assertEqual(run_kwargs["source"], "json")

        ds = Dataset.objects.get(title="Regional sales")
        self.assertEqual(ds.dataset_type, "json")
        self.assertTrue(ds.file.name.endswith(".jsonl"))

    def test_invalid_json_upload_returns_field_error(self):
        upload = SimpleUploadedFile("sales.json", b"region,sales\nEast,10\n")
        response = self.client.post(
            reverse("upload_dataset"),
            {
                "title": "Not really JSON",
                "bio": "This file is CSV content with a .json name.",
                "topics": "sales",
                "dataset_type": "json",
                "file": upload,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.json()["errors"])
        self.assertFalse(Dataset.objects.filter(title="Not really JSON").exists())


class PreviewPageTests(TestCase):
    """Uploaded JSON / JSONL files render a preview, not an error."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="ada", email="ada@example.com", password="pw-test-123"
        )

    def _dataset(self, name, content):
        return Dataset.objects.create(
            title=f"Dataset {name}",
            bio="Test dataset for the JSON preview page.",
            topics="test",
            dataset_type="json",
            author=self.user,
            file=SimpleUploadedFile(name, content),
        )

    def test_jsonl_preview_shows_rows_and_columns(self):
        content = "\n".join(json.dumps(r) for r in ROWS).encode()
        ds = self._dataset("preview.jsonl", content)
        response = self.client.get(reverse("dataset_preview", args=[ds.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get("error_message"))
        self.assertEqual(response.context["total_rows"], 2)
        self.assertIn("address.city", response.context["columns"])

    def test_jsonl_detail_page_builds_chart_from_the_data(self):
        rows = [
            {"region": "East", "sales": 10},
            {"region": "East", "sales": 30},
            {"region": "West", "sales": 25},
            {"region": "North", "sales": 5},
        ]
        content = "\n".join(json.dumps(r) for r in rows).encode()
        ds = self._dataset("chart.jsonl", content)
        response = self.client.get(reverse("dataset_detail", args=[ds.slug]))
        self.assertEqual(response.status_code, 200)
        graph = response.context["graph_data"]
        self.assertIsNotNone(graph)
        # Categories come from the data, and the values are the group averages.
        self.assertEqual(sorted(graph["raw_labels"]), ["East", "North", "West"])
        values = {label: data for label, data in zip(graph["raw_labels"], graph["raw_datasets"][0]["data"])}
        self.assertEqual(values["East"], 20.0)

    def test_malformed_jsonl_preview_shows_the_reason(self):
        ds = self._dataset("broken.jsonl", b'{"a": 1}\n{oops}\n')
        response = self.client.get(reverse("dataset_preview", args=[ds.slug]))
        self.assertIn("Line 2 is not valid JSON", response.context["error_message"])
