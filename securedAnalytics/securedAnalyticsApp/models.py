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
        ("trooper", "Trooper"),
        ("Trooper 1", "Trooper 1"),
        ("Trooper 2", "Trooper 2"),
        ("Trooper 3", "Trooper 3"),
        ("Trooper 4", "Trooper 4"),
        ("Trooper 5", "Trooper 5"),
        ("Trooper 6", "Trooper 6"),
        ("Ranger", "Ranger"),
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

    AVATAR_CHOICES = [
        ("", "— No Avatar —"),
        ("avatar_badge.svg", "Badge"),
        ("avatar_shield.svg", "Shield"),
        ("avatar_star.svg", "Star"),
        ("avatar_eagle.svg", "Eagle"),
        ("avatar_helmet.svg", "Helmet"),
    ]

    user = models.OneToOneField(Users, on_delete=models.CASCADE)
    anonymous_id = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        default=generate_anonymous_id,
    )
    profile_photo = models.ImageField(
        upload_to="profile_photos/",
        blank=True,
        default="",
    )
    avatar = models.CharField(
        max_length=50,
        choices=AVATAR_CHOICES,
        blank=True,
        default="",
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
        ("V", "V"), ("VI", "VI"), ("VII", "VII"), ("VIII", "VIII"),
        ("IX", "IX"), ("X", "X"), ("XI", "XI"), ("XII", "XII"),
        ("XIII", "XIII"), ("XIV", "XIV"), ("XV", "XV"), ("XVI", "XVI"),
        ("XVII", "XVII"), ("XVIII", "XVIII"), ("XIX", "XIX"), ("XX", "XX"),
        ("XXI", "XXI"), ("XXII", "XXII"), ("XXIII", "XXIII"),
        ("XXIV", "XXIV"), ("XXV", "XXV"), ("XXVI", "XXVI"),
        ("XXVII", "XXVII"), ("XXVIII", "XXVIII"), ("XXIX", "XXIX"),
        ("XXX", "XXX"),
    ]

    numeral = models.CharField(max_length=10, choices=NUMERAL_CHOICES, unique=True)
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
        SLECategory, on_delete=models.CASCADE, related_name="questions", db_index=True,
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
        MERCategory, on_delete=models.CASCADE, related_name="questions", db_index=True,
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
        OWBCategory, on_delete=models.CASCADE, related_name="questions", db_index=True,
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
        PSWCategory, on_delete=models.CASCADE, related_name="questions", db_index=True,
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
        OCLCategory, on_delete=models.CASCADE, related_name="questions", db_index=True,
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


# ---------------------------------------------------------------------------
# Survey Progress (save & resume)
# ---------------------------------------------------------------------------

class SurveyProgress(models.Model):
    """Persists survey state so users can save progress and resume later."""

    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="survey_sessions",
    )
    anonymous_id = models.CharField(
        max_length=10, blank=True, default="",
        help_text="Copied from Person.anonymous_id to link user ↔ person ↔ results.",
    )
    question_pool = models.JSONField()
    responses = models.JSONField(default=dict, blank=True)
    current_page = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="in_progress", db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Survey Progress"
        verbose_name_plural = "Survey Progress"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "status"], name="idx_survey_user_status"),
        ]

    def __str__(self):
        return f"Survey({self.user.username}, {self.status}, page {self.current_page})"


# ---------------------------------------------------------------------------
# Assessment Result (organized & graded per‑assessment data)
# ---------------------------------------------------------------------------

class AssessmentResult(models.Model):
    """Stores organized, gradable results for one assessment within a survey.

    Each record holds every category → question → answer for a single
    assessment key (e.g. "sle"), structured in ``results_data`` so
    business logic can iterate and grade.
    """

    survey_progress = models.ForeignKey(
        SurveyProgress,
        on_delete=models.CASCADE,
        related_name="assessment_results",
    )
    anonymous_id = models.CharField(
        max_length=10, blank=True, default="",
        help_text="Copied from Person.anonymous_id to link user ↔ person ↔ results.",
    )
    assessment_key = models.CharField(max_length=10, db_index=True)
    assessment_label = models.CharField(max_length=255)
    results_data = models.JSONField(
        help_text=(
            "Nested structure: "
            '{"categories": [{"numeral": "I", "title": "…", "description": "…", '
            '"questions": [{"pk": 1, "number": 1, "text": "…", '
            '"answer": 5, "answer_label": "Highly Agree"}]}]}'
        ),
    )
    score = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text="Overall assessment score (populated by grading logic).",
    )
    graded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Assessment Result"
        verbose_name_plural = "Assessment Results"
        ordering = ["assessment_key"]
        constraints = [
            models.UniqueConstraint(
                fields=["survey_progress", "assessment_key"],
                name="unique_result_per_assessment",
            ),
        ]

    def __str__(self):
        return f"{self.assessment_label} – Survey #{self.survey_progress_id}"
