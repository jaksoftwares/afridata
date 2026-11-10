"""Browser test: a part that silently stops responding is abandoned and sent again."""
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
except ImportError:  # pragma: no cover
    sync_playwright = None

User = get_user_model()
CSV = b"region,sales\n" + b"".join(f"Row{i},{i}\n".encode() for i in range(30000))
SMALL_PARTS = {"CHUNKED_UPLOAD_THRESHOLD": 100 * 1024, "CHUNKED_UPLOAD_PART_SIZE": 64 * 1024}


@override_settings(**SMALL_PARTS)
class StalledPartUiTests(StaticLiveServerTestCase):

    def setUp(self):
        if sync_playwright is None:
            self.skipTest("Playwright is not installed")
        self.user = User.objects.create_user(username="ada", email="ada@example.com", password="pw-test-123", is_verified=True)
        self.client.force_login(self.user)
        self.session_cookie = self.client.cookies["sessionid"].value

    @mock.patch("dataset.views.threading", new=mock.MagicMock())
    def test_a_stuck_part_is_retried_and_the_file_still_saves_intact(self):
        held = {"count": 0}

        def hold_first_try_of_part_two(route, request):
            # The first attempt at part 2 never gets an answer, like a stalled connection.
            if request.method == "PUT" and request.url.endswith("/2/") and held["count"] == 0:
                held["count"] += 1
                return  # no response: the uploader's stall watchdog must give up on it
            route.continue_()

        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-proxy-server"])
            try:
                context = browser.new_context(viewport={"width": 390, "height": 844})
                context.add_cookies([{"name": "sessionid", "value": self.session_cookie, "url": self.live_server_url}])
                page = context.new_page()
                page.set_default_timeout(20000)
                page.goto(self.live_server_url + reverse("upload_dataset"), wait_until="domcontentloaded", timeout=120000)
                page.wait_for_selector("#submit-btn")
                page.route("**/dataset/upload/chunks/**", hold_first_try_of_part_two)

                path = os.path.join(tempfile.mkdtemp(), "sales.csv")
                with open(path, "wb") as fh:
                    fh.write(CSV)
                page.fill("#id_title", "Regional sales")
                page.fill("#id_bio", "Regional sales records for the stall test.")
                page.fill("#id_topics", "sales")
                page.select_option("#id_dataset_type", "csv")
                page.set_input_files("#id_file", path)
                page.click("#submit-btn")

                # The stall window is 30 s; allow the retry and the save after it.
                page.locator("#upload-success").wait_for(state="visible", timeout=150000)
            finally:
                browser.close()

        self.assertEqual(held["count"], 1, "the stalled part was never held")
        dataset = Dataset.objects.get(title="Regional sales")
        with dataset.file.open("rb") as fh:
            self.assertEqual(fh.read(), CSV)
