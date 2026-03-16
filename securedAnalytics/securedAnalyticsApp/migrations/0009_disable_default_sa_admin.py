from django.contrib.auth.hashers import check_password
from django.db import migrations


def disable_default_sa_admin(apps, schema_editor):
    Users = apps.get_model("securedAnalyticsApp", "Users")
    for user in Users.objects.filter(username="SA_Admin"):
        if user.email == "sa_admin@example.com" and check_password("SA_Admin01", user.password):
            user.is_active = False
            user.save(update_fields=["is_active"])


class Migration(migrations.Migration):

    dependencies = [
        ("securedAnalyticsApp", "0008_person_anonymous_id_char10"),
    ]

    operations = [
        migrations.RunPython(disable_default_sa_admin, migrations.RunPython.noop),
    ]
