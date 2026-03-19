from django.apps import AppConfig


class AssessmentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "assessments"
    verbose_name = "Assessments"

    def ready(self):
        from django.contrib import admin

        _original_get_app_list = admin.AdminSite.get_app_list

        def _custom_get_app_list(self, request, app_label=None):
            app_list = _original_get_app_list(self, request, app_label)
            # Desired order: SLE assessment + its sub-models, then MER assessment + its sub-models
            order = [
                "Supervisor Leadership Engagement",   # heading
                "SLE Categor",                         # SLE Categories
                "SLE Question",                        # SLE Questions
                "Mental and Emotional Resilience",     # heading
                "MER Categor",                         # MER Categories
                "MER Question",                        # MER Questions
                "Officer Wellbeing",                   # heading
                "OWB Categor",                         # OWB Categories
                "OWB Question",                        # OWB Questions
                "Psychological Safety",                # heading
                "PSW Categor",                         # PSW Categories
                "PSW Question",                        # PSW Questions
                "Organizational Culture",              # heading
                "OCL Categor",                         # OCL Categories
                "OCL Question",                        # OCL Questions
            ]
            for app in app_list:
                if app["app_label"] == "assessments":
                    models = app["models"]

                    def _sort_key(m):
                        name = m.get("name", "")
                        for i, prefix in enumerate(order):
                            if prefix in name:
                                return i
                        return len(order)

                    app["models"] = sorted(models, key=_sort_key)

            # Ensure securedAnalyticsApp appears before assessments
            app_order = ["securedAnalyticsApp", "assessments"]
            def _app_sort_key(a):
                label = a.get("app_label", "")
                if label in app_order:
                    return app_order.index(label)
                return -1  # other apps (auth, etc.) stay at the top

            app_list.sort(key=_app_sort_key)
            return app_list

        admin.AdminSite.get_app_list = _custom_get_app_list
