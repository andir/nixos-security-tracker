import datetime

import pytest
import pytz
from django.db import transaction
from django.db.utils import IntegrityError
from django.urls import reverse
from freezegun import freeze_time

from ..exceptions import GitHubEventBodyNotSupported
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
@freeze_time("2015-01-01 00:30:00")
def test_issue_sort_order():
    """
    Issues should by default be sorted by the date they were published.
    """

    now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    issues = [
        IssueFactory(
            identifier="AAAAA", published_date=now - datetime.timedelta(hours=1)
        ),
        IssueFactory(
            identifier="BBBBB", published_date=now + datetime.timedelta(days=1)
        ),
        IssueFactory(identifier="CCCCC", published_date=now),
    ]

    q = Issue.objects.filter(pk__in=[i.pk for i in issues])
    assert q.first().identifier == "BBBBB"
    assert q[1].identifier == "CCCCC"
    assert q.last().identifier == "AAAAA"


@pytest.mark.django_db
def test_issue_identifier_must_be_unique():
    identifier = "unique-issue-identifier"
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    i1 = Issue(identifier=identifier, published_date=now)
    i1.save()

    with pytest.raises(IntegrityError):
        i2 = Issue(identifier=identifier, published_date=now)
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


def test_github_event_data_missing():
    event = GitHubEvent(kind="unsupported type", data={})
    with pytest.raises(GitHubEventBodyNotSupported):
        event.body
