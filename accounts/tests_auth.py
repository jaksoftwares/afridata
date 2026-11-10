"""Login, logout, redirects and password reset, through the real views."""
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

User = get_user_model()
PASSWORD = "Str0ng-pass-42"


class LoginTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="ada", email="ada@example.com", password=PASSWORD,
            full_name="Ada Lovelace", is_verified=True,
        )

    def login(self, email="ada@example.com", password=PASSWORD, **extra):
        data = {"email": email, "password": password}
        data.update(extra)
        return self.client.post(reverse("authenticate_login"), data)

    def test_correct_credentials_log_the_user_in(self):
        response = self.login()

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_email_is_case_insensitive(self):
        response = self.login(email="ADA@Example.com")
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)

    def test_wrong_password_is_refused_without_logging_in(self):
        response = self.login(password="not-the-password")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Invalid email or password", response.context["field_errors"]["password"])
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_unknown_email_gets_the_same_message_as_a_wrong_password(self):
        # Same message for both, so the form can't be used to find registered emails.
        response = self.login(email="nobody@example.com")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Invalid email or password", response.context["field_errors"]["password"])

    def test_missing_fields_are_reported(self):
        response = self.login(password="")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Password is required", response.context["field_errors"]["password"])

    def test_unverified_user_is_sent_to_verification_and_not_logged_in(self):
        User.objects.create_user(username="bob", email="bob@example.com", password=PASSWORD, is_verified=False)
        response = self.login(email="bob@example.com")

        self.assertRedirects(response, reverse("verify_email"), fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.session["verification_email"], "bob@example.com")

    def test_deactivated_account_cannot_log_in(self):
        self.user.is_active = False
        self.user.save()
        response = self.login()

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_next_parameter_on_the_same_site_is_honoured(self):
        response = self.login(next="/dataset/upload/")
        self.assertRedirects(response, "/dataset/upload/", fetch_redirect_response=False)

    def test_next_parameter_to_another_site_is_ignored(self):
        # Prevents the login form being used to send users to a phishing site.
        response = self.login(next="https://evil.example.com/steal")
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)

    def test_logout_ends_the_session(self):
        self.login()
        response = self.client.get(reverse("logout"))

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)

    def test_login_page_renders_for_visitors(self):
        response = self.client.get(reverse("login_signup"))
        self.assertEqual(response.status_code, 200)

    def test_protected_page_redirects_anonymous_visitors_to_login(self):
        response = self.client.get(reverse("upload_dataset"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/", response["Location"])


class PasswordResetTests(TestCase):

    def setUp(self):
        User.objects.create_user(username="ada", email="ada@example.com", password=PASSWORD, is_verified=True)

    def test_reset_email_is_sent_to_a_registered_address(self):
        response = self.client.post(reverse("password_reset"), {"email": "ada@example.com"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ada@example.com"])
        self.assertIn("/accounts/password-reset-confirm/", mail.outbox[0].body)

    def test_reset_request_for_unknown_address_looks_the_same(self):
        # No email is sent, but the user sees the same confirmation page.
        response = self.client.post(reverse("password_reset"), {"email": "nobody@example.com"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.client.get(response["Location"]).status_code, 200)

    def test_full_reset_lets_the_user_log_in_with_the_new_password(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = User.objects.get(email="ada@example.com")
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        confirm_url = reverse("password_reset_confirm", args=[uid, token])

        # Django redirects the token URL to a set-password URL; follow it and submit.
        first = self.client.get(confirm_url)
        set_url = first["Location"]
        self.client.post(set_url, {"new_password1": "Brand-new-pass-99", "new_password2": "Brand-new-pass-99"})

        self.client.logout()
        self.assertFalse(self.client.login(username="ada@example.com", password=PASSWORD))
        self.assertTrue(self.client.login(username="ada@example.com", password="Brand-new-pass-99"))
