from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, View
from django.urls import reverse_lazy
from django.contrib.auth.hashers import check_password
from .models import Person, Users


class LoginRequiredMixin:
    """Mixin that checks if user is logged in via session."""

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("login")
        return super().dispatch(request, *args, **kwargs)


class LoginPageView(TemplateView):
    template_name = "securedAnalyticsApp/login.html"

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            user = Users.objects.get(username=username, is_active=True)
            if check_password(password, user.password):
                # Store user_id in session to simulate login
                request.session["user_id"] = user.id
                return redirect("welcome")
            else:
                return render(request, self.template_name, {"error": "Invalid credentials"})
        except Users.DoesNotExist:
            # For now, redirect back to login with error
            return render(request, self.template_name, {"error": "Invalid credentials"})


class WelcomePageView(LoginRequiredMixin, TemplateView):
    """Welcome/Splash screen shown after login with Yes/No buttons."""

    template_name = "securedAnalyticsApp/welcome.html"


class DisclaimerPageView(LoginRequiredMixin, TemplateView):
    """Disclaimer page with Accept/Do Not Accept buttons."""

    template_name = "securedAnalyticsApp/disclaimer.html"


class DemographicsView(LoginRequiredMixin, CreateView):
    """Demographics page for entering Person model information."""

    model = Person
    template_name = "securedAnalyticsApp/demographics.html"
    fields = ["phone_number", "address", "city", "state", "zip_code", "date_of_birth", "ethnicity"]
    success_url = reverse_lazy("person_list")

    def form_valid(self, form):
        # Get the current user from session
        user_id = self.request.session.get("user_id")
        if user_id:
            try:
                user = Users.objects.get(id=user_id)
                form.instance.user = user
            except Users.DoesNotExist:
                return redirect("login")
        return super().form_valid(form)


class LogoutView(View):
    """Logs the user out by clearing the session."""

    def get(self, request, *args, **kwargs):
        # Clear the session
        request.session.flush()
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
