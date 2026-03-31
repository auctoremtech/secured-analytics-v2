from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from .models import Users, Person, AssessmentResult, SurveyProgress

# Desired model ordering within the securedAnalyticsApp section
_MODEL_ORDER = {"users": 0, "person": 1, "assessmentresult": 2}


def _sort_app_models(app_list):
    for app in app_list:
        if app["app_label"] == "securedAnalyticsApp":
            app["models"].sort(
                key=lambda m: _MODEL_ORDER.get(m["object_name"].lower(), 99)
            )
    return app_list


# Monkey-patch the default admin site to enforce ordering
_original_get_app_list = admin.AdminSite.get_app_list


def _patched_get_app_list(self, request, app_label=None):
    app_list = _original_get_app_list(self, request, app_label)
    return _sort_app_models(app_list)


admin.AdminSite.get_app_list = _patched_get_app_list


@admin.register(Users)
class UsersAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "middle_name", "last_name", "name_suffix", "is_active", "date_joined")
    search_fields = ("username", "email", "first_name", "middle_name", "last_name", "name_suffix")
    list_filter = ("is_active", "is_staff", "date_joined")
    ordering = ("-date_joined",)

    # Extend the default UserAdmin fieldsets to include custom fields
    fieldsets = UserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("middle_name", "name_suffix")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional Info", {"fields": ("middle_name", "name_suffix")}),
    )


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("user", "anonymous_id", "phone_number", "ethnicity", "city", "state", "created_at", "assessment_results_link")
    list_select_related = ("user",)
    search_fields = ("user__username", "phone_number", "city")
    list_filter = ("ethnicity", "city", "state", "created_at")
    readonly_fields = ("assessment_results_link",)
    ordering = ("-created_at",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _result_count=Count("user__survey_sessions__assessment_results"),
        )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:
            fieldsets = list(fieldsets) + [
                ("Assessment Results", {"fields": ("assessment_results_link",)}),
            ]
        return fieldsets

    @admin.display(description="Assessment Results")
    def assessment_results_link(self, obj):
        if not obj or not obj.pk:
            return "-"
        # Use annotated count from get_queryset; fall back to query for detail views
        count = getattr(obj, "_result_count", None)
        if count is None:
            count = AssessmentResult.objects.filter(
                survey_progress__user=obj.user,
            ).count()
        if count:
            url = reverse("admin:securedAnalyticsApp_assessmentresult_changelist")
            filtered_url = f"{url}?{urlencode({'q': obj.user.username})}"
            return format_html(
                '<a href="{}">View {} result{}</a>',
                filtered_url, count, "s" if count != 1 else "",
            )
        return "None"


@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = (
        "get_user", "anonymous_id", "assessment_label", "assessment_key",
        "score", "graded_at", "view_detail_link",
    )
    list_select_related = ("survey_progress", "survey_progress__user")
    list_filter = ("assessment_key", "graded_at")
    search_fields = (
        "assessment_label",
        "survey_progress__user__username",
        "survey_progress__user__first_name",
        "survey_progress__user__last_name",
    )
    readonly_fields = ("anonymous_id", "results_data", "created_at")
    ordering = ("-created_at",)

    @admin.display(description="User", ordering="survey_progress__user__username")
    def get_user(self, obj):
        user = obj.survey_progress.user
        return f"{user.get_full_name()} ({user.username})"

    @admin.display(description="Details")
    def view_detail_link(self, obj):
        url = reverse(
            "admin:securedAnalyticsApp_assessmentresult_grade_detail",
            args=[obj.pk],
        )
        return format_html('<a href="{}">View Grades</a>', url)

    def get_urls(self):
        custom_urls = [
            path(
                "<int:pk>/grades/",
                self.admin_site.admin_view(self.grade_detail_view),
                name="securedAnalyticsApp_assessmentresult_grade_detail",
            ),
        ]
        return custom_urls + super().get_urls()

    def grade_detail_view(self, request, pk):
        result = AssessmentResult.objects.select_related(
            "survey_progress", "survey_progress__user",
        ).get(pk=pk)
        user = result.survey_progress.user
        data = result.results_data or {}
        categories = data.get("categories", [])

        context = {
            **self.admin_site.each_context(request),
            "title": f"Grade Detail – {result.assessment_label}",
            "result": result,
            "assessed_user": user,
            "categories": categories,
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request,
            "admin/securedAnalyticsApp/assessmentresult/grade_detail.html",
            context,
        )
