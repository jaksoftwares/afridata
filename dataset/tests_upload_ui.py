"""
Browser test of the upload page: what the user actually sees while a file uploads.

Runs real Chromium (Playwright) against a live test server, scrolled to the
bottom of the form where the Upload button is. The status overlay must be on
screen there, not at the top of the page.
"""
import os
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from django.urls import reverse

from dataset.models import Dataset

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - Playwright is optional for the normal test run
    sync_playwright = None

User = get_user_model()
CSV_BYTES = b"region,sales\nEast,10\nWest,25\nNorth,5\n"


class UploadUiTests(StaticLiveServerTestCase):

    def setUp(self):
        if sync_playwright is None:
            self.skipTest("Playwright is not installed")
        self.user = User.objects.create_user(
            username="ada", email="ada@example.com", password="pw-test-123", is_verified=True
        )
        # Log in by reusing a Django session, so the browser test doesn't depend on the login form.
        self.client.force_login(self.user)
        self.session_cookie = self.client.cookies["sessionid"].value

    def _browser_page(self, playwright):
        # Talk to the test server directly, never through a system proxy.
        browser = playwright.chromium.launch(args=["--no-proxy-server"])
        context = browser.new_context(viewport={"width": 390, "height": 844})  # a phone screen
        context.add_cookies([{
            "name": "sessionid", "value": self.session_cookie,
            "url": self.live_server_url,
        }])
        page = context.new_page()
        page.set_default_timeout(20000)
        # Wait for the form itself, not for every third-party asset (fonts, icons) to finish.
        page.goto(self.live_server_url + reverse("upload_dataset"), wait_until="domcontentloaded", timeout=120000)
        page.wait_for_selector("#submit-btn")
        return browser, page

    def _fill_form(self, page, dataset_type, file_name, content):
        path = os.path.join(tempfile.mkdtemp(), file_name)
        with open(path, "wb") as fh:
            fh.write(content)
        page.fill("#id_title", "Regional sales")
        page.fill("#id_bio", "Regional sales records for the test upload.")
        page.fill("#id_topics", "sales")
        page.select_option("#id_dataset_type", dataset_type)
        page.set_input_files("#id_file", path)

    # Keep the background metadata analysis out of the browser test.
    @mock.patch("dataset.views.threading")
    def test_progress_and_success_are_visible_when_the_button_is_at_the_bottom(self, _thread):
        with sync_playwright() as p:
            browser, page = self._browser_page(p)
            try:
                self._fill_form(page, "csv", "sales.csv", CSV_BYTES)
                # Scroll to the Upload button, as a user would after filling in the form.
                page.locator("#submit-btn").scroll_into_view_if_needed()
                self.assertGreater(page.evaluate("window.scrollY"), 0)

                page.click("#submit-btn")

                overlay = page.locator("#upload-overlay")
                overlay.wait_for(state="visible", timeout=10000)
                # The overlay is on screen even though the user is at the bottom of the page.
                box = overlay.bounding_box()
                self.assertIsNotNone(box)
                self.assertGreaterEqual(box["y"], 0)
                self.assertLessEqual(box["y"] + box["height"], 844 + 1)
                # A small local file can finish before this check, so accept either panel.
                self.assertTrue(page.locator("#upload-progress").is_visible()
                                or page.locator("#upload-success").is_visible())

                # Ends on the success panel, with the dataset title and a way to open it.
                page.locator("#upload-success").wait_for(state="visible", timeout=30000)
                self.assertIn("Dataset published", page.inner_text("#upload-success"))
                self.assertIn("Regional sales", page.inner_text("#upload-success"))
                self.assertTrue(page.locator("#success-open-link").is_visible())
            finally:
                browser.close()

    @mock.patch("dataset.views.threading")
    def test_validation_failure_is_shown_then_returns_to_the_highlighted_field(self, _thread):
        with sync_playwright() as p:
            browser, page = self._browser_page(p)
            try:
                # CSV content in a file named .json, for the JSON type: the server must refuse it.
                self._fill_form(page, "json", "sales.json", CSV_BYTES)
                page.locator("#submit-btn").scroll_into_view_if_needed()
                page.click("#submit-btn")

                failure = page.locator("#upload-failure")
                failure.wait_for(state="visible", timeout=15000)
                self.assertIn("Please check the form", page.inner_text("#upload-failure"))
                self.assertNotIn("Traceback", page.content())

                page.click("#failure-close-btn")
                self.assertFalse(page.locator("#upload-overlay").is_visible())
                # The user is taken to the field that needs fixing, with the reason beside it.
                self.assertTrue(page.locator("#file-error").is_visible())
                self.assertIn("look like JSON", page.inner_text("#file-error"))
            finally:
                browser.close()


# Parts are forced to a small size so a few hundred KB exercises the chunked path.
CHUNK_CSV = b"region,sales\n" + b"".join(f"Row{i},{i}\n".encode() for i in range(30000))
SMALL_PARTS = {"CHUNKED_UPLOAD_THRESHOLD": 100 * 1024, "CHUNKED_UPLOAD_PART_SIZE": 64 * 1024}


class ChunkedUploadUiTests(UploadUiTests):
    """The same page, for a file large enough to be sent in parts."""

    @override_settings(**SMALL_PARTS)
    @mock.patch("dataset.views.threading", new=mock.MagicMock())
    def test_large_file_is_sent_in_parts_and_saved_intact(self):
        with sync_playwright() as p:
            browser, page = self._browser_page(p)
            try:
                part_puts = []
                page.on("request", lambda r: part_puts.append(r.url) if r.method == "PUT" else None)
                self._fill_form(page, "csv", "big.csv", CHUNK_CSV)
                page.locator("#submit-btn").scroll_into_view_if_needed()
                page.click("#submit-btn")

                page.locator("#upload-success").wait_for(state="visible", timeout=60000)
                self.assertGreaterEqual(len(part_puts), 6)  # about 400 KB in 64 KB parts
            finally:
                browser.close()

        # Database checks run outside the browser block: Playwright's event loop forbids them inside.
        dataset = Dataset.objects.get(title="Regional sales")
        with dataset.file.open("rb") as fh:
            self.assertEqual(fh.read(), CHUNK_CSV)

    @override_settings(**SMALL_PARTS)
    @mock.patch("dataset.views.threading", new=mock.MagicMock())
    def test_a_dropped_part_is_retried_and_the_upload_still_completes(self):
        with sync_playwright() as p:
            browser, page = self._browser_page(p)
            try:
                dropped = {"done": False}

                def drop_the_first_try_of_part_one(route, request):
                    if request.method == "PUT" and request.url.endswith("/1/") and not dropped["done"]:
                        dropped["done"] = True
                        route.abort()  # the connection drops mid-part
                    else:
                        route.continue_()

                page.route("**/dataset/upload/chunks/**", drop_the_first_try_of_part_one)
                self._fill_form(page, "csv", "big.csv", CHUNK_CSV)
                page.locator("#submit-btn").scroll_into_view_if_needed()
                page.click("#submit-btn")

                page.locator("#upload-success").wait_for(state="visible", timeout=60000)
                self.assertTrue(dropped["done"], "the test never dropped a part")
            finally:
                browser.close()

        # Database checks run outside the browser block: Playwright's event loop forbids them inside.
        dataset = Dataset.objects.get(title="Regional sales")
        with dataset.file.open("rb") as fh:
            self.assertEqual(fh.read(), CHUNK_CSV)
