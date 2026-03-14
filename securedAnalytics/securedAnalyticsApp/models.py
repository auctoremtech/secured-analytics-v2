import string

from django.db import models
from django.utils.crypto import get_random_string


def generate_anonymous_id():
    """Generate a unique 10-character alphanumeric ID for anonymous tracking."""
    allowed_chars = string.ascii_uppercase + string.digits
    while True:
        candidate = get_random_string(10, allowed_chars=allowed_chars)
        if not Person.objects.filter(anonymous_id=candidate).exists():
            return candidate


class Users(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    first_name = models.CharField(max_length=150, blank=True)
    middle_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    name_suffix = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username


class Person(models.Model):
    YEARS_OF_SERVICE_CHOICES = [
        ("", "— Select —"),
        ("0-2", "0–2 years"),
        ("2-3", "2–3 years"),
        ("3-5", "3–5 years"),
        ("5-7", "5–7 years"),
    ]

    ETHNICITY_CHOICES = [
        ("Asian", "Asian"),
        ("Black", "Black"),
        ("Hispanic", "Hispanic"),
        ("Native American", "Native American"),
        ("Pacific Islander", "Pacific Islander"),
        ("White", "White"),
        ("Mixed Race", "Mixed Race"),
        ("Other", "Other"),
        ("Prefer not to say", "Prefer not to say"),
    ]

    GENDER_CHOICES = [
        ("", "— Select —"),
        ("Male", "Male"),
        ("Female", "Female"),
    ]

    RANK_CHOICES = [
        ("", "— Select —"),
        ("Officer", "Officer"),
        ("Deputy", "Deputy"),
        ("trooper", "trooper"),
        ("Constable", "Constable"),
        ("Detective", "Detective"),
        ("Investigator", "Investigator"),
        ("Deputy Inspector", "Deputy Inspector"),
        ("Corporal", "Corporal"),
        ("Senior Officer", "Senior Officer"),
        ("Sergeant", "Sergeant"),
        ("Staff Sergeant", "Staff Sergeant"),
        ("Lieutenant", "Lieutenant"),
        ("Captain", "Captain"),
        ("Commander", "Commander"),
        ("Major", "Major"),
        ("Deputy Chief", "Deputy Chief"),
        ("Assistant Chief", "Assistant Chief"),
        ("Lieutenant Colonel", "Lieutenant Colonel"),
        ("Colonel", "Colonel"),
        ("Undersheriff", "Undersheriff"),
        ("Chief of Police", "Chief of Police"),
        ("Sheriff", "Sheriff"),
        ("Commissioner", "Commissioner"),
        ("Superintendent", "Superintendent"),
    ]

    user = models.OneToOneField(Users, on_delete=models.CASCADE)
    anonymous_id = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        default=generate_anonymous_id,
    )
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    ethnicity = models.CharField(
        max_length=50,
        choices=ETHNICITY_CHOICES,
        blank=True,
        default="Other",
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        default="",
    )
    rank = models.CharField(
        max_length=30,
        choices=RANK_CHOICES,
        blank=True,
        default="",
    )
    years_of_service = models.CharField(
        max_length=10,
        choices=YEARS_OF_SERVICE_CHOICES,
        blank=True,
        default="",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "People"

    def __str__(self):
        return f"Person({self.user.username})"


class Address(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="addresses")
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, blank=True)
    address_type = models.CharField(
        max_length=50,
        choices=[
            ("Home", "Home"),
            ("Work", "Work"),
            ("Other", "Other"),
        ],
        default="Home",
    )
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state}"
