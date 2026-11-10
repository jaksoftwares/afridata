"""
Trending datasets: a blend of what people search for and what was uploaded recently.

Each trending list alternates between two sources, so neither dominates:
  * most searched: datasets matching the terms people searched for in the last 7 days,
    ranked by how often those terms were searched, then by downloads.
  * recent uploads: the newest datasets.
Duplicates are removed. If there aren't enough of either, the list is filled with
the most downloaded datasets, so a new site still shows something useful.
"""
from datetime import timedelta
from itertools import zip_longest

from django.db.models import Count, Q
from django.utils import timezone

from .models import Dataset, SearchEvent

SEARCH_WINDOW = timedelta(days=7)
TERMS_CONSIDERED = 8
MIN_TERM_LENGTH = 2
MAX_TERM_LENGTH = 100


def normalise_term(raw: str) -> str:
    """Lower-case, single spaces, trimmed and length-limited. Empty string if not worth logging."""
    term = " ".join((raw or "").lower().split())[:MAX_TERM_LENGTH]
    return term if len(term) >= MIN_TERM_LENGTH else ""


def log_search(raw: str, user=None) -> None:
    term = normalise_term(raw)
    if term:
        SearchEvent.objects.create(term=term, user=user if getattr(user, "is_authenticated", False) else None)


def top_search_terms(limit: int = TERMS_CONSIDERED):
    """[(term, count)] for the most searched terms in the window, most searched first."""
    since = timezone.now() - SEARCH_WINDOW
    rows = (
        SearchEvent.objects.filter(created_at__gte=since)
        .values("term")
        .annotate(count=Count("id"))
        .order_by("-count", "term")[:limit]
    )
    return [(row["term"], row["count"]) for row in rows]


def most_searched(limit: int):
    terms = top_search_terms()
    if not terms:
        return []
    weight = dict(terms)
    match = Q()
    for term in weight:
        match |= Q(title__icontains=term) | Q(topics__icontains=term) | Q(bio__icontains=term)

    candidates = list(Dataset.objects.select_related("author").filter(match)[: limit * 10])

    def score(dataset):
        text = f"{dataset.title} {dataset.topics} {dataset.bio}".lower()
        matched = sum(count for term, count in weight.items() if term in text)
        return (matched, dataset.downloads, dataset.views)

    candidates.sort(key=score, reverse=True)
    return candidates[:limit]


def recent_uploads(limit: int):
    return list(Dataset.objects.select_related("author").order_by("-created_at")[:limit])


def trending_datasets(limit: int = 3):
    """A blend of most searched and most recent, with no duplicates."""
    searched = most_searched(limit)
    recent = recent_uploads(limit)

    result, seen = [], set()

    def add(dataset):
        if dataset is not None and dataset.pk not in seen:
            seen.add(dataset.pk)
            result.append(dataset)
        return len(result) >= limit

    for searched_item, recent_item in zip_longest(searched, recent):
        if add(searched_item) or add(recent_item):
            return result[:limit]

    if len(result) < limit:
        for dataset in Dataset.objects.select_related("author").exclude(pk__in=seen).order_by("-downloads", "-views")[: limit - len(result)]:
            add(dataset)
    return result[:limit]


def top_terms_for_display(fallback, limit: int = 5):
    """Searched terms first (title case), then the given fallback terms to fill the list."""
    searched = [term.title() for term, _ in top_search_terms(limit)]
    filled = searched + [term for term in fallback if term not in searched]
    return filled[:limit]
