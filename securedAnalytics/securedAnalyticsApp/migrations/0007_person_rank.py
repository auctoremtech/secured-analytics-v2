from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("securedAnalyticsApp", "0006_person_gender"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="rank",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "— Select —"),
                    ("Officer", "Officer"),
                    ("Deputy", "Deputy"),
                    ("trooper", "trooper"),
                    ("Constable", "Constable"),
                    ("Detective", "Detective"),
                    ("Investigator", "Investigator"),
                    ("Deputy Inspector", "Deputy Inspector"),
                    ("Corporal", "Corporal"),
                    ("Senior Officer", "Senior Officer"),
                    ("Sergeant", "Sergeant"),
                    ("Staff Sergeant", "Staff Sergeant"),
                    ("Lieutenant", "Lieutenant"),
                    ("Captain", "Captain"),
                    ("Commander", "Commander"),
                    ("Major", "Major"),
                    ("Deputy Chief", "Deputy Chief"),
                    ("Assistant Chief", "Assistant Chief"),
                    ("Lieutenant Colonel", "Lieutenant Colonel"),
                    ("Colonel", "Colonel"),
                    ("Undersheriff", "Undersheriff"),
                    ("Chief of Police", "Chief of Police"),
                    ("Sheriff", "Sheriff"),
                    ("Commissioner", "Commissioner"),
                    ("Superintendent", "Superintendent"),
                ],
                default="",
                max_length=30,
            ),
        ),
    ]
