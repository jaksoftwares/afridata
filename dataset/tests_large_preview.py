"""Large datasets: previews read a bounded sample, and downloads stream."""
import io
import json
from unittest import mock

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import FileResponse
from django.test import TestCase
from django.urls import reverse

from dataset import preview
from dataset.models import Dataset

User = get_user_model()


class LargeDatasetTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="ada", email="ada@example.com", password="pw-test-123", is_verified=True)
        self.client.force_login(self.user)

    def dataset(self, name, dataset_type, content):
        return Dataset.objects.create(
            title=f"Dataset {name}", bio="A dataset used to test large-file previews.", topics="test",
            dataset_type=dataset_type, author=self.user,
            file=SimpleUploadedFile(name, content),
        )

    def big_csv(self, rows):
        body = "region,sales\n" + "".join(f"Row{i},{i}\n" for i in range(rows))
        return body.encode()

    def test_a_large_csv_previews_only_a_sample(self):
        ds = self.dataset("large.csv", "csv", self.big_csv(preview.PREVIEW_ROWS + 3000))
        response = self.client.get(reverse("dataset_preview", args=[ds.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_rows"], preview.PREVIEW_ROWS)
        self.assertTrue(response.context["is_sample"])
        self.assertContains(response, "preview sample of a larger file")

    def test_a_small_csv_is_not_marked_as_a_sample(self):
        ds = self.dataset("small.csv", "csv", self.big_csv(10))
        response = self.client.get(reverse("dataset_preview", args=[ds.slug]))

        self.assertFalse(response.context["is_sample"])
        self.assertEqual(response.context["total_rows"], 10)

    def test_the_detail_chart_says_it_is_based_on_the_sample(self):
        rows = ["region,sales"] + [f"{'East' if i % 2 else 'West'},{i}" for i in range(preview.PREVIEW_ROWS + 500)]
        ds = self.dataset("chart.csv", "csv", ("\n".join(rows) + "\n").encode())
        response = self.client.get(reverse("dataset_detail", args=[ds.slug]))

        self.assertEqual(response.status_code, 200)
        graph = response.context["graph_data"]
        self.assertIsNotNone(graph)
        self.assertIn(f"first {preview.PREVIEW_ROWS:,} rows", graph["insight_label"])

    def test_an_oversized_excel_file_is_refused_with_a_download_message(self):
        buffer = io.BytesIO()
        pd.DataFrame({"a": [1, 2, 3]}).to_excel(buffer, index=False)
        ds = self.dataset("book.xlsx", "excel", buffer.getvalue())
        with mock.patch.object(preview, "MAX_WHOLE_PARSE_BYTES", 10):
            response = self.client.get(reverse("dataset_detail", args=[ds.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertIn("too large to preview", response.context["error_message"])
        self.assertIn("download it", response.context["error_message"])

    def test_an_oversized_json_array_is_refused(self):
        content = json.dumps([{"a": i} for i in range(200)]).encode()
        ds = self.dataset("array.json", "json", content)
        with mock.patch.object(preview, "MAX_WHOLE_PARSE_BYTES", 100):
            response = self.client.get(reverse("dataset_preview", args=[ds.slug]))

        self.assertIn("too large to preview", response.context["error_message"])

    def test_a_large_jsonl_file_previews_only_the_first_rows(self):
        lines = "\n".join(json.dumps({"a": i}) for i in range(preview.PREVIEW_ROWS + 500))
        ds = self.dataset("lines.jsonl", "json", lines.encode())
        with mock.patch.object(preview, "MAX_WHOLE_PARSE_BYTES", 100):
            df, is_sample = preview.read_preview_frame(ds)

        self.assertEqual(len(df), preview.PREVIEW_ROWS)
        self.assertTrue(is_sample)

    def test_download_streams_the_file_rather_than_loading_it(self):
        content = self.big_csv(500)
        ds = self.dataset("download.csv", "csv", content)
        response = self.client.get(reverse("download_dataset", args=[ds.slug]))

        self.assertIsInstance(response, FileResponse)
        self.assertTrue(response.streaming)
        self.assertEqual(b"".join(response.streaming_content), content)
