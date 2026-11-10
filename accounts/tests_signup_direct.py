"""Frictionless signup: an account is active and logged in straight after the form."""
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

User = get_user_model()
PASSWORD = "Str0ng-pass-42"


class DirectSignupTests(TestCase):

    def signup(self, email="ada@example.com"):
        return self.client.post(reverse("process_signup"), {
            "email": email, "password": PASSWORD, "confirm_password": PASSWORD,
            "full_name": "Ada Lovelace", "username": "", "phone_number": "", "bio": "", "referral_code": "",
        })

    def test_signup_logs_the_user_in_and_goes_home(self):
        response = self.signup()

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        user = User.objects.get(email="ada@example.com")
        self.assertTrue(user.is_verified)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_no_verification_email_is_sent(self):
        self.signup()
        self.assertEqual(len(mail.outbox), 0)
        self.assertNotIn("verification_email", self.client.session)

    def test_the_welcome_card_is_shown_on_the_first_visit(self):
        self.signup()
        self.assertContains(self.client.get(reverse("home")), "Welcome to AfriData")

    def test_the_new_account_can_log_in_again_with_its_password(self):
        self.signup()
        self.client.logout()
        response = self.client.post(reverse("authenticate_login"), {"email": "ada@example.com", "password": PASSWORD})
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)

    def test_an_email_already_in_use_is_still_refused(self):
        self.signup()
        self.client.logout()
        response = self.signup()
        self.assertEqual(response.status_code, 200)
        self.assertIn("already exists", response.context["field_errors"]["email"])


class StuckAccountTests(TestCase):
    """Accounts left unverified by the old code step can log in with their password."""

    def test_an_unverified_account_logs_in_directly(self):
        user = User.objects.create_user(username="old", email="old@example.com", password=PASSWORD, is_verified=False)
        response = self.client.post(reverse("authenticate_login"), {"email": "old@example.com", "password": PASSWORD})

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        user.refresh_from_db()
        self.assertTrue(user.is_verified)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_an_unverified_account_still_needs_the_right_password(self):
        User.objects.create_user(username="old", email="old@example.com", password=PASSWORD, is_verified=False)
        response = self.client.post(reverse("authenticate_login"), {"email": "old@example.com", "password": "wrong-pass-1"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
