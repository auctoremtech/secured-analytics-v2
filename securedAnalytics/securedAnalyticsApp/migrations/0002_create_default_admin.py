from django.db import migrations


def create_default_admin(apps, schema_editor):
    """Create the default admin user if it doesn't exist."""
    Users = apps.get_model("securedAnalyticsApp", "Users")
    
    if not Users.objects.filter(username="SA_Admin").exists():
        Users.objects.create(
            username="SA_Admin",
            email="sa_admin@example.com",
            password="SA_Admin01",
            first_name="Admin",
            last_name="User",
            is_active=True,
        )


def remove_default_admin(apps, schema_editor):
    """Remove the default admin user (reverse migration)."""
    Users = apps.get_model("securedAnalyticsApp", "Users")
    Users.objects.filter(username="SA_Admin").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("securedAnalyticsApp", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_admin, remove_default_admin),
    ]
