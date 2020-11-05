from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Release(models.Model):
    """
    A NixOS release
    """

    alive = models.BooleanField(
        default=False, help_text="The release is still supported"
    )


class SCMRevision(models.Model):
    """
    A unique version in the SCM repository
    """

    identifier = models.CharField(
        max_length=255, help_text="The revision in the SCM repository"
    )
    release = models.ForeignKey(
        Release,
        on_delete=models.CASCADE,
        help_text="The release this revision belongs to",
    )


class Package(models.Model):
    """
    A version of a package. e.g. python-2.7a1
    """

    revision = models.ForeignKey(
        SCMRevision,
        on_delete=models.CASCADE,
        help_text="The revision this package appeard in",
    )
    attribute_name = models.CharField(
        max_length=255, help_text="The name of the package"
    )
    name = models.CharField(max_length=255, help_text="The name of the package")
    version = models.CharField(max_length=100, help_text="The version of the package")

    patches = models.ManyToManyField("Patch")


class Patch(models.Model):
    filename = models.CharField(max_length=256, help_text="Name of the patch file")


class Issue(models.Model):
    """
    A single issue with one or more packages.
    """

    identifier = models.CharField(
        max_length=32, help_text="Well-known (external) identifier (e.g. CVE number)"
    )
    description = models.TextField(blank=True, help_text="A description for this issue")
    packages = models.ManyToManyField(Package, through="PackageAdvisoryStatus")
    note = models.TextField(blank=True, help_text="A note regarding this issue")


#########################################################


class AdvisoryStatus(models.TextChoices):
    DRAFT = "DRAFT", _("draft")
    RELEASED = "RELEASED", _("released")
    REVISED = "REVISED", _("revised")


class AdvisorySeverity(models.TextChoices):
    UNKNOWN = "UNKNOWN", _("unknown")
    LOW = "LOW", _("low")
    MEDIUM = "MEDIUM", _("medium")
    HIGH = "HIGH", _("high")
    CRITICAL = "CRITICAL", _("critical")


class Advisory(models.Model):
    """
    Advisory for users of NixOS about one or more vulnerabilities/issues.
    """

    nsa_id = models.CharField(max_length=32, unique=True)

    # FIXME: Add a `through` table that enforces RESTRICT or PROTECT on the foreign keys
    issues = models.ManyToManyField(
        "Issue", help_text="The issues addressed in this advisory"
    )
    status = models.CharField(
        choices=AdvisoryStatus.choices,
        default=AdvisoryStatus.DRAFT,
        max_length=max(len(x[0]) for x in AdvisoryStatus.choices),
    )
    not_before = models.DateTimeField(
        default=timezone.now, help_text="Not published before this date"
    )
    severity = models.CharField(
        choices=AdvisorySeverity.choices,
        default=AdvisorySeverity.UNKNOWN,
        max_length=max(len(x[0]) for x in AdvisorySeverity.choices),
        help_text="The severity of this advisory",
    )
    internal_note = models.TextField(
        blank=True, help_text="A note regarding this issue"
    )

    title = models.TextField(
        blank=False, help_text="The title the advisory (e.g. the email subject)"
    )
    text = models.TextField(
        blank=False, help_text="The text of the advisory (e.g. the email body)"
    )

    def make_text(self) -> str:
        # FIXME: the label field is missing from the TextChoices in
        # django-stubs: https://github.com/typeddjango/django-stubs/issues/346
        label: str = getattr(self.severity, "label")
        text = f"""
            {self.nsa_id} ({label}) - {self.title}

            ------------

            {self.text}
        """

        return text


class PackageIssueStatus(models.TextChoices):
    UNKNOWN = "unknown", _("unknown")
    FIXED = "fixed", _("fixed")
    UNAFFECTED = "unaffected", _("unaffected")
    VULNERABLE = "vulnerable", _("vulnerable")


class PackageAdvisoryStatus(models.Model):
    issue = models.ForeignKey("Issue", on_delete=models.CASCADE)
    package = models.ForeignKey("Package", on_delete=models.CASCADE)

    status = models.CharField(
        choices=PackageIssueStatus.choices,
        default=PackageIssueStatus.UNKNOWN,
        max_length=max(len(x[0]) for x in PackageIssueStatus.choices),
        help_text="Status of the issue in the package.",
    )
    confirmed = models.BooleanField(
        default=False,
        help_text="Whether this issue status has been confirmed by a human.",
    )
    note = models.TextField(blank=True, help_text="A note regarding this issue")
