from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("securedAnalyticsApp", "0003_users_middle_name_users_name_suffix"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="years_of_service",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "— Select —"),
                    ("0-2", "0–2 years"),
                    ("2-3", "2–3 years"),
                    ("3-5", "3–5 years"),
                    ("5-7", "5–7 years"),
                ],
                default="",
                max_length=10,
            ),
        ),
    ]
