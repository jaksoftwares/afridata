"""
Users see plain-language errors. Developer details (exception text, tracebacks,
internal names) never reach the page.
"""
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.test import Client
from django.views.defaults import server_error

from afridata.user_errors import USER_MESSAGES
from dataset.models import Dataset

User = get_user_model()
SECRET = "db-password-hunter2-SECRET"


def assert_no_developer_detail(test, body):
    for leak in ("Traceback", "Exception", "Error at", "File \"", "SECRET", "hunter2", "django.", "pandas", "Expecting"):
        test.assertNotIn(leak, body, f"developer detail leaked: {leak!r}")


class ErrorPageTests(TestCase):

    def test_404_page_is_friendly_and_leaks_nothing(self):
        response = self.client.get("/this/page/does/not/exist/")

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "We can't find that page", status_code=404)
        assert_no_developer_detail(self, response.content.decode())

    def test_missing_dataset_gives_the_friendly_404_page(self):
        response = self.client.get("/dataset/no-such-dataset-slug/")

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "We can't find that page", status_code=404)

    def test_500_page_hides_the_exception_text(self):
        # Call the 500 handler directly, the way Django does when a view crashes.
        request = RequestFactory().get("/")
        try:
            raise RuntimeError(SECRET)
        except RuntimeError:
            response = server_error(request)

        body = response.content.decode()
        self.assertEqual(response.status_code, 500)
        self.assertIn("Something went wrong on our side", body)
        self.assertIn("The problem has been recorded", body)
        self.assertNotIn(SECRET, body)
        assert_no_developer_detail(self, body)

    def test_csrf_failure_shows_a_friendly_403_without_the_technical_reason(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post("/accounts/signup/", {"email": "x@example.com"})

        self.assertEqual(response.status_code, 403)
        body = response.content.decode()
        self.assertIn("You can't do that here", body)
        self.assertNotIn("CSRF", body)
        assert_no_developer_detail(self, body)


class UserFacingMessageTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="ada", email="ada@example.com", password="pw-test-123")
        self.client.force_login(self.user)

    def test_unreadable_excel_file_shows_plain_message_not_parser_error(self):
        # Garbage bytes with an Excel type: the reader raises an internal error.
        ds = Dataset.objects.create(
            title="Broken workbook",
            bio="A workbook whose file content is not a real spreadsheet.",
            topics="test",
            dataset_type="excel",
            author=self.user,
            file=SimpleUploadedFile("broken.xlsx", b"this is not a spreadsheet at all"),
        )
        response = self.client.get(f"/dataset/{ds.slug}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["error_message"], USER_MESSAGES["file_read"])
        assert_no_developer_detail(self, response.content.decode())

    def test_user_messages_contain_no_technical_words(self):
        for key, text in USER_MESSAGES.items():
            for word in ("Exception", "Traceback", "None", "NoneType", "KeyError", "stack", "SQL", "errno"):
                self.assertNotIn(word, text, f"{key} mentions {word!r}")
