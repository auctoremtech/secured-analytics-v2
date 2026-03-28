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
    DemographicsSavedView,
    LogoutView,
    SurveyView,
    SurveyDoneView,
)

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="login", permanent=False), name="home"),
    path("login/", LoginPageView.as_view(), name="login"),
    path("welcome/", WelcomePageView.as_view(), name="welcome"),
    path("disclaimer/", DisclaimerPageView.as_view(), name="disclaimer"),
    path("demographics/", DemographicsView.as_view(), name="demographics"),
    path("demographics/saved/", DemographicsSavedView.as_view(), name="demographics_saved"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("survey/", SurveyView.as_view(), name="survey"),
    path("survey/done/", SurveyDoneView.as_view(), name="survey_done"),
    path("persons/", PersonListView.as_view(), name="person_list"),
    path("persons/<int:pk>/", PersonDetailView.as_view(), name="person_detail"),
    path("persons/create/", PersonCreateView.as_view(), name="person_create"),
    path("persons/<int:pk>/update/", PersonUpdateView.as_view(), name="person_update"),
]
