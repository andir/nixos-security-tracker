import pytest
from django.test import TestCase
from unittest import TestCase

from .models import (
    Issue,
    Package,
    SCMRevision,
    Release,
    Advisory,
    AdvisoryStatus,
    AdvisorySeverity,
)


@pytest.mark.django_db
def test_create_issue_with_advisory():
    release = Release.objects.create()
    revision = SCMRevision.objects.create(release=release)

    package = Package.objects.create(
        revision=revision, attribute_name="hello", name="hello", version="123",
    )

    assert package.name == "hello"
    issue = Issue.objects.create()
    issue.packages.add(package)

    advisory = Advisory.objects.create(
        nsa_id="123", severity=AdvisorySeverity.MEDIUM, title="title"
    )
    assert advisory.status == AdvisoryStatus.DRAFT

    advisory.issues.add(issue)

    text = advisory.make_text()
    assert text.split("\n")[1].strip() == "123 (medium) - title"
