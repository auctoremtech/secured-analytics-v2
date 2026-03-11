from django.test import TestCase, Client
from django.urls import reverse
from .models import Users, Person


class WelcomePageViewTest(TestCase):
    def test_welcome_page_renders(self):
        """Test that the welcome page renders correctly."""
        response = self.client.get(reverse("welcome"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "securedAnalyticsApp/welcome.html")
        self.assertContains(response, "Welcome to Secure Analytics")
        self.assertContains(response, "Would you like to proceed?")
        self.assertContains(response, "Yes")
        self.assertContains(response, "No")


class DisclaimerPageViewTest(TestCase):
    def test_disclaimer_page_renders(self):
        """Test that the disclaimer page renders correctly."""
        response = self.client.get(reverse("disclaimer"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "securedAnalyticsApp/disclaimer.html")
        self.assertContains(response, "Disclaimer Page")
        self.assertContains(response, "Lorem ipsum")
        self.assertContains(response, "Accept")
        self.assertContains(response, "Do Not Accept")


class DemographicsViewTest(TestCase):
    def setUp(self):
        """Set up test user."""
        self.user = Users.objects.create(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

    def test_demographics_page_renders(self):
        """Test that the demographics page renders correctly."""
        response = self.client.get(reverse("demographics"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "securedAnalyticsApp/demographics.html")
        self.assertContains(response, "Demographics Information")
        self.assertContains(response, "Phone Number")
        self.assertContains(response, "Date of Birth")
        self.assertContains(response, "Street Address")
        self.assertContains(response, "City")
        self.assertContains(response, "State")
        self.assertContains(response, "Zip Code")
        self.assertContains(response, "Ethnicity")

    def test_demographics_form_submit(self):
        """Test that demographics form can be submitted."""
        # Set up session with user_id
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        response = self.client.post(
            reverse("demographics"),
            {
                "phone_number": "555-1234",
                "address": "123 Test St",
                "city": "Test City",
                "state": "TX",
                "zip_code": "12345",
                "date_of_birth": "1990-01-01",
                "ethnicity": "Other",
            },
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(Person.objects.filter(user=self.user).exists())


class LogoutViewTest(TestCase):
    def test_logout_clears_session_and_redirects(self):
        """Test that logout clears session and redirects to login."""
        # Set up a session
        session = self.client.session
        session["user_id"] = 1
        session.save()

        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("login"))

        # Session should be cleared
        self.assertNotIn("user_id", self.client.session)


class LoginPageViewTest(TestCase):
    def setUp(self):
        """Set up test user."""
        self.user = Users.objects.create(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

    def test_login_page_renders(self):
        """Test that the login page renders correctly."""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "securedAnalyticsApp/login.html")

    def test_login_success_redirects_to_welcome(self):
        """Test that successful login redirects to welcome page."""
        response = self.client.post(
            reverse("login"),
            {"username": "testuser", "password": "testpass123"},
        )
        self.assertRedirects(response, reverse("welcome"))

    def test_login_failure_stays_on_login(self):
        """Test that failed login stays on login page."""
        response = self.client.post(
            reverse("login"),
            {"username": "wronguser", "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid credentials")

