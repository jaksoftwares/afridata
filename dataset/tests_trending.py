"""Trending: a blend of most-searched and most-recent datasets, and the search log behind it."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dataset import trending
from dataset.models import Dataset, SearchEvent

User = get_user_model()


class TrendingTests(TestCase):

    def setUp(self):
        self.author = User.objects.create_user(username="ada", email="ada@example.com", password="pw-test-123", is_verified=True)

    def dataset(self, title, topics="misc", downloads=0, age_days=0):
        ds = Dataset.objects.create(
            title=title, bio=f"{title} records for research and analysis.", topics=topics,
            dataset_type="csv", author=self.author,
            file=SimpleUploadedFile(f"{title.replace(' ', '_')}.csv", b"a,b\n1,2\n"),
            downloads=downloads,
        )
        # created_at is set by Django on insert; move it back to make an older upload.
        Dataset.objects.filter(pk=ds.pk).update(created_at=timezone.now() - timedelta(days=age_days))
        ds.refresh_from_db()
        return ds

    def search(self, term, times=1, when=None):
        for _ in range(times):
            event = SearchEvent.objects.create(term=term)
            if when is not None:
                SearchEvent.objects.filter(pk=event.pk).update(created_at=when)

    def test_blend_alternates_searched_and_recent(self):
        # Searched datasets are old; recent ones match nothing anyone searched for.
        s1 = self.dataset("Kenya maize yields", topics="agriculture", age_days=30)
        s2 = self.dataset("Kenya rainfall", topics="climate", age_days=20)
        r1 = self.dataset("Ghana tax receipts", age_days=0)
        r2 = self.dataset("Senegal fisheries", age_days=1)
        self.search("kenya", times=5)

        result = trending.trending_datasets(4)
        self.assertEqual(result, [s1, r1, s2, r2])

    def test_no_duplicates_when_a_dataset_is_both_searched_and_recent(self):
        both = self.dataset("Kenya health survey", topics="health", age_days=0)
        other = self.dataset("Nigeria trade", age_days=5)
        self.search("kenya", times=3)

        result = trending.trending_datasets(3)
        pks = [d.pk for d in result]
        self.assertEqual(len(pks), len(set(pks)))
        self.assertIn(both, result)
        self.assertIn(other, result)

    def test_without_searches_the_list_is_the_most_recent_uploads(self):
        old = self.dataset("Old file", age_days=40)
        new = self.dataset("New file", age_days=0)
        self.assertEqual(trending.trending_datasets(2), [new, old])

    def test_with_no_uploads_nothing_is_shown(self):
        self.assertEqual(trending.trending_datasets(3), [])

    def test_fills_with_popular_datasets_when_there_are_few_recent_ones(self):
        popular = self.dataset("Popular archive", downloads=500, age_days=60)
        self.dataset("Only other", age_days=0)
        result = trending.trending_datasets(3)
        self.assertIn(popular, result)
        self.assertEqual(len(result), 2)

    def test_searches_older_than_the_window_do_not_count(self):
        old_term_match = self.dataset("Uganda coffee", age_days=10)
        recent = self.dataset("Brand new upload", age_days=0)
        self.search("uganda", times=50, when=timezone.now() - timedelta(days=30))

        result = trending.trending_datasets(2)
        self.assertEqual(result[0], recent)
        self.assertNotIn(old_term_match, result[:1])

    def test_most_searched_terms_are_ranked_by_count(self):
        self.search("water", times=2)
        self.search("energy", times=5)
        self.assertEqual(trending.top_search_terms()[0], ("energy", 5))


class SearchLoggingTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="grace", email="grace@example.com", password="pw-test-123", is_verified=True)

    def test_a_search_on_the_datasets_page_is_logged(self):
        self.client.get(reverse("dataset_list"), {"search": "  Kenya   Health "})
        self.assertEqual(list(SearchEvent.objects.values_list("term", flat=True)), ["kenya health"])

    def test_the_logged_in_user_is_recorded(self):
        self.client.force_login(self.user)
        self.client.get(reverse("dataset_list"), {"search": "trade"})
        self.assertEqual(SearchEvent.objects.get().user, self.user)

    def test_single_letters_and_empty_searches_are_not_logged(self):
        self.client.get(reverse("dataset_list"), {"search": "a"})
        self.client.get(reverse("dataset_list"), {"search": "   "})
        self.assertFalse(SearchEvent.objects.exists())

    def test_terms_are_capped_in_length(self):
        self.client.get(reverse("dataset_list"), {"search": "x" * 300})
        self.assertEqual(len(SearchEvent.objects.get().term), trending.MAX_TERM_LENGTH)

    def test_searched_terms_come_first_on_the_home_page_list(self):
        trending.log_search("Kenya Agriculture")
        self.assertEqual(trending.top_terms_for_display(["Nigeria GDP", "Kenya Agriculture"])[0], "Kenya Agriculture")
