from django.db import models


class Users(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username


class Person(models.Model):
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

    user = models.OneToOneField(Users, on_delete=models.CASCADE)
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
