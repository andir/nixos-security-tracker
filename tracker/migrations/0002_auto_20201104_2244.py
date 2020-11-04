# Generated by Django 3.1.3 on 2020-11-04 22:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Patch",
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
                    "filename",
                    models.CharField(
                        help_text="Name of the patch file", max_length=256
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="issue",
            name="description",
            field=models.TextField(
                blank=True, help_text="A description for this issue"
            ),
        ),
        migrations.AlterField(
            model_name="issue",
            name="identifier",
            field=models.CharField(
                help_text="Well-known (external) identifier (e.g. CVE number)",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="package",
            name="patches",
            field=models.ManyToManyField(to="tracker.Patch"),
        ),
    ]
