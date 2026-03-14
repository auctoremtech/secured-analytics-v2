import string

from django.db import migrations, models
from django.utils.crypto import get_random_string


def _generate_unique_id(existing_ids):
    allowed_chars = string.ascii_uppercase + string.digits
    while True:
        candidate = get_random_string(10, allowed_chars=allowed_chars)
        if candidate not in existing_ids:
            return candidate


def normalize_anonymous_ids(apps, schema_editor):
    Person = apps.get_model("securedAnalyticsApp", "Person")
    existing_ids = set(
        Person.objects.exclude(anonymous_id__isnull=True)
        .exclude(anonymous_id="")
        .values_list("anonymous_id", flat=True)
    )

    for person in Person.objects.all():
        value = person.anonymous_id or ""
        if len(value) == 10 and value.isalnum():
            continue
        new_id = _generate_unique_id(existing_ids)
        person.anonymous_id = new_id
        person.save(update_fields=["anonymous_id"])
        existing_ids.add(new_id)


class Migration(migrations.Migration):

    dependencies = [
        ("securedAnalyticsApp", "0007_person_rank"),
    ]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="anonymous_id",
            field=models.CharField(
                default="",
                editable=False,
                max_length=10,
                unique=True,
            ),
        ),
        migrations.RunPython(normalize_anonymous_ids, migrations.RunPython.noop),
    ]
