import pytest
from django.db import transaction
from django.db.utils import IntegrityError
from django.urls import reverse

from ..models import Advisory, AdvisorySeverity, AdvisoryStatus, GitHubEvent, Issue
from .factories import AdvisoryFactory, IssueFactory, IssueReferenceFactory


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
    issue = IssueFactory()

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
def test_issue_sort_order():
    """
    Issues should by default be sorted by the identifier.
    """

    issues = [
        IssueFactory(identifier="ZZZZZ"),
        IssueFactory(identifier="AAAAA"),
        IssueFactory(identifier="DDDDD"),
    ]

    print(issues)
    q = Issue.objects.filter(pk__in=[i.pk for i in issues])
    assert q.first().identifier == "AAAAA"
    assert q[1].identifier == "DDDDD"
    assert q.last().identifier == "ZZZZZ"


@pytest.mark.django_db
def test_issue_identifier_must_be_unique():
    identifier = "unique-issue-identifier"
    i1 = Issue(identifier=identifier)
    i1.save()

    with pytest.raises(IntegrityError):
        i2 = Issue(identifier=identifier)
        i2.save()


@pytest.mark.django_db
def test_issue_factory_sets_identifier_and_description():
    i = IssueFactory()
    assert i.identifier and i.identifier != ""
    assert i.description and i.description != ""


@pytest.mark.django_db
def test_issue_get_absolute_url():
    issue = IssueFactory()
    assert issue.get_absolute_url() == reverse(
        "issue_detail", kwargs={"identifier": issue.identifier}
    )


@pytest.mark.django_db
def test_issue_reference():
    reference = IssueReferenceFactory()
    assert reference.issue and isinstance(reference.issue, Issue)
    assert reference.uri and reference.uri != ""


@pytest.mark.django_db
def test_create_github_event():
    event = GitHubEvent(kind="some_event", data={"key": "value"})
    event.save()


@pytest.mark.django_db
def test_create_github_event_requires_data():
    event = GitHubEvent(kind="some_event", data=None)
    with pytest.raises(IntegrityError):
        event.save()


@pytest.mark.django_db
def test_create_github_event_requires_event_kind():
    event = GitHubEvent(kind=None, data={})
    with pytest.raises(IntegrityError):
        event.save()
