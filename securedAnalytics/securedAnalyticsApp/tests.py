from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from .models import Users, Person


class WelcomePageViewTest(TestCase):
    def setUp(self):
        """Set up test user and login."""
        self.user = Users.objects.create(
            username="testuser",
            email="test@example.com",
            password=make_password("testpass123"),
        )

    def test_welcome_page_requires_login(self):
        """Test that the welcome page redirects to login if not authenticated."""
        response = self.client.get(reverse("welcome"))
        self.assertRedirects(response, reverse("login"))

    def test_welcome_page_renders_when_logged_in(self):
        """Test that the welcome page renders correctly when logged in."""
        # Set up session with user_id
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        response = self.client.get(reverse("welcome"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "securedAnalyticsApp/welcome.html")
        self.assertContains(response, "Welcome to Secure Analytics")
        self.assertContains(response, "Would you like to proceed?")
        self.assertContains(response, "Yes")
        self.assertContains(response, "No")


class DisclaimerPageViewTest(TestCase):
    def setUp(self):
        """Set up test user."""
        self.user = Users.objects.create(
            username="testuser",
            email="test@example.com",
            password=make_password("testpass123"),
        )

    def test_disclaimer_page_requires_login(self):
        """Test that the disclaimer page redirects to login if not authenticated."""
        response = self.client.get(reverse("disclaimer"))
        self.assertRedirects(response, reverse("login"))

    def test_disclaimer_page_renders_when_logged_in(self):
        """Test that the disclaimer page renders correctly when logged in."""
        # Set up session with user_id
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

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
            password=make_password("testpass123"),
        )

    def test_demographics_page_requires_login(self):
        """Test that the demographics page redirects to login if not authenticated."""
        response = self.client.get(reverse("demographics"))
        self.assertRedirects(response, reverse("login"))

    def test_demographics_page_renders_when_logged_in(self):
        """Test that the demographics page renders correctly when logged in."""
        # Set up session with user_id
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        response = self.client.get(reverse("demographics"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "securedAnalyticsApp/demographics.html")
        self.assertContains(response, "Demographics Information")
        self.assertContains(response, "First Name")
        self.assertContains(response, "Middle Name")
        self.assertContains(response, "Last Name")
        self.assertContains(response, "Suffix")
        self.assertContains(response, "Phone Number")
        self.assertContains(response, "Date of Birth")
        self.assertContains(response, "Street Address")
        self.assertContains(response, "City")
        self.assertContains(response, "State")
        self.assertContains(response, "Zip Code")
        self.assertContains(response, "Ethnicity")
        self.assertContains(response, "Gender")
        self.assertContains(response, "Rank")
        self.assertContains(response, "Years of Service")

    def test_demographics_form_submit(self):
        """Test that demographics form can be submitted."""
        # Set up session with user_id
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        response = self.client.post(
            reverse("demographics"),
            {
                "first_name": "Taylor",
                "middle_name": "Anne",
                "last_name": "Jordan",
                "name_suffix": "Jr.",
                "phone_number": "555-123-4567",
                "address": "123 Test St",
                "city": "Test City",
                "state": "TX",
                "zip_code": "12345",
                "date_of_birth": "1990-01-01",
                "ethnicity": "Other",
                "gender": "Male",
                "rank": "Detective",
                "years_of_service": "3-5",
            },
        )
        self.assertRedirects(response, reverse("demographics_saved"))
        person = Person.objects.get(user=self.user)
        self.assertEqual(person.phone_number, "555-123-4567")
        self.assertEqual(person.gender, "Male")
        self.assertEqual(person.rank, "Detective")
        self.assertEqual(person.years_of_service, "3-5")
        self.assertEqual(len(person.anonymous_id), 10)
        self.assertTrue(person.anonymous_id.isalnum())
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Taylor")
        self.assertEqual(self.user.middle_name, "Anne")
        self.assertEqual(self.user.last_name, "Jordan")
        self.assertEqual(self.user.name_suffix, "Jr.")

    def test_demographics_form_updates_existing_person_record(self):
        """Test that demographics submissions update the current user's Person record."""
        person = Person.objects.create(
            user=self.user,
            phone_number="555-0000",
            address="Old Address",
            city="Old City",
            state="CA",
            zip_code="00000",
            ethnicity="Other",
        )

        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        response = self.client.post(
            reverse("demographics"),
            {
                "first_name": "Casey",
                "middle_name": "Lee",
                "last_name": "Morgan",
                "name_suffix": "III",
                "phone_number": "555-999-9999",
                "address": "456 Updated Ave",
                "city": "New City",
                "state": "NY",
                "zip_code": "10001",
                "date_of_birth": "1985-05-05",
                "ethnicity": "Asian",
                "gender": "Female",
                "rank": "Captain",
                "years_of_service": "5-7",
            },
        )

        self.assertRedirects(response, reverse("demographics_saved"))
        self.assertEqual(Person.objects.filter(user=self.user).count(), 1)

        person.refresh_from_db()
        self.assertEqual(person.phone_number, "555-999-9999")
        self.assertEqual(person.address, "456 Updated Ave")
        self.assertEqual(person.city, "New City")
        self.assertEqual(person.state, "NY")
        self.assertEqual(person.zip_code, "10001")
        self.assertEqual(str(person.date_of_birth), "1985-05-05")
        self.assertEqual(person.ethnicity, "Asian")
        self.assertEqual(person.gender, "Female")
        self.assertEqual(person.rank, "Captain")
        self.assertEqual(person.years_of_service, "5-7")

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Casey")
        self.assertEqual(self.user.middle_name, "Lee")
        self.assertEqual(self.user.last_name, "Morgan")
        self.assertEqual(self.user.name_suffix, "III")

    def test_years_of_service_saves_correctly(self):
        """Test that each years_of_service range is accepted and saved."""
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        for yos in ["0-2", "2-3", "3-5", "5-7"]:
            self.client.post(
                reverse("demographics"),
                {
                    "first_name": "Sam",
                    "middle_name": "",
                    "last_name": "Test",
                    "name_suffix": "",
                    "phone_number": "",
                    "address": "",
                    "city": "",
                    "state": "",
                    "zip_code": "",
                    "date_of_birth": "",
                    "ethnicity": "Other",
                    "years_of_service": yos,
                },
            )
            person = Person.objects.get(user=self.user)
            self.assertEqual(person.years_of_service, yos)

    def test_zip_code_accepts_zip_plus_four(self):
        """Test that ZIP+4 format (12345-6789) is accepted."""
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        response = self.client.post(
            reverse("demographics"),
            {
                "first_name": "Alex",
                "middle_name": "",
                "last_name": "Smith",
                "name_suffix": "",
                "phone_number": "555-000-0001",
                "address": "1 Main St",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701-1234",
                "date_of_birth": "",
                "ethnicity": "Other",
            },
        )
        self.assertRedirects(response, reverse("demographics_saved"))
        person = Person.objects.get(user=self.user)
        self.assertEqual(person.zip_code, "78701-1234")

    def test_zip_code_rejects_invalid_format(self):
        """Test that non-US zip code formats are rejected."""
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        for bad_zip in ["1234", "123456", "ABCDE", "1234-56789"]:
            response = self.client.post(
                reverse("demographics"),
                {
                    "first_name": "Alex",
                    "middle_name": "",
                    "last_name": "Smith",
                    "name_suffix": "",
                    "phone_number": "555-000-0001",
                    "address": "1 Main St",
                    "city": "Austin",
                    "state": "TX",
                    "zip_code": bad_zip,
                    "date_of_birth": "",
                    "ethnicity": "Other",
                },
            )
            self.assertEqual(
                response.status_code,
                200,
                msg=f"Expected form error for zip '{bad_zip}' but got a redirect",
            )
            self.assertContains(response, "valid US zip code")

    def test_state_rejects_invalid_value(self):
        """Test that a value not in the US states list is rejected."""
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        response = self.client.post(
            reverse("demographics"),
            {
                "first_name": "Alex",
                "middle_name": "",
                "last_name": "Smith",
                "name_suffix": "",
                "phone_number": "555-000-0001",
                "address": "1 Main St",
                "city": "Austin",
                "state": "XX",
                "zip_code": "78701",
                "date_of_birth": "",
                "ethnicity": "Other",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a valid choice")

    def test_name_fields_reject_invalid_characters(self):
        """Test that name fields reject digits and special characters."""
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        for bad_name in ["Taylor123", "Anne@Work", "Jordan<script>"]:
            response = self.client.post(
                reverse("demographics"),
                {
                    "first_name": bad_name,
                    "middle_name": "",
                    "last_name": "Smith",
                    "name_suffix": "",
                    "phone_number": "",
                    "address": "",
                    "city": "",
                    "state": "",
                    "zip_code": "",
                    "date_of_birth": "",
                    "ethnicity": "Other",
                    "years_of_service": "",
                },
            )
            self.assertEqual(
                response.status_code, 200,
                msg=f"Expected validation error for first_name='{bad_name}'",
            )

    def test_name_fields_accept_hyphens_and_apostrophes(self):
        """Test that hyphenated names and names with apostrophes are accepted."""
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        response = self.client.post(
            reverse("demographics"),
            {
                "first_name": "Mary-Jane",
                "middle_name": "O'Brien",
                "last_name": "Smith-Jones",
                "name_suffix": "",
                "phone_number": "",
                "address": "",
                "city": "",
                "state": "",
                "zip_code": "",
                "date_of_birth": "",
                "ethnicity": "Other",
                "years_of_service": "",
            },
        )
        self.assertRedirects(response, reverse("demographics_saved"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Mary-Jane")
        self.assertEqual(self.user.middle_name, "O'Brien")
        self.assertEqual(self.user.last_name, "Smith-Jones")

    def test_demographics_saved_page_requires_login(self):
        """Test that the demographics saved page redirects to login if not authenticated."""
        response = self.client.get(reverse("demographics_saved"))
        self.assertRedirects(response, reverse("login"))

    def test_demographics_saved_page_displays_anonymous_id_and_copy(self):
        """Test that demographics saved page shows anonymous ID and the Proceed button."""
        person = Person.objects.create(user=self.user)

        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        response = self.client.get(reverse("demographics_saved"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "securedAnalyticsApp/demographics_saved.html")
        self.assertContains(response, "Your unique anonymous ID is:")
        self.assertContains(response, str(person.anonymous_id))
        self.assertContains(response, "Lorem ipsum")
        self.assertContains(response, "Proceed")

    def test_phone_rejects_invalid_format(self):
        """Test that non-US phone number formats are rejected."""
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        for bad_phone in ["555-1234", "12345", "abcdefghij", "555-abc-1234"]:
            response = self.client.post(
                reverse("demographics"),
                {
                    "first_name": "",
                    "middle_name": "",
                    "last_name": "",
                    "name_suffix": "",
                    "phone_number": bad_phone,
                    "address": "",
                    "city": "",
                    "state": "",
                    "zip_code": "",
                    "date_of_birth": "",
                    "ethnicity": "Other",
                    "years_of_service": "",
                },
            )
            self.assertEqual(
                response.status_code, 200,
                msg=f"Expected validation error for phone='{bad_phone}'",
            )

    def test_address_rejects_invalid_characters(self):
        """Test that address rejects characters outside the allowed set."""
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        response = self.client.post(
            reverse("demographics"),
            {
                "first_name": "",
                "middle_name": "",
                "last_name": "",
                "name_suffix": "",
                "phone_number": "",
                "address": "123 Main St <script>alert(1)</script>",
                "city": "",
                "state": "",
                "zip_code": "",
                "date_of_birth": "",
                "ethnicity": "Other",
                "years_of_service": "",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_city_rejects_invalid_characters(self):
        """Test that city rejects characters outside the allowed set."""
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        response = self.client.post(
            reverse("demographics"),
            {
                "first_name": "",
                "middle_name": "",
                "last_name": "",
                "name_suffix": "",
                "phone_number": "",
                "address": "",
                "city": "New <City>",
                "state": "",
                "zip_code": "",
                "date_of_birth": "",
                "ethnicity": "Other",
                "years_of_service": "",
            },
        )
        self.assertEqual(response.status_code, 200)


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
            password=make_password("testpass123"),
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

