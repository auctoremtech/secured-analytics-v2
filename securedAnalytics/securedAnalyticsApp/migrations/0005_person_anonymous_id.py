import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("securedAnalyticsApp", "0004_person_years_of_service"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="anonymous_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
