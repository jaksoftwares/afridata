"""The datasets page: every filter changes the results, and live refresh returns only the results area."""
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from dataset.models import Dataset

User = get_user_model()
XHR = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


class DatasetListFilterTests(TestCase):

    def setUp(self):
        self.author = User.objects.create_user(username="ada", email="ada@example.com", password="pw-test-123", is_verified=True)
        self.csv_cc = self.make("Maize yields", "csv", "Creative Commons Attribution", 2.0, 4.5, "agriculture")
        self.json_gpl = self.make("Clinic visits", "json", "GPL", 80.0, 3.0, "healthcare")
        self.xlsx_odb = self.make("Budget lines", "excel", "Open Database License", 15.0, 0.0, "finance")

    def make(self, title, dtype, licence, size_mb, rating, topic):
        ds = Dataset.objects.create(
            title=title, bio=f"{title} for research.", topics=topic, dataset_type=dtype,
            author=self.author, dataset_license=licence, rating=rating,
            file=SimpleUploadedFile(f"{title.replace(' ', '_')}.{dtype}", b"a,b\n1,2\n"),
        )
        Dataset.objects.filter(pk=ds.pk).update(file_size_mb=size_mb)
        return ds

    def titles(self, params=None, headers=None):
        response = self.client.get(reverse("dataset_list"), params or {}, **(headers or {}))
        self.assertEqual(response.status_code, 200)
        return sorted(d["title"] for d in response.context["datasets"]), response

    def test_all_datasets_shown_with_no_filters(self):
        titles, _ = self.titles()
        self.assertEqual(titles, ["Budget lines", "Clinic visits", "Maize yields"])

    def test_several_formats_can_be_ticked(self):
        titles, _ = self.titles({"format": ["csv", "excel"]})
        self.assertEqual(titles, ["Budget lines", "Maize yields"])

    def test_licence_filter(self):
        titles, _ = self.titles({"license": ["gpl", "odb"]})
        self.assertEqual(titles, ["Budget lines", "Clinic visits"])

    def test_size_range_filter(self):
        titles, _ = self.titles({"min_size": "10", "max_size": "100"})
        self.assertEqual(titles, ["Budget lines", "Clinic visits"])

    def test_minimum_rating_filter(self):
        titles, _ = self.titles({"min_rating": "4"})
        self.assertEqual(titles, ["Maize yields"])

    def test_bad_numbers_are_ignored_not_crashed_on(self):
        titles, _ = self.titles({"min_size": "lots", "min_rating": "high", "format": ["bogus"]})
        self.assertEqual(len(titles), 3)

    def test_trending_category_uses_the_blended_list(self):
        titles, _ = self.titles({"category": "trending"})
        self.assertEqual(len(titles), 3)  # everything is recent here, so all three qualify

    def test_topic_category(self):
        titles, _ = self.titles({"category": "healthcare"})
        self.assertEqual(titles, ["Clinic visits"])

    def test_filters_combine(self):
        titles, _ = self.titles({"format": ["csv", "json"], "min_rating": "4"})
        self.assertEqual(titles, ["Maize yields"])

    def test_active_filters_are_listed_for_removal(self):
        _, response = self.titles({"format": ["csv"], "min_rating": "3"})
        labels = [f["label"] for f in response.context["active_filters"]]
        self.assertIn("CSV", labels)
        self.assertIn("Rating 3+", labels)

    def test_live_refresh_returns_only_the_results_region(self):
        response = self.client.get(reverse("dataset_list"), {"search": "clinic"}, **XHR)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn('id="resultsRegion"', body)
        self.assertNotIn("<html", body.lower())
        self.assertNotIn('id="filterForm"', body)

    def test_full_page_load_still_renders_the_whole_page(self):
        body = self.client.get(reverse("dataset_list")).content.decode()
        self.assertIn('id="filterForm"', body)
        self.assertIn('id="resultsRegion"', body)

    def test_pagination_keeps_the_other_filters(self):
        for i in range(14):
            self.make(f"Extra {i}", "csv", "GPL", 1.0, 0.0, "misc")
        body = self.client.get(reverse("dataset_list"), {"format": "csv"}).content.decode()
        self.assertIn("format=csv", body)
        self.assertIn("page=2", body)

    def test_no_results_shows_a_clear_message(self):
        body = self.client.get(reverse("dataset_list"), {"search": "zzz-nothing-matches"}).content.decode()
        self.assertIn("No datasets match these filters", body)
