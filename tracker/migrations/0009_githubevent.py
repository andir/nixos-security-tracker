# Generated by Django 3.1.3 on 2020-11-30 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0008_issue_status_reason"),
    ]

    operations = [
        migrations.CreateModel(
            name="GitHubEvent",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "received_at",
                    models.DateTimeField(
                        auto_now_add=True, help_text="Datetime when this entry was made"
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        help_text="Content of the X-GitHub-Event HTTP header",
                        max_length=32,
                    ),
                ),
                (
                    "data",
                    models.JSONField(
                        help_text="The RAW event data as received from GitHub"
                    ),
                ),
            ],
        ),
    ]
