from django.urls import path
from .views import PersonListView, PersonDetailView, PersonCreateView, PersonUpdateView

urlpatterns = [
    path("persons/", PersonListView.as_view(), name="person_list"),
    path("persons/<int:pk>/", PersonDetailView.as_view(), name="person_detail"),
    path("persons/create/", PersonCreateView.as_view(), name="person_create"),
    path("persons/<int:pk>/update/", PersonUpdateView.as_view(), name="person_update"),
]
