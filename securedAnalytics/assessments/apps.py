from django.apps import AppConfig

# Desired display order of model name prefixes inside the assessments app
_MODEL_ORDER = [
    "Supervisor Leadership Engagement",
    "SLE Categor",
    "SLE Question",
    "Mental and Emotional Resilience",
    "MER Categor",
    "MER Question",
    "Officer Wellbeing",
    "OWB Categor",
    "OWB Question",
    "Psychological Safety",
    "PSW Categor",
    "PSW Question",
    "Organizational Culture",
    "OCL Categor",
    "OCL Question",
]

_APP_ORDER = ["securedAnalyticsApp", "assessments"]


class AssessmentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "assessments"
    verbose_name = "Assessments"

    def ready(self):
        from django.contrib import admin

        _original_get_app_list = admin.AdminSite.get_app_list

        def _custom_get_app_list(self, request, app_label=None):
            app_list = _original_get_app_list(self, request, app_label)

            for app in app_list:
                if app["app_label"] == "assessments":
                    sentinel = len(_MODEL_ORDER)
                    app["models"].sort(
                        key=lambda m: next(
                            (i for i, prefix in enumerate(_MODEL_ORDER) if prefix in m.get("name", "")),
                            sentinel,
                        )
                    )

            app_list.sort(
                key=lambda a: _APP_ORDER.index(a["app_label"])
                if a["app_label"] in _APP_ORDER
                else -1
            )
            return app_list

        admin.AdminSite.get_app_list = _custom_get_app_list

        from .bulk_load import get_bulk_load_urls

        _original_get_urls = admin.AdminSite.get_urls

        def _custom_get_urls(self):
            return get_bulk_load_urls() + _original_get_urls(self)

        admin.AdminSite.get_urls = _custom_get_urls
