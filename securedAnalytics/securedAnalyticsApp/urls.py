from django.urls import path
from django.views.generic import RedirectView
from .views import (
    PersonListView,
    PersonDetailView,
    PersonCreateView,
    PersonUpdateView,
    LoginPageView,
    WelcomePageView,
    DisclaimerPageView,
    DemographicsView,
    LogoutView,
)

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="login", permanent=False), name="home"),
    path("login/", LoginPageView.as_view(), name="login"),
    path("welcome/", WelcomePageView.as_view(), name="welcome"),
    path("disclaimer/", DisclaimerPageView.as_view(), name="disclaimer"),
    path("demographics/", DemographicsView.as_view(), name="demographics"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("persons/", PersonListView.as_view(), name="person_list"),
    path("persons/<int:pk>/", PersonDetailView.as_view(), name="person_detail"),
    path("persons/create/", PersonCreateView.as_view(), name="person_create"),
    path("persons/<int:pk>/update/", PersonUpdateView.as_view(), name="person_update"),
]
