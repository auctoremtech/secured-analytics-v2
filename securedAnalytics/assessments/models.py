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

# Non-breaking-space indent used uniformly for sub-item proxy verbose names
_INDENT = "\u00a0\u00a0\u00a0\u00a0"

# (proxy_name, parent_model, verbose_name, verbose_name_plural)
_PROXY_DEFS = [
    # SLE
    ("SLECategoryProxy", SLECategory, f"{_INDENT}SLE Category", f"{_INDENT}SLE Categories"),
    ("SLEQuestionProxy", SLEQuestion, f"{_INDENT}SLE Question", f"{_INDENT}SLE Questions"),
    ("SupervisorLeadershipEngagementProxy", SupervisorLeadershipEngagement, None, None),
    # MER
    ("MERCategoryProxy", MERCategory, f"{_INDENT}MER Category", f"{_INDENT}MER Categories"),
    ("MERQuestionProxy", MERQuestion, f"{_INDENT}MER Question", f"{_INDENT}MER Questions"),
    ("MentalEmotionalResilienceProxy", MentalEmotionalResilience, None, None),
    # OWB
    ("OWBCategoryProxy", OWBCategory, f"{_INDENT}OWB Category", f"{_INDENT}OWB Categories"),
    ("OWBQuestionProxy", OWBQuestion, f"{_INDENT}OWB Question", f"{_INDENT}OWB Questions"),
    ("OfficerWellbeingProxy", OfficerWellbeing, None, None),
    # PSW
    ("PSWCategoryProxy", PSWCategory, f"{_INDENT}PSW Category", f"{_INDENT}PSW Categories"),
    ("PSWQuestionProxy", PSWQuestion, f"{_INDENT}PSW Question", f"{_INDENT}PSW Questions"),
    ("PsychologicalSafetyProxy", PsychologicalSafety, None, None),
    # OCL
    ("OCLCategoryProxy", OCLCategory, f"{_INDENT}OCL Category", f"{_INDENT}OCL Categories"),
    ("OCLQuestionProxy", OCLQuestion, f"{_INDENT}OCL Question", f"{_INDENT}OCL Questions"),
    ("OrganizationalCultureChangeProxy", OrganizationalCultureChange, None, None),
]


def _make_proxy(name, parent, vn, vnp):
    """Create a proxy model class dynamically."""
    meta_attrs = {"proxy": True, "app_label": "assessments"}
    meta_attrs["verbose_name"] = vn if vn else parent._meta.verbose_name
    meta_attrs["verbose_name_plural"] = vnp if vnp else parent._meta.verbose_name_plural
    meta_cls = type("Meta", (), meta_attrs)
    return type(name, (parent,), {"Meta": meta_cls, "__module__": __name__})


# Generate all proxy models and inject into module namespace
for _name, _parent, _vn, _vnp in _PROXY_DEFS:
    globals()[_name] = _make_proxy(_name, _parent, _vn, _vnp)
