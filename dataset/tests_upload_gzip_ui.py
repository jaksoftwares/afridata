"""Browser test: a text upload is compressed in the browser, so far fewer bytes are sent."""
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
class GzipUploadUiTests(StaticLiveServerTestCase):

    def setUp(self):
        if sync_playwright is None:
            self.skipTest("Playwright is not installed")
        self.user = User.objects.create_user(username="ada", email="ada@example.com", password="pw-test-123", is_verified=True)
        self.client.force_login(self.user)
        self.session_cookie = self.client.cookies["sessionid"].value

    @mock.patch("dataset.views.threading", new=mock.MagicMock())
    def test_csv_is_compressed_in_the_browser_and_saved_intact(self):
        sent = []
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-proxy-server"])
            try:
                context = browser.new_context(viewport={"width": 390, "height": 844})
                context.add_cookies([{"name": "sessionid", "value": self.session_cookie, "url": self.live_server_url}])
                page = context.new_page()
                page.set_default_timeout(20000)
                page.goto(self.live_server_url + reverse("upload_dataset"), wait_until="domcontentloaded", timeout=120000)
                page.wait_for_selector("#submit-btn")

                page.on("request", lambda r: sent.append(len(r.post_data_buffer or b"")) if r.method == "PUT" else None)
                path = os.path.join(tempfile.mkdtemp(), "sales.csv")
                with open(path, "wb") as fh:
                    fh.write(CSV)
                page.fill("#id_title", "Regional sales")
                page.fill("#id_bio", "Regional sales records for the compression test.")
                page.fill("#id_topics", "sales")
                page.select_option("#id_dataset_type", "csv")
                page.set_input_files("#id_file", path)
                page.click("#submit-btn")

                page.locator("#upload-success").wait_for(state="visible", timeout=60000)
            finally:
                browser.close()

        # Database checks happen outside the browser block (Playwright forbids them inside).
        self.assertTrue(sent, "no parts were sent")
        self.assertLess(sum(sent), len(CSV) // 2, f"sent {sum(sent)} bytes for a {len(CSV)} byte file")
        dataset = Dataset.objects.get(title="Regional sales")
        with dataset.file.open("rb") as fh:
            self.assertEqual(fh.read(), CSV)
