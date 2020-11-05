import pytest
from django.test import TestCase
from unittest import TestCase

from .factories import IssueFactory, PackageFactory

from ..models import (
    Issue,
    Package,
    SCMRevision,
    Release,
    Advisory,
    AdvisoryStatus,
    AdvisorySeverity,
)


@pytest.mark.django_db
def test_advisory_make_text():
    package = PackageFactory()
    issue = IssueFactory()
    issue.packages.add(package)

    advisory = Advisory.objects.create(
        nsa_id="123", severity=AdvisorySeverity.MEDIUM, title="title"
    )
    assert advisory.status == AdvisoryStatus.DRAFT

    advisory.issues.add(issue)

    text = advisory.make_text()
    assert text.split("\n")[1].strip() == "123 (medium) - title"
