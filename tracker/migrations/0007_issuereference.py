# Generated by Django 3.1.3 on 2020-11-11 17:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0006_issue_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="IssueReference",
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
                    "uri",
                    models.TextField(
                        help_text="URI for additional resources for an issue"
                    ),
                ),
                (
                    "issue",
                    models.ForeignKey(
                        help_text="Issue this reference ",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="references",
                        to="tracker.issue",
                    ),
                ),
            ],
        ),
    ]