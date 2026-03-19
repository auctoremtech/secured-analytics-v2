from securedAnalyticsApp.models import (
    SLECategory,
    SLEQuestion,
    SupervisorLeadershipEngagement,
    MentalEmotionalResilience,
    MERCategory,
    MERQuestion,
    OfficerWellbeing,
    OWBCategory,
    OWBQuestion,
    PsychologicalSafety,
    PSWCategory,
    PSWQuestion,
    OrganizationalCultureChange,
    OCLCategory,
    OCLQuestion,
)


class SLECategoryProxy(SLECategory):
    class Meta:
        proxy = True
        verbose_name = "\u00a0\u00a0\u00a0\u00a0SLE Category"
        verbose_name_plural = "\u00a0\u00a0\u00a0\u00a0SLE Categories"


class SLEQuestionProxy(SLEQuestion):
    class Meta:
        proxy = True
        verbose_name = "    SLE Question"
        verbose_name_plural = "    SLE Questions"


class SupervisorLeadershipEngagementProxy(SupervisorLeadershipEngagement):
    class Meta:
        proxy = True
        verbose_name = SupervisorLeadershipEngagement._meta.verbose_name
        verbose_name_plural = SupervisorLeadershipEngagement._meta.verbose_name_plural


class MentalEmotionalResilienceProxy(MentalEmotionalResilience):
    class Meta:
        proxy = True
        verbose_name = MentalEmotionalResilience._meta.verbose_name
        verbose_name_plural = MentalEmotionalResilience._meta.verbose_name_plural


class MERCategoryProxy(MERCategory):
    class Meta:
        proxy = True
        verbose_name = "    MER Category"
        verbose_name_plural = "    MER Categories"


class MERQuestionProxy(MERQuestion):
    class Meta:
        proxy = True
        verbose_name = "    MER Question"
        verbose_name_plural = "    MER Questions"

class OfficerWellbeingProxy(OfficerWellbeing):
    class Meta:
        proxy = True
        verbose_name = OfficerWellbeing._meta.verbose_name
        verbose_name_plural = OfficerWellbeing._meta.verbose_name_plural


class OWBCategoryProxy(OWBCategory):
    class Meta:
        proxy = True
        verbose_name = "\u00a0\u00a0\u00a0\u00a0OWB Category"
        verbose_name_plural = "\u00a0\u00a0\u00a0\u00a0OWB Categories"


class OWBQuestionProxy(OWBQuestion):
    class Meta:
        proxy = True
        verbose_name = "\u00a0\u00a0\u00a0\u00a0OWB Question"
        verbose_name_plural = "\u00a0\u00a0\u00a0\u00a0OWB Questions"


class PsychologicalSafetyProxy(PsychologicalSafety):
    class Meta:
        proxy = True
        verbose_name = PsychologicalSafety._meta.verbose_name
        verbose_name_plural = PsychologicalSafety._meta.verbose_name_plural


class PSWCategoryProxy(PSWCategory):
    class Meta:
        proxy = True
        verbose_name = "\u00a0\u00a0\u00a0\u00a0PSW Category"
        verbose_name_plural = "\u00a0\u00a0\u00a0\u00a0PSW Categories"


class PSWQuestionProxy(PSWQuestion):
    class Meta:
        proxy = True
        verbose_name = "\u00a0\u00a0\u00a0\u00a0PSW Question"
        verbose_name_plural = "\u00a0\u00a0\u00a0\u00a0PSW Questions"


class OrganizationalCultureChangeProxy(OrganizationalCultureChange):
    class Meta:
        proxy = True
        verbose_name = OrganizationalCultureChange._meta.verbose_name
        verbose_name_plural = OrganizationalCultureChange._meta.verbose_name_plural


class OCLCategoryProxy(OCLCategory):
    class Meta:
        proxy = True
        verbose_name = "\u00a0\u00a0\u00a0\u00a0OCL Category"
        verbose_name_plural = "\u00a0\u00a0\u00a0\u00a0OCL Categories"


class OCLQuestionProxy(OCLQuestion):
    class Meta:
        proxy = True
        verbose_name = "\u00a0\u00a0\u00a0\u00a0OCL Question"
        verbose_name_plural = "\u00a0\u00a0\u00a0\u00a0OCL Questions"