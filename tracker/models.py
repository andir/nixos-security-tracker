from typing import List

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .exceptions import GitHubEventBodyNotSupported


class GitHubEvent(models.Model):
    """
    GitHub events as they happen within Nixpkgs
    """

    received_at = models.DateTimeField(
        auto_now_add=True, help_text="Datetime when this entry was made"
    )
    kind = models.CharField(
        max_length=32,
        blank=False,
        null=False,
        help_text="Content of the X-GitHub-Event HTTP header",
    )
    data = models.JSONField(
        blank=False, null=False, help_text="The RAW event data as received from GitHub"
    )

    @property
    def text(self) -> List[str]:
        """
        Get the text parts (i.e. the message & title) of this event.
        Raises GitHubEventBodyNotSupported exception in case we do not yet know how
        to deal with this kind.
        """

        if self.kind == "issue_comment":
            return [self.data["comment"]["body"]]
        elif self.kind == "pull_request":
            return [
                self.data["pull_request"]["body"],
                self.data["pull_request"]["title"],
            ]

        raise GitHubEventBodyNotSupported(
            f"`body` attribute not supported for event kind {self.kind}"
        )

    def __str__(self):
        gh_number = "N/A"
        if self.kind == "issue_comment":
            gh_number = self.data["issue"]["number"]
        elif self.kind == "pull_request":
            gh_number = self.data["pull_request"]["number"]

        return f"<GitHubEvent(id={self.pk}, gh_id={gh_number}, kind={self.kind}, received_at={self.received_at})>"


class IssueReference(models.Model):
    """
    Additional references for issues
    """

    issue = models.ForeignKey(
        "Issue",
        help_text="Issue this reference ",
        on_delete=models.CASCADE,
        related_name="references",
    )
    uri = models.TextField(
        blank=False, null=False, help_text="URI for additional resources for an issue"
    )


class IssueStatus(models.TextChoices):
    UNKNOWN = "UNKNOWN", _("unknown")
    AFFECTED = "AFFECTED", _("affected")
    NOTAFFECTED = "NOTAFFECTED", _("notaffected")
    NOTFORUS = "NOTFORUS", _("notforus")
    WONTFIX = "WONTFIX", _("wontfix")


class Issue(models.Model):
    """
    A single issue with one or more packages.
    """

    identifier = models.CharField(
        max_length=32,
        help_text="Well-known (external) identifier (e.g. CVE number)",
        blank=False,
        unique=True,
        default=None,
    )
    status = models.CharField(
        choices=IssueStatus.choices,
        default=IssueStatus.UNKNOWN,
        max_length=max(len(x[0]) for x in IssueStatus.choices),
        help_text="The status the issue is currently in",
    )
    status_reason = models.CharField(
        max_length=256, blank=True, help_text="A short explanation for the status"
    )
    description = models.TextField(blank=True, help_text="A description for this issue")
    note = models.TextField(blank=True, help_text="A note regarding this issue")
    published_date = models.DateTimeField(
        blank=False,
        null=True,  # allow this to be Null while we migrate the database
        help_text="The date and time when the issue was first published",
    )

    def get_absolute_url(self):
        return reverse("issue_detail", kwargs={"identifier": self.identifier})

    class Meta:
        ordering = ("-published_date",)


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

    nsa_id = models.CharField(max_length=32, unique=True, blank=False)

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
