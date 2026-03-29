import random
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, View
from django.urls import reverse_lazy
from django.utils import timezone
from .forms import DemographicsForm
from .models import Person, Users, SurveyProgress

from assessments.bulk_load import ASSESSMENT_REGISTRY


_REQUIRED_DEMOGRAPHICS_FIELDS = DemographicsForm.REQUIRED_DEMOGRAPHICS_FIELDS


def _demographics_complete(user):
    """Return True only if the user has a Person record with all required fields."""
    try:
        person = Person.objects.select_related("user").get(user=user)
    except Person.DoesNotExist:
        return False
    for field in _REQUIRED_DEMOGRAPHICS_FIELDS:
        if not getattr(person, field, None):
            return False
    user_obj = person.user
    if not user_obj.first_name or not user_obj.last_name:
        return False
    return True


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
        if request.user.is_authenticated and not _demographics_complete(request.user):
            return redirect("demographics")
        return super().dispatch(request, *args, **kwargs)


class UserRoleMixin:
    """Add user_role to template context."""

    def get_user_role(self):
        return "Staff" if self.request.user.is_staff else "Member"


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
            # Single query to determine redirect: completed → dashboard,
            # in_progress → survey, otherwise → welcome
            latest_status = (
                SurveyProgress.objects
                .filter(user=user)
                .values_list("status", flat=True)
            )
            status_set = set(latest_status)
            if "completed" in status_set:
                return redirect("dashboard")
            if "in_progress" in status_set:
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
        # Clear any previous demographics so the form starts blank
        Person.objects.filter(user=request.user).delete()
        user = request.user
        if user.first_name or user.last_name or getattr(user, "middle_name", "") or getattr(user, "name_suffix", ""):
            user.first_name = ""
            user.last_name = ""
            user.middle_name = ""
            user.name_suffix = ""
            user.save(update_fields=["first_name", "last_name", "middle_name", "name_suffix"])
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class DemographicsSavedView(LoginRequiredMixin, TemplateView):
    """Confirmation page shown after demographics are saved."""

    login_url = "login"
    template_name = "securedAnalyticsApp/demographics_saved.html"

    def get(self, request, *args, **kwargs):
        if not _demographics_complete(request.user):
            return redirect("demographics")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person"] = Person.objects.filter(user=self.request.user).first()
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
            progress = SurveyProgress.objects.create(
                user=request.user,
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
            return redirect("survey_submit")

        return redirect("survey_done")


class SurveySubmitView(LoginRequiredMixin, DemographicsRequiredMixin, View):
    """Marks the survey as completed and shows a dashboard-ready confirmation."""

    login_url = "login"

    def get(self, request):
        SurveyProgress.objects.filter(
            user=request.user, status="in_progress",
        ).update(status="completed")
        return render(request, "securedAnalyticsApp/survey_submit.html")


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_role"] = self.get_user_role()
        return context


LIKERT_LABELS = {
    "5": "Highly Agree",
    "4": "Agree",
    "3": "Neutral",
    "2": "Disagree",
    "1": "Highly Disagree",
}


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
        })
