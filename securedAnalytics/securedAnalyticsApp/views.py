import os
import random
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Max
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, View
from django.urls import reverse_lazy
from django.utils import timezone
from .forms import DemographicsForm
from .models import Person, Users, SurveyProgress, AssessmentResult
from .grading import organize_survey_results, LIKERT_LABELS as _LIKERT_LABELS_INT

from assessments.bulk_load import ASSESSMENT_REGISTRY


_REQUIRED_DEMOGRAPHICS_FIELDS = DemographicsForm.REQUIRED_DEMOGRAPHICS_FIELDS


def _batch_fetch_questions(pool_slice):
    """Group question PKs by assessment key and batch-fetch with categories.

    Returns a dict mapping (key, pk) to the question ORM object.
    """
    by_key = {}
    for key, pk in pool_slice:
        by_key.setdefault(key, []).append(pk)

    fetched = {}
    for key, pks in by_key.items():
        info = ASSESSMENT_REGISTRY.get(key)
        if info:
            qs = info["question_model"].objects.filter(
                pk__in=pks,
            ).select_related("category")
            for q in qs:
                fetched[(key, q.pk)] = q
    return fetched


class DemographicsRequiredMixin:
    """Redirect to demographics if the user hasn't completed them."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            person = Person.objects.filter(user=request.user).first()
            if person is None:
                return redirect("demographics")
            # Cache for UserRoleMixin to avoid duplicate Person queries
            self._cached_person = person
            for field in _REQUIRED_DEMOGRAPHICS_FIELDS:
                if not getattr(person, field, None):
                    return redirect("demographics")
            if not request.user.first_name or not request.user.last_name:
                return redirect("demographics")
        return super().dispatch(request, *args, **kwargs)


class UserRoleMixin:
    """Add user_role and profile image info to template context."""

    def _get_person(self):
        """Return the Person for the current user, cached on the view instance."""
        if not hasattr(self, "_cached_person"):
            self._cached_person = Person.objects.filter(
                user=self.request.user,
            ).first()
        return self._cached_person

    def get_user_role(self):
        person = self._get_person()
        if person and person.rank:
            return person.get_rank_display()
        return "Staff" if self.request.user.is_staff else "Member"

    def get_user_profile_context(self):
        """Return dict with profile_photo_url and avatar_url keys."""
        ctx = {"profile_photo_url": "", "avatar_url": ""}
        person = self._get_person()
        if person:
            if person.profile_photo:
                ctx["profile_photo_url"] = person.profile_photo.url
            elif person.avatar:
                from django.templatetags.static import static
                ctx["avatar_url"] = static(f"securedAnalyticsApp/avatars/{person.avatar}")
        return ctx

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_role"] = self.get_user_role()
        context.update(self.get_user_profile_context())
        return context


class LoginPageView(TemplateView):
    template_name = "securedAnalyticsApp/login.html"
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15
    FAILED_ATTEMPTS_KEY = "failed_login_attempts"
    LOCKED_UNTIL_KEY = "login_locked_until"

    def _is_locked(self, request):
        locked_until = request.session.get(self.LOCKED_UNTIL_KEY)
        if not locked_until:
            return False
        try:
            locked_until_dt = timezone.datetime.fromisoformat(locked_until)
        except ValueError:
            request.session.pop(self.LOCKED_UNTIL_KEY, None)
            return False
        if timezone.is_naive(locked_until_dt):
            locked_until_dt = timezone.make_aware(locked_until_dt, timezone.get_current_timezone())
        if timezone.now() >= locked_until_dt:
            request.session.pop(self.LOCKED_UNTIL_KEY, None)
            request.session.pop(self.FAILED_ATTEMPTS_KEY, None)
            return False
        return True

    def _register_failed_attempt(self, request):
        attempts = request.session.get(self.FAILED_ATTEMPTS_KEY, 0) + 1
        request.session[self.FAILED_ATTEMPTS_KEY] = attempts
        if attempts >= self.MAX_FAILED_ATTEMPTS:
            lockout_until = timezone.now() + timedelta(minutes=self.LOCKOUT_MINUTES)
            request.session[self.LOCKED_UNTIL_KEY] = lockout_until.isoformat()

    def post(self, request, *args, **kwargs):
        if self._is_locked(request):
            return render(
                request,
                self.template_name,
                {"error": "Too many failed login attempts. Please try again later."},
            )

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # exists() short-circuits with LIMIT 1 — faster than fetching all rows
            if SurveyProgress.objects.filter(user=user, status="completed").exists():
                return redirect("dashboard")
            if SurveyProgress.objects.filter(user=user, status="in_progress").exists():
                return redirect("survey")
            return redirect("welcome")
        else:
            self._register_failed_attempt(request)
            return render(request, self.template_name, {"error": "Invalid credentials"})


class WelcomePageView(LoginRequiredMixin, TemplateView):
    """Welcome/Splash screen shown after login with Yes/No buttons."""

    login_url = "login"
    template_name = "securedAnalyticsApp/welcome.html"


class DisclaimerPageView(LoginRequiredMixin, TemplateView):
    """Disclaimer page with Accept/Do Not Accept buttons."""

    login_url = "login"
    template_name = "securedAnalyticsApp/disclaimer.html"


class DemographicsView(LoginRequiredMixin, CreateView):
    """Demographics page for entering Person model information."""

    login_url = "login"
    model = Person
    form_class = DemographicsForm
    template_name = "securedAnalyticsApp/demographics.html"
    success_url = reverse_lazy("demographics_saved")

    def get(self, request, *args, **kwargs):
        # Only clear if demographics are incomplete (avoids wiping on accidental visit)
        existing = Person.objects.filter(user=request.user).first()
        needs_reset = False
        if existing is None:
            needs_reset = True
        else:
            for field in _REQUIRED_DEMOGRAPHICS_FIELDS:
                if not getattr(existing, field, None):
                    needs_reset = True
                    break
            if not request.user.first_name or not request.user.last_name:
                needs_reset = True
        if needs_reset and existing:
            existing.delete()
            user = request.user
            if user.first_name or user.last_name or getattr(user, "middle_name", "") or getattr(user, "name_suffix", ""):
                user.first_name = ""
                user.last_name = ""
                user.middle_name = ""
                user.name_suffix = ""
                user.save(update_fields=["first_name", "last_name", "middle_name", "name_suffix"])
        elif not needs_reset:
            return redirect("demographics_saved")
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class DemographicsSavedView(LoginRequiredMixin, DemographicsRequiredMixin, TemplateView):
    """Confirmation page shown after demographics are saved."""

    login_url = "login"
    template_name = "securedAnalyticsApp/demographics_saved.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person"] = self._cached_person
        return context


class LogoutView(View):
    """Logs the user out by clearing the session. POST-only to prevent CSRF-free logout."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect("login")


class StaffRequiredMixin(UserPassesTestMixin):
    """Restrict access to staff users only."""
    login_url = "login"

    def test_func(self):
        return self.request.user.is_staff


class PersonListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    login_url = "login"
    model = Person
    template_name = "securedAnalyticsApp/person_list.html"
    context_object_name = "persons"
    paginate_by = 10

    def get_queryset(self):
        return super().get_queryset().select_related("user")


class PersonDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    login_url = "login"
    model = Person
    template_name = "securedAnalyticsApp/person_detail.html"
    context_object_name = "person"


class PersonCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    login_url = "login"
    model = Person
    template_name = "securedAnalyticsApp/person_form.html"
    fields = ["user", "phone_number", "address", "city", "state", "zip_code", "date_of_birth", "ethnicity"]
    success_url = reverse_lazy("person_list")


class PersonUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    login_url = "login"
    model = Person
    template_name = "securedAnalyticsApp/person_form.html"
    fields = ["phone_number", "address", "city", "state", "zip_code", "date_of_birth", "ethnicity"]
    success_url = reverse_lazy("person_list")


# ---------------------------------------------------------------------------
# Assessment survey flow
# ---------------------------------------------------------------------------

QUESTIONS_PER_PAGE = 10


class SurveyView(LoginRequiredMixin, DemographicsRequiredMixin, View):
    """Serve 10 random non-repeated questions from ALL assessments per page.

    Survey state is persisted in a SurveyProgress record so users can
    save their progress and resume later with questions in identical order.
    """

    login_url = "login"

    def _get_or_create_progress(self, request):
        """Find existing in-progress survey or create a new one."""
        progress = SurveyProgress.objects.filter(
            user=request.user, status="in_progress",
        ).first()
        if progress is None:
            pool = [
                [key, pk]
                for key, info in ASSESSMENT_REGISTRY.items()
                for pk in info["question_model"]
                    .objects.values_list("pk", flat=True)
            ]
            random.shuffle(pool)
            anon_id = ""
            try:
                anon_id = Person.objects.values_list(
                    "anonymous_id", flat=True,
                ).get(user=request.user)
            except Person.DoesNotExist:
                pass
            progress = SurveyProgress.objects.create(
                user=request.user,
                anonymous_id=anon_id,
                question_pool=pool,
                current_page=0,
            )
        return progress

    def _current_page_slice(self, progress):
        """Return the question pool slice for the current page."""
        start = progress.current_page * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        return progress.question_pool[start:end]

    def _page_items(self, progress):
        """Return question items for the current page with saved responses."""
        page_slice = self._current_page_slice(progress)

        if not page_slice:
            return [], True

        fetched = _batch_fetch_questions(page_slice)

        responses = progress.responses or {}
        question_items = []
        for key, pk in page_slice:
            q_obj = fetched.get((key, pk))
            if q_obj:
                resp_key = f"{key}_{pk}"
                question_items.append({
                    "question": q_obj,
                    "resp_key": resp_key,
                    "saved_value": str(responses.get(resp_key, "")),
                })

        is_last = (progress.current_page + 1) * QUESTIONS_PER_PAGE >= len(progress.question_pool)
        return question_items, is_last

    def _save_page_responses(self, request, progress):
        """Extract Likert responses from POST and merge into progress."""
        page_slice = self._current_page_slice(progress)

        responses = dict(progress.responses or {})
        for key, pk in page_slice:
            resp_key = f"{key}_{pk}"
            value = request.POST.get(resp_key)
            if value in ("1", "2", "3", "4", "5"):
                responses[resp_key] = value
        progress.responses = responses

    def get(self, request):
        progress = self._get_or_create_progress(request)
        question_items, is_last = self._page_items(progress)

        if not question_items:
            return redirect("survey_done")

        total = len(progress.question_pool)
        total_pages = (total + QUESTIONS_PER_PAGE - 1) // QUESTIONS_PER_PAGE
        reviewing = request.session.get("survey_reviewing", False)

        return render(request, "securedAnalyticsApp/survey.html", {
            "question_items": question_items,
            "is_last": is_last,
            "page_number": progress.current_page + 1,
            "total_pages": total_pages,
            "start_number": progress.current_page * QUESTIONS_PER_PAGE,
            "reviewing": reviewing,
            "show_previous": reviewing and progress.current_page > 0,
        })

    def post(self, request):
        progress = SurveyProgress.objects.filter(
            user=request.user, status="in_progress",
        ).first()
        if progress is None:
            return redirect("survey")

        action = request.POST.get("action", "next")
        self._save_page_responses(request, progress)

        if action == "save":
            progress.save(update_fields=["responses", "updated_at"])
            return redirect("survey_saved")

        if action == "previous" and progress.current_page > 0:
            progress.current_page -= 1
            progress.save(update_fields=["responses", "current_page", "updated_at"])
            return redirect("survey")

        # Server-side validation: all questions on the page must be answered
        page_slice = self._current_page_slice(progress)
        responses = progress.responses or {}
        unanswered = [f"{k}_{pk}" for k, pk in page_slice if f"{k}_{pk}" not in responses]
        if unanswered:
            progress.save(update_fields=["responses", "updated_at"])
            question_items, is_last = self._page_items(progress)
            total = len(progress.question_pool)
            total_pages = (total + QUESTIONS_PER_PAGE - 1) // QUESTIONS_PER_PAGE
            reviewing = request.session.get("survey_reviewing", False)
            return render(request, "securedAnalyticsApp/survey.html", {
                "question_items": question_items,
                "is_last": is_last,
                "page_number": progress.current_page + 1,
                "total_pages": total_pages,
                "start_number": progress.current_page * QUESTIONS_PER_PAGE,
                "reviewing": reviewing,
                "show_previous": reviewing and progress.current_page > 0,
                "unanswered_keys": unanswered,
                "validation_error": True,
            })

        # action == "next" or "done" — advance page
        progress.current_page += 1
        progress.save(update_fields=["responses", "current_page", "updated_at"])

        total = len(progress.question_pool)
        if progress.current_page * QUESTIONS_PER_PAGE >= total:
            return redirect("survey_done")

        return redirect("survey")


class SurveyDoneView(LoginRequiredMixin, DemographicsRequiredMixin, View):
    """Shown when all questions have been presented.

    Offers the user a choice to review their answers or submit them.
    """

    login_url = "login"

    def get(self, request):
        return render(request, "securedAnalyticsApp/survey_done.html")

    def post(self, request):
        action = request.POST.get("action", "")

        if action == "review":
            progress = SurveyProgress.objects.filter(
                user=request.user, status="in_progress",
            ).first()
            if progress:
                progress.current_page = 0
                progress.save(update_fields=["current_page", "updated_at"])
            request.session["survey_reviewing"] = True
            return redirect("survey")

        if action == "submit":
            request.session.pop("survey_reviewing", None)
            # Process submission inline (POST-only state mutation)
            in_progress = list(SurveyProgress.objects.filter(
                user=request.user, status="in_progress",
            ))
            for sp in in_progress:
                organize_survey_results(sp)
            if in_progress:
                SurveyProgress.objects.filter(
                    pk__in=[sp.pk for sp in in_progress],
                ).update(status="completed", updated_at=timezone.now())
            return render(request, "securedAnalyticsApp/survey_submit.html")

        return redirect("survey_done")


class SurveySavedView(LoginRequiredMixin, DemographicsRequiredMixin, TemplateView):
    """Confirmation page when the user saves progress mid-survey."""

    login_url = "login"
    template_name = "securedAnalyticsApp/survey_saved.html"


class DashboardView(LoginRequiredMixin, UserRoleMixin, TemplateView):
    """Post-survey dashboard with sidebar navigation."""

    login_url = "login"
    template_name = "securedAnalyticsApp/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not SurveyProgress.objects.filter(user=request.user, status="completed").exists():
                return redirect("welcome")
        return super().dispatch(request, *args, **kwargs)


LIKERT_LABELS = {str(k): v for k, v in _LIKERT_LABELS_INT.items()}


class AssessmentHistoryView(LoginRequiredMixin, UserRoleMixin, View):
    """List all completed assessments for the logged-in user."""

    login_url = "login"

    def get(self, request):
        completed = (
            SurveyProgress.objects
            .filter(user=request.user, status="completed")
            .only("pk", "question_pool", "responses", "updated_at")
            .order_by("-updated_at")
        )

        assessments = []
        for sp in completed:
            total_questions = len(sp.question_pool) if sp.question_pool else 0
            total_answered = len(sp.responses) if sp.responses else 0
            assessments.append({
                "pk": sp.pk,
                "completed_at": sp.updated_at,
                "total_questions": total_questions,
                "total_answered": total_answered,
            })

        return render(request, "securedAnalyticsApp/assessment_history.html", {
            "assessments": assessments,
            "user_role": self.get_user_role(),
            **self.get_user_profile_context(),
        })


class AssessmentReviewView(LoginRequiredMixin, UserRoleMixin, View):
    """Show all questions and the user's answers for a completed assessment."""

    login_url = "login"

    def get(self, request, pk):
        try:
            progress = SurveyProgress.objects.get(
                pk=pk, user=request.user, status="completed",
            )
        except SurveyProgress.DoesNotExist:
            return redirect("assessment_history")

        pool = progress.question_pool or []
        responses = progress.responses or {}

        fetched = _batch_fetch_questions(pool)

        items = []
        for idx, (key, q_pk) in enumerate(pool, start=1):
            q_obj = fetched.get((key, q_pk))
            if q_obj:
                resp_key = f"{key}_{q_pk}"
                value = responses.get(resp_key, "")
                info = ASSESSMENT_REGISTRY.get(key, {})
                items.append({
                    "number": idx,
                    "text": q_obj.text,
                    "category": q_obj.category.title if q_obj.category else "",
                    "assessment": info.get("label", key.upper()),
                    "value": value,
                    "label": LIKERT_LABELS.get(str(value), "Not Answered"),
                })

        return render(request, "securedAnalyticsApp/assessment_review.html", {
            "progress": progress,
            "items": items,
            "user_role": self.get_user_role(),
            **self.get_user_profile_context(),
        })


class ProfilePhotoView(LoginRequiredMixin, View):
    """Allow user to upload a photo or select a preset avatar."""

    login_url = "login"

    def get(self, request):
        person = Person.objects.filter(user=request.user).first()
        return render(request, "securedAnalyticsApp/profile_photo.html", {
            "person": person,
            "avatar_choices": Person.AVATAR_CHOICES[1:],  # skip blank
        })

    # 5 MB max upload size
    MAX_UPLOAD_BYTES = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    ALLOWED_CONTENT_TYPES = {
        "image/jpeg", "image/png", "image/gif", "image/webp",
    }

    def post(self, request):
        person = Person.objects.filter(user=request.user).first()
        if not person:
            return redirect("dashboard")

        action = request.POST.get("action", "")

        if action == "upload" and request.FILES.get("photo"):
            photo = request.FILES["photo"]
            # Validate file size
            if photo.size > self.MAX_UPLOAD_BYTES:
                return render(request, "securedAnalyticsApp/profile_photo.html", {
                    "person": person,
                    "avatar_choices": Person.AVATAR_CHOICES[1:],
                    "error": "File too large. Maximum size is 5 MB.",
                })
            # Validate file extension
            ext = os.path.splitext(photo.name)[1].lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                return render(request, "securedAnalyticsApp/profile_photo.html", {
                    "person": person,
                    "avatar_choices": Person.AVATAR_CHOICES[1:],
                    "error": "Invalid file type. Allowed: JPG, PNG, GIF, WebP.",
                })
            # Validate content type
            if photo.content_type not in self.ALLOWED_CONTENT_TYPES:
                return render(request, "securedAnalyticsApp/profile_photo.html", {
                    "person": person,
                    "avatar_choices": Person.AVATAR_CHOICES[1:],
                    "error": "Invalid file type. Allowed: JPG, PNG, GIF, WebP.",
                })
            # Clear any selected avatar when uploading a photo
            person.avatar = ""
            person.profile_photo = photo
            person.save(update_fields=["profile_photo", "avatar", "updated_at"])
        elif action == "avatar":
            avatar_value = request.POST.get("avatar", "")
            valid_avatars = [c[0] for c in Person.AVATAR_CHOICES]
            if avatar_value in valid_avatars:
                # Clear uploaded photo when selecting an avatar
                if person.profile_photo:
                    person.profile_photo.delete(save=False)
                person.avatar = avatar_value
                person.save(update_fields=["profile_photo", "avatar", "updated_at"])
        elif action == "remove":
            if person.profile_photo:
                person.profile_photo.delete(save=False)
            person.avatar = ""
            person.save(update_fields=["profile_photo", "avatar", "updated_at"])

        return redirect("profile_photo")


class AnalyticsView(LoginRequiredMixin, DemographicsRequiredMixin, UserRoleMixin, TemplateView):
    """Analytics page with chart type selection."""

    login_url = "login"
    template_name = "securedAnalyticsApp/analytics.html"


VALID_CHART_TYPES = {"pie", "bar", "line", "funnel"}
CHART_TITLES = {
    "pie": "Pie Chart",
    "bar": "Bar Chart",
    "line": "Line Chart",
    "funnel": "Funnel Chart",
}


class AnalyticsChartView(LoginRequiredMixin, DemographicsRequiredMixin, UserRoleMixin, TemplateView):
    """Render a specific chart type using assessment data."""

    login_url = "login"
    template_name = "securedAnalyticsApp/analytics_chart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chart_type = self.kwargs.get("chart_type", "pie")
        if chart_type not in VALID_CHART_TYPES:
            chart_type = "pie"

        context["chart_type"] = chart_type
        context["chart_title"] = CHART_TITLES.get(chart_type, "Chart")

        # Fetch the user's most recent AssessmentResult per assessment_key
        # Subquery gets the latest id per key; outer query fetches only those rows
        latest_ids = (
            AssessmentResult.objects
            .filter(survey_progress__user=self.request.user)
            .values("assessment_key")
            .annotate(latest_id=Max("id"))
            .values_list("latest_id", flat=True)
        )
        latest = list(
            AssessmentResult.objects
            .filter(id__in=latest_ids)
            .order_by("assessment_key")
        )

        labels = []
        scores = []
        category_data = []
        for r in latest:
            labels.append(r.assessment_label or r.assessment_key)
            scores.append(float(r.score) if r.score else 0)
            cats = []
            if r.results_data and "categories" in r.results_data:
                for cat in r.results_data["categories"]:
                    cats.append({
                        "title": f"{cat.get('numeral', '')}. {cat.get('title', '')}",
                        "score": cat.get("score", 0),
                    })
            category_data.append({
                "assessment": r.assessment_label or r.assessment_key,
                "categories": cats,
            })

        context["chart_data"] = {
            "labels": labels,
            "scores": scores,
            "category_data": category_data,
        }
        context["has_data"] = len(latest) > 0
        return context
