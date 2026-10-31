from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from store import models as store_models


class RegistrationTests(TestCase):
    def test_registration_creates_user_and_customer(self):
        response = self.client.post(reverse("accounts:register"), {
            "username": "ada",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "password1": "SuperSecret123!",
            "password2": "SuperSecret123!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="ada").exists())
        user = User.objects.get(username="ada")
        self.assertTrue(store_models.Customer.objects.filter(user=user).exists())

    def test_duplicate_email_rejected(self):
        User.objects.create_user(username="existing", email="taken@example.com", password="x")
        response = self.client.post(reverse("accounts:register"), {
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "email": "taken@example.com",
            "password1": "SuperSecret123!",
            "password2": "SuperSecret123!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())


class ProfileViewTests(TestCase):
    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)

    def test_profile_loads_for_logged_in_user(self):
        User.objects.create_user(username="ada", password="SuperSecret123!")
        self.client.login(username="ada", password="SuperSecret123!")
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
