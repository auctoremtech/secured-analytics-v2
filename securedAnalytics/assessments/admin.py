from django.contrib import admin

from securedAnalyticsApp.models import SLEQuestion, MERQuestion, OWBQuestion, PSWQuestion, OCLQuestion

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


class SLEQuestionInline(admin.TabularInline):
    model = SLEQuestion
    extra = 0
    ordering = ("number",)


@admin.register(SLECategoryProxy)
class SLECategoryAdmin(admin.ModelAdmin):
    list_display = ("numeral", "title", "description", "order")
    ordering = ("order",)
    inlines = [SLEQuestionInline]


@admin.register(SLEQuestionProxy)
class SLEQuestionAdmin(admin.ModelAdmin):
    list_display = ("number", "category", "text")
    list_filter = ("category",)
    ordering = ("number",)


@admin.register(SupervisorLeadershipEngagementProxy)
class SupervisorLeadershipEngagementAdmin(admin.ModelAdmin):
    list_display = ("title", "assessed_at", "updated_at")
    list_filter = ("assessed_at",)
    search_fields = ("title",)
    ordering = ("-assessed_at",)

    def has_add_permission(self, request):
        return False


@admin.register(MentalEmotionalResilienceProxy)
class MentalEmotionalResilienceAdmin(admin.ModelAdmin):
    list_display = ("title", "assessed_at", "updated_at")
    list_filter = ("assessed_at",)
    search_fields = ("title",)
    ordering = ("-assessed_at",)

    def has_add_permission(self, request):
        return False


class MERQuestionInline(admin.TabularInline):
    model = MERQuestion
    extra = 0
    ordering = ("number",)


@admin.register(MERCategoryProxy)
class MERCategoryAdmin(admin.ModelAdmin):
    list_display = ("numeral", "title", "description", "order")
    ordering = ("order",)
    inlines = [MERQuestionInline]


@admin.register(MERQuestionProxy)
class MERQuestionAdmin(admin.ModelAdmin):
    list_display = ("number", "category", "text")
    list_filter = ("category",)
    ordering = ("number",)


@admin.register(OfficerWellbeingProxy)
class OfficerWellbeingAdmin(admin.ModelAdmin):
    list_display = ("title", "assessed_at", "updated_at")
    list_filter = ("assessed_at",)
    search_fields = ("title",)
    ordering = ("-assessed_at",)

    def has_add_permission(self, request):
        return False


class OWBQuestionInline(admin.TabularInline):
    model = OWBQuestion
    extra = 0
    ordering = ("number",)


@admin.register(OWBCategoryProxy)
class OWBCategoryAdmin(admin.ModelAdmin):
    list_display = ("numeral", "title", "description", "order")
    ordering = ("order",)
    inlines = [OWBQuestionInline]


@admin.register(OWBQuestionProxy)
class OWBQuestionAdmin(admin.ModelAdmin):
    list_display = ("number", "category", "text")
    list_filter = ("category",)
    ordering = ("number",)


@admin.register(PsychologicalSafetyProxy)
class PsychologicalSafetyAdmin(admin.ModelAdmin):
    list_display = ("title", "assessed_at", "updated_at")
    list_filter = ("assessed_at",)
    search_fields = ("title",)
    ordering = ("-assessed_at",)

    def has_add_permission(self, request):
        return False


class PSWQuestionInline(admin.TabularInline):
    model = PSWQuestion
    extra = 0
    ordering = ("number",)


@admin.register(PSWCategoryProxy)
class PSWCategoryAdmin(admin.ModelAdmin):
    list_display = ("numeral", "title", "description", "order")
    ordering = ("order",)
    inlines = [PSWQuestionInline]


@admin.register(PSWQuestionProxy)
class PSWQuestionAdmin(admin.ModelAdmin):
    list_display = ("number", "category", "text")
    list_filter = ("category",)
    ordering = ("number",)


@admin.register(OrganizationalCultureChangeProxy)
class OrganizationalCultureChangeAdmin(admin.ModelAdmin):
    list_display = ("title", "assessed_at", "updated_at")
    list_filter = ("assessed_at",)
    search_fields = ("title",)
    ordering = ("-assessed_at",)

    def has_add_permission(self, request):
        return False


class OCLQuestionInline(admin.TabularInline):
    model = OCLQuestion
    extra = 0
    ordering = ("number",)


@admin.register(OCLCategoryProxy)
class OCLCategoryAdmin(admin.ModelAdmin):
    list_display = ("numeral", "title", "description", "order")
    ordering = ("order",)
    inlines = [OCLQuestionInline]


@admin.register(OCLQuestionProxy)
class OCLQuestionAdmin(admin.ModelAdmin):
    list_display = ("number", "category", "text")
    list_filter = ("category",)
    ordering = ("number",)
