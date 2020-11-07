import pytest
from django.db import transaction
from django.db.utils import IntegrityError

from ..models import Advisory, AdvisorySeverity, AdvisoryStatus, Issue
from .factories import AdvisoryFactory, IssueFactory, PackageFactory


@pytest.mark.django_db
def test_advisories_require_nsa_id():
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            AdvisoryFactory(nsa_id=None)

    adv = AdvisoryFactory()
    assert adv.nsa_id
    with pytest.raises(IntegrityError):
        adv.nsa_id = None
        adv.save()


@pytest.mark.django_db
def test_advisories_require_unique_nsa_id():
    nsa_id = "NSA0001"
    adv = AdvisoryFactory(nsa_id=nsa_id)
    adv.save()

    with pytest.raises(IntegrityError):
        adv = AdvisoryFactory(nsa_id=nsa_id)
        adv.save()


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


@pytest.mark.django_db
def test_issue_requires_identifier():
    i = Issue()
    with pytest.raises(IntegrityError):
        i.save()


@pytest.mark.django_db
def test_issue_identifier_must_be_unique():
    identifier = "unique-issue-identifier"
    i1 = Issue(identifier=identifier)
    i1.save()

    with pytest.raises(IntegrityError):
        i2 = Issue(identifier=identifier)
        i2.save()
