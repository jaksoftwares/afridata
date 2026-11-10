"""
Signup, email verification and onboarding, end to end through the real views.

Django's test runner sends mail to an in-memory outbox, so the codes are read
from the outbox or from the stored token, exactly as a user would receive them.
"""
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import EmailVerificationToken

User = get_user_model()
PASSWORD = "Str0ng-pass-42"


class OnboardingFlowTests(TestCase):

    def signup(self, email="ada@example.com", **extra):
        data = {
            "email": email,
            "password": PASSWORD,
            "confirm_password": PASSWORD,
            "full_name": "Ada Lovelace",
            "username": "",
            "phone_number": "",
            "bio": "",
            "referral_code": "",
        }
        data.update(extra)
        return self.client.post(reverse("process_signup"), data)

    def code_for(self, email):
        user = User.objects.get(email=email)
        return EmailVerificationToken.objects.get(user=user).code

    def verify(self, code, follow=False):
        return self.client.post(reverse("verify_email"), {"code": code}, follow=follow)

    # ----- signup -------------------------------------------------------

    def test_signup_creates_unverified_account_and_emails_a_code(self):
        response = self.signup()

        self.assertRedirects(response, reverse("verify_email"))
        user = User.objects.get(email="ada@example.com")
        self.assertFalse(user.is_verified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ada@example.com"])
        self.assertIn(self.code_for("ada@example.com"), mail.outbox[0].body)
        self.assertEqual(self.client.session["verification_email"], "ada@example.com")

    def test_signup_succeeds_even_when_the_mail_server_fails(self):
        # The account must not be lost because email delivery failed.
        with mock.patch("accounts.views.send_verification_email", side_effect=OSError("smtp down")):
            response = self.signup()

        # fetch_redirect_response=False: fetching the page would consume the one-time message.
        self.assertRedirects(response, reverse("verify_email"), fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(email="ada@example.com").exists())
        follow = self.client.get(reverse("verify_email"))
        self.assertContains(follow, "We couldn")  # tells the user how to recover
        self.assertContains(follow, "Resend Code")

    def test_signup_with_an_unverified_email_resumes_instead_of_failing(self):
        self.signup()
        response = self.signup()  # same address again, e.g. the first mail never arrived

        self.assertRedirects(response, reverse("verify_email"))
        self.assertEqual(User.objects.filter(email="ada@example.com").count(), 1)
        self.assertEqual(self.client.session["verification_email"], "ada@example.com")

    def test_signup_with_a_verified_email_is_refused(self):
        User.objects.create_user(username="old", email="ada@example.com", password=PASSWORD, is_verified=True)
        response = self.signup()

        self.assertEqual(response.status_code, 200)
        self.assertIn("already exists", response.context["field_errors"]["email"])

    # ----- verification -------------------------------------------------

    def test_correct_code_verifies_logs_in_and_shows_welcome_once(self):
        self.signup()
        response = self.verify(self.code_for("ada@example.com"))

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertTrue(User.objects.get(email="ada@example.com").is_verified)
        self.assertNotIn("verification_email", self.client.session)

        home = self.client.get(reverse("home"))
        self.assertContains(home, "Welcome to AfriData")
        self.assertContains(home, "Complete your profile")

        # The welcome card is one-time: it must not come back on the next visit.
        again = self.client.get(reverse("home"))
        self.assertNotContains(again, "Welcome to AfriData")

    def test_wrong_code_shows_remaining_attempts_on_the_page(self):
        self.signup()
        response = self.verify("000000", follow=True)

        self.assertContains(response, "That code is incorrect. 4 attempts left.")

    def test_code_locks_after_five_wrong_attempts(self):
        self.signup()
        correct = self.code_for("ada@example.com")
        for _ in range(5):
            self.verify("000000")

        response = self.verify(correct, follow=True)
        self.assertContains(response, "Too many incorrect attempts")
        self.assertFalse(User.objects.get(email="ada@example.com").is_verified)

    def test_expired_code_is_explained(self):
        self.signup()
        EmailVerificationToken.objects.filter(user__email="ada@example.com").update(
            created_at=timezone.now() - timedelta(hours=25)
        )
        response = self.verify(self.code_for("ada@example.com"), follow=True)

        self.assertContains(response, "This code has expired")

    # ----- resend and change address -------------------------------------

    def test_resend_is_blocked_during_the_cooldown(self):
        self.signup()
        response = self.client.post(reverse("resend_verification"), follow=True)

        self.assertContains(response, "Please wait")
        self.assertEqual(len(mail.outbox), 1)  # no second email

    def test_resend_sends_a_new_code_after_the_cooldown(self):
        self.signup()
        EmailVerificationToken.objects.filter(user__email="ada@example.com").update(
            created_at=timezone.now() - timedelta(seconds=120)
        )
        response = self.client.post(reverse("resend_verification"), follow=True)

        self.assertContains(response, "A new code was sent")
        self.assertEqual(len(mail.outbox), 2)

    def test_wrong_address_can_be_corrected_and_the_code_goes_to_the_new_one(self):
        self.signup(email="ada@exmaple.com")  # typo
        response = self.client.post(
            reverse("change_verification_email"), {"new_email": "ada@example.com"}, follow=True
        )

        self.assertContains(response, "We sent a new code to ada@example.com")
        self.assertTrue(User.objects.filter(email="ada@example.com").exists())
        self.assertFalse(User.objects.filter(email="ada@exmaple.com").exists())
        self.assertEqual(mail.outbox[-1].to, ["ada@example.com"])

        # The new code is the one that works.
        self.verify(self.code_for("ada@example.com"))
        self.assertTrue(User.objects.get(email="ada@example.com").is_verified)

    def test_changing_to_an_address_in_use_is_refused(self):
        User.objects.create_user(username="taken", email="taken@example.com", password=PASSWORD, is_verified=True)
        self.signup()
        response = self.client.post(
            reverse("change_verification_email"), {"new_email": "taken@example.com"}, follow=True
        )

        self.assertContains(response, "Another account already uses that email address")
        self.assertTrue(User.objects.filter(email="ada@example.com").exists())

    def test_verify_page_without_a_pending_signup_sends_the_user_to_signup(self):
        response = self.client.get(reverse("verify_email"), follow=True)

        self.assertRedirects(response, reverse("login_signup"))
        self.assertContains(response, "Log in or sign up to continue")
