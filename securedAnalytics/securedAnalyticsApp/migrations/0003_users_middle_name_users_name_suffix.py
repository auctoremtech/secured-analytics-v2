from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("securedAnalyticsApp", "0002_create_default_admin"),
    ]

    operations = [
        migrations.AddField(
            model_name="users",
            name="middle_name",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="users",
            name="name_suffix",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]