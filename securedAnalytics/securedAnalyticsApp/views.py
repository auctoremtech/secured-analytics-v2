import random
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, View
from django.urls import reverse_lazy
from django.utils import timezone
from .forms import DemographicsForm
from .models import Person, Users

from assessments.bulk_load import ASSESSMENT_REGISTRY


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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["instance"] = Person.objects.filter(user=self.request.user).first()
        return kwargs


class DemographicsSavedView(LoginRequiredMixin, TemplateView):
    """Confirmation page shown after demographics are saved."""

    login_url = "login"
    template_name = "securedAnalyticsApp/demographics_saved.html"

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
SESSION_KEY_POOL = "survey_pool"       # list of (assessment_key, pk) tuples
SESSION_KEY_PAGE = "survey_page"


class SurveyView(LoginRequiredMixin, View):
    """Serve 10 random non-repeated questions from ALL assessments per page."""

    login_url = "login"

    def _init_session(self, request):
        """Pool every question across all assessments, shuffle, store in session."""
        pool = [
            (key, pk)
            for key, info in ASSESSMENT_REGISTRY.items()
            for pk in info["question_model"].objects.values_list("pk", flat=True).iterator()
        ]
        random.shuffle(pool)
        request.session[SESSION_KEY_POOL] = pool
        request.session[SESSION_KEY_PAGE] = 0

    def _current_page(self, request):
        """Return question objects for the current page slice."""
        pool = request.session.get(SESSION_KEY_POOL, [])
        page = request.session.get(SESSION_KEY_PAGE, 0)
        start = page * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        page_items = pool[start:end]       # list of (key, pk)

        if not page_items:
            return [], True

        # Group PKs by assessment key for efficient querying
        by_key = {}
        for key, pk in page_items:
            by_key.setdefault(key, []).append(pk)

        # Fetch questions from each model
        fetched = {}  # (key, pk) → question instance
        for key, pks in by_key.items():
            info = ASSESSMENT_REGISTRY[key]
            qs = info["question_model"].objects.filter(pk__in=pks).select_related("category")
            for q in qs:
                fetched[(key, q.pk)] = q

        # Preserve shuffled order
        questions = [fetched[tuple(item)] for item in page_items if tuple(item) in fetched]

        is_last = end >= len(pool)
        return questions, is_last

    def get(self, request):
        # Initialise on first visit (no pool in session yet)
        if not request.session.get(SESSION_KEY_POOL):
            self._init_session(request)

        questions, is_last = self._current_page(request)
        if not questions:
            return redirect("survey_done")

        page = request.session.get(SESSION_KEY_PAGE, 0)
        total = len(request.session.get(SESSION_KEY_POOL, []))
        total_pages = (total + QUESTIONS_PER_PAGE - 1) // QUESTIONS_PER_PAGE

        return render(request, "securedAnalyticsApp/survey.html", {
            "questions": questions,
            "is_last": is_last,
            "page_number": page + 1,
            "total_pages": total_pages,
            "start_number": page * QUESTIONS_PER_PAGE,
        })

    def post(self, request):
        page = request.session.get(SESSION_KEY_PAGE, 0)
        request.session[SESSION_KEY_PAGE] = page + 1

        questions, _ = self._current_page(request)
        if not questions:
            return redirect("survey_done")

        return redirect("survey")


class SurveyDoneView(LoginRequiredMixin, TemplateView):
    """Shown when all questions have been presented."""

    login_url = "login"
    template_name = "securedAnalyticsApp/survey_done.html"

    def get(self, request, *args, **kwargs):
        # Clean up session
        for k in (SESSION_KEY_POOL, SESSION_KEY_PAGE):
            request.session.pop(k, None)
        return super().get(request, *args, **kwargs)
