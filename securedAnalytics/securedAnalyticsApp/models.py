import string

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string


def generate_anonymous_id():
    """Generate a unique 10-character alphanumeric ID for anonymous tracking."""
    allowed_chars = string.ascii_uppercase + string.digits
    while True:
        candidate = get_random_string(10, allowed_chars=allowed_chars)
        if not Person.objects.filter(anonymous_id=candidate).exists():
            return candidate


class Users(AbstractUser):
    middle_name = models.CharField(max_length=150, blank=True)
    name_suffix = models.CharField(max_length=20, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

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


# ---------------------------------------------------------------------------
# Abstract base models — shared structure for all assessment types
# ---------------------------------------------------------------------------

class BaseAssessmentCategory(models.Model):
    """Abstract base for Roman-numeral assessment category sections."""

    NUMERAL_CHOICES = [
        ("I", "I"), ("II", "II"), ("III", "III"), ("IV", "IV"),
        ("V", "V"), ("VI", "VI"), ("VII", "VII"),
    ]

    numeral = models.CharField(max_length=4, choices=NUMERAL_CHOICES, unique=True)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    order = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        abstract = True
        ordering = ["order"]

    def __str__(self):
        return f"{self.numeral}. {self.title}"


class BaseAssessmentQuestion(models.Model):
    """Abstract base for numbered assessment questions."""

    number = models.PositiveSmallIntegerField(unique=True)
    text = models.TextField()

    class Meta:
        abstract = True
        ordering = ["number"]

    def __str__(self):
        return f"Q{self.number}: {self.text[:80]}"


class BaseAssessment(models.Model):
    """Abstract base for assessment heading/instance models."""

    assessed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-assessed_at"]

    def __str__(self):
        return f"{self.title} ({self.assessed_at:%Y-%m-%d})"


# ---------------------------------------------------------------------------
# Supervisor's Leadership Engagement (SLE)
# ---------------------------------------------------------------------------

class SLECategory(BaseAssessmentCategory):
    class Meta(BaseAssessmentCategory.Meta):
        verbose_name = "SLE Category"
        verbose_name_plural = "SLE Categories"


class SLEQuestion(BaseAssessmentQuestion):
    category = models.ForeignKey(
        SLECategory, on_delete=models.CASCADE, related_name="questions",
    )

    class Meta(BaseAssessmentQuestion.Meta):
        verbose_name = "SLE Question"
        verbose_name_plural = "SLE Questions"


class SupervisorLeadershipEngagement(BaseAssessment):
    title = models.CharField(max_length=255, default="Supervisor's Leadership Engagement")

    class Meta(BaseAssessment.Meta):
        verbose_name = "Supervisor Leadership Engagement"
        verbose_name_plural = "Supervisor Leadership Engagements"


# ---------------------------------------------------------------------------
# Mental and Emotional Resilience in Leadership (MER)
# ---------------------------------------------------------------------------

class MERCategory(BaseAssessmentCategory):
    class Meta(BaseAssessmentCategory.Meta):
        verbose_name = "MER Category"
        verbose_name_plural = "MER Categories"


class MERQuestion(BaseAssessmentQuestion):
    category = models.ForeignKey(
        MERCategory, on_delete=models.CASCADE, related_name="questions",
    )

    class Meta(BaseAssessmentQuestion.Meta):
        verbose_name = "MER Question"
        verbose_name_plural = "MER Questions"


class MentalEmotionalResilience(BaseAssessment):
    title = models.CharField(
        max_length=255, default="Mental and Emotional Resilience in Leadership",
    )

    class Meta(BaseAssessment.Meta):
        verbose_name = "Mental and Emotional Resilience in Leadership"
        verbose_name_plural = "Mental and Emotional Resilience in Leadership"


# ---------------------------------------------------------------------------
# Officer Wellbeing (OWB)
# ---------------------------------------------------------------------------

class OWBCategory(BaseAssessmentCategory):
    class Meta(BaseAssessmentCategory.Meta):
        verbose_name = "OWB Category"
        verbose_name_plural = "OWB Categories"


class OWBQuestion(BaseAssessmentQuestion):
    category = models.ForeignKey(
        OWBCategory, on_delete=models.CASCADE, related_name="questions",
    )

    class Meta(BaseAssessmentQuestion.Meta):
        verbose_name = "OWB Question"
        verbose_name_plural = "OWB Questions"


class OfficerWellbeing(BaseAssessment):
    title = models.CharField(max_length=255, default="Officer Wellbeing")

    class Meta(BaseAssessment.Meta):
        verbose_name = "Officer Wellbeing"
        verbose_name_plural = "Officer Wellbeing"


# ---------------------------------------------------------------------------
# Psychological Safety in the Workplace (PSW)
# ---------------------------------------------------------------------------

class PSWCategory(BaseAssessmentCategory):
    class Meta(BaseAssessmentCategory.Meta):
        verbose_name = "PSW Category"
        verbose_name_plural = "PSW Categories"


class PSWQuestion(BaseAssessmentQuestion):
    category = models.ForeignKey(
        PSWCategory, on_delete=models.CASCADE, related_name="questions",
    )

    class Meta(BaseAssessmentQuestion.Meta):
        verbose_name = "PSW Question"
        verbose_name_plural = "PSW Questions"


class PsychologicalSafety(BaseAssessment):
    title = models.CharField(
        max_length=255, default="Psychological Safety in the Workplace",
    )

    class Meta(BaseAssessment.Meta):
        verbose_name = "Psychological Safety in the Workplace"
        verbose_name_plural = "Psychological Safety in the Workplace"


# ---------------------------------------------------------------------------
# Organizational Culture and Leadership Change (OCL)
# ---------------------------------------------------------------------------

class OCLCategory(BaseAssessmentCategory):
    class Meta(BaseAssessmentCategory.Meta):
        verbose_name = "OCL Category"
        verbose_name_plural = "OCL Categories"


class OCLQuestion(BaseAssessmentQuestion):
    category = models.ForeignKey(
        OCLCategory, on_delete=models.CASCADE, related_name="questions",
    )

    class Meta(BaseAssessmentQuestion.Meta):
        verbose_name = "OCL Question"
        verbose_name_plural = "OCL Questions"


class OrganizationalCultureChange(BaseAssessment):
    title = models.CharField(
        max_length=255, default="Organizational Culture and Leadership Change",
    )

    class Meta(BaseAssessment.Meta):
        verbose_name = "Organizational Culture and Leadership Change"
        verbose_name_plural = "Organizational Culture and Leadership Change"
