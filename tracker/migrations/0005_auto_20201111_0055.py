# Generated by Django 3.1.3 on 2020-11-11 00:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0004_auto_20201110_1412"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="packageadvisorystatus",
            name="issue",
        ),
        migrations.RemoveField(
            model_name="packageadvisorystatus",
            name="package",
        ),
        migrations.RemoveField(
            model_name="scmrevision",
            name="release",
        ),
        migrations.RemoveField(
            model_name="issue",
            name="packages",
        ),
        migrations.DeleteModel(
            name="Package",
        ),
        migrations.DeleteModel(
            name="PackageAdvisoryStatus",
        ),
        migrations.DeleteModel(
            name="Patch",
        ),
        migrations.DeleteModel(
            name="Release",
        ),
        migrations.DeleteModel(
            name="SCMRevision",
        ),
    ]
