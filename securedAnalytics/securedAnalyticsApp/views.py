from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, View
from django.urls import reverse_lazy
from django.utils import timezone
from .forms import DemographicsForm
from .models import Person, Users


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
    """Logs the user out by clearing the session."""

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect("login")

    def get(self, request, *args, **kwargs):
        return redirect("login")


class PersonListView(ListView):
    model = Person
    template_name = "securedAnalyticsApp/person_list.html"
    context_object_name = "persons"
    paginate_by = 10


class PersonDetailView(DetailView):
    model = Person
    template_name = "securedAnalyticsApp/person_detail.html"
    context_object_name = "person"


class PersonCreateView(CreateView):
    model = Person
    template_name = "securedAnalyticsApp/person_form.html"
    fields = ["user", "phone_number", "address", "city", "state", "zip_code", "date_of_birth", "ethnicity"]
    success_url = reverse_lazy("person_list")


class PersonUpdateView(UpdateView):
    model = Person
    template_name = "securedAnalyticsApp/person_form.html"
    fields = ["phone_number", "address", "city", "state", "zip_code", "date_of_birth", "ethnicity"]
    success_url = reverse_lazy("person_list")
