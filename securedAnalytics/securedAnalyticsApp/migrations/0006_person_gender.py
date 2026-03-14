from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("securedAnalyticsApp", "0005_person_anonymous_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="gender",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "— Select —"),
                    ("Male", "Male"),
                    ("Female", "Female"),
                ],
                default="",
                max_length=10,
            ),
        ),
    ]
