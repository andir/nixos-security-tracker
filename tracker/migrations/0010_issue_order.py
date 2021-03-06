# Generated by Django 3.1.3 on 2020-12-01 00:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0009_githubevent"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="issue",
            options={"ordering": ("-published_date",)},
        ),
        migrations.AddField(
            model_name="issue",
            name="published_date",
            field=models.DateTimeField(
                default=None,
                help_text="The date and time when the issue was first published",
                null=True,
            ),
            preserve_default=False,
        ),
    ]
