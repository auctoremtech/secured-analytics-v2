from django.contrib import admin

from securedAnalyticsApp.models import (
    SLEQuestion, MERQuestion, OWBQuestion, PSWQuestion, OCLQuestion,
)

from .models import (
    SLECategoryProxy,
    SLEQuestionProxy,
    SupervisorLeadershipEngagementProxy,
    MentalEmotionalResilienceProxy,
    MERCategoryProxy,
    MERQuestionProxy,
    OfficerWellbeingProxy,
    OWBCategoryProxy,
    OWBQuestionProxy,
    PsychologicalSafetyProxy,
    PSWCategoryProxy,
    PSWQuestionProxy,
    OrganizationalCultureChangeProxy,
    OCLCategoryProxy,
    OCLQuestionProxy,
)


# ---------------------------------------------------------------------------
# Base admin classes — shared configuration for all assessment types
# ---------------------------------------------------------------------------

class BaseCategoryAdmin(admin.ModelAdmin):
    list_display = ("numeral", "title", "description", "order")
    ordering = ("order",)


class BaseQuestionAdmin(admin.ModelAdmin):
    list_display = ("number", "category", "text")
    list_filter = ("category",)
    list_select_related = ("category",)
    ordering = ("number",)


class BaseAssessmentAdmin(admin.ModelAdmin):
    list_display = ("title", "assessed_at", "updated_at")
    list_filter = ("assessed_at",)
    search_fields = ("title",)
    ordering = ("-assessed_at",)

    def has_add_permission(self, request):
        return False


# ---------------------------------------------------------------------------
# Data-driven registration
# ---------------------------------------------------------------------------

_ASSESSMENT_DEFS = [
    # (category_proxy, question_model, question_proxy, assessment_proxy)
    (SLECategoryProxy, SLEQuestion, SLEQuestionProxy, SupervisorLeadershipEngagementProxy),
    (MERCategoryProxy, MERQuestion, MERQuestionProxy, MentalEmotionalResilienceProxy),
    (OWBCategoryProxy, OWBQuestion, OWBQuestionProxy, OfficerWellbeingProxy),
    (PSWCategoryProxy, PSWQuestion, PSWQuestionProxy, PsychologicalSafetyProxy),
    (OCLCategoryProxy, OCLQuestion, OCLQuestionProxy, OrganizationalCultureChangeProxy),
]


def _register_assessment(cat_proxy, q_model, q_proxy, assess_proxy):
    """Register category, question, and assessment admin for one assessment type."""
    inline_cls = type(
        f"{q_model.__name__}Inline",
        (admin.TabularInline,),
        {"model": q_model, "extra": 0, "ordering": ("number",)},
    )
    cat_admin = type(
        f"{cat_proxy.__name__}Admin",
        (BaseCategoryAdmin,),
        {"inlines": [inline_cls]},
    )
    q_admin = type(f"{q_proxy.__name__}Admin", (BaseQuestionAdmin,), {})
    assess_admin = type(f"{assess_proxy.__name__}Admin", (BaseAssessmentAdmin,), {})

    admin.site.register(cat_proxy, cat_admin)
    admin.site.register(q_proxy, q_admin)
    admin.site.register(assess_proxy, assess_admin)


for _def in _ASSESSMENT_DEFS:
    _register_assessment(*_def)
