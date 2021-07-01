import datetime

import pytest
import pytz
from django.db import transaction
from django.db.utils import IntegrityError
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from ..exceptions import GitHubEventBodyNotSupported
from ..models import (
    Advisory,
    AdvisorySeverity,
    AdvisoryStatus,
    Channel,
    ChannelRevision,
    GitHubEvent,
    Issue,
    Package,
    PackageAttributeName,
    PackageName,
    PackageVersion,
)
from .factories import (
    AdvisoryFactory,
    ChannelFactory,
    ChannelRevisionFactory,
    IssueFactory,
    IssueReferenceFactory,
    PackageAttributeNameFactory,
    PackageFactory,
    PackageNameFactory,
    PackageVersionFactory,
)


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
        AdvisoryFactory(nsa_id=nsa_id)


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
        event.text


@pytest.mark.parametrize("klass, kwargs", [(GitHubEvent, {"kind": "test"})])
def test_model_str(klass, kwargs):
    obj = klass(**kwargs)
    s = str(obj)
    assert isinstance(s, str)


@pytest.mark.django_db
def test_channel_create():
    channel = ChannelFactory()
    channel.save()


@pytest.mark.django_db
def test_channel_duplicate_name():
    channel = ChannelFactory()
    channel.save()
    with pytest.raises(IntegrityError):
        Channel.objects.create(name=channel.name)


@pytest.mark.django_db
def test_channel_revision():
    channel = ChannelFactory()
    ChannelRevision.objects.create(
        channel=channel,
        name="some-revision",
        git_revision="1234567",
        datetime_created=timezone.now(),
    )


@pytest.mark.django_db
def test_channel_revision_duplicate():
    """
    Creating a ChannelRevision with the same name twice isn't
    allowed.
    """
    channel = ChannelFactory()
    c1 = ChannelRevision.objects.create(
        channel=channel,
        name="some-revision",
        git_revision="1234567",
        datetime_created=timezone.now(),
    )

    # create a duplicate by nulling the pk
    c1.pk = None
    with pytest.raises(IntegrityError):
        c1.save()


@pytest.mark.django_db
def test_channel_revision_duplicate_git_revision():
    """
    A git revision must only occur once within a channels lifetime
    """
    c1 = ChannelRevisionFactory()

    with pytest.raises(IntegrityError):
        ChannelRevisionFactory(
            channel=c1.channel,
            git_revision=c1.git_revision,
        )


@pytest.mark.django_db
def test_channel_revision_no_channel():
    """
    A ChannelRevision must always have a channel
    """
    c1 = ChannelRevisionFactory()
    c1.channel = None

    with pytest.raises(IntegrityError):
        c1.save()


@pytest.mark.django_db
def test_channel_revision_no_git_revision():
    """
    A ChannelRevision must always have a git revision
    """
    c1 = ChannelRevisionFactory()
    c1.git_revision = None

    with pytest.raises(IntegrityError):
        c1.save()


@pytest.mark.django_db
def test_channel_revision_no_name():
    """
    A ChannelRevision must always have a name
    """
    c1 = ChannelRevisionFactory()
    c1.name = None

    with pytest.raises(IntegrityError):
        c1.save()


@pytest.mark.django_db
def test_package_name():
    PackageName.objects.create(value="test")


@pytest.mark.django_db
def test_package_name_duplicate():
    PackageName.objects.create(value="test")
    with pytest.raises(IntegrityError):
        PackageName.objects.create(value="test")


@pytest.mark.django_db
def test_package_version():
    PackageVersion.objects.create(value="test")


@pytest.mark.django_db
def test_package_version_duplicate():
    PackageVersion.objects.create(value="test")
    with pytest.raises(IntegrityError):
        PackageVersion.objects.create(value="test")


@pytest.mark.django_db
def test_package_attribute_name():
    PackageAttributeName.objects.create(value="test")


@pytest.mark.django_db
def test_package_attribute_name_duplicate():
    PackageAttributeName.objects.create(value="test")
    with pytest.raises(IntegrityError):
        PackageAttributeName.objects.create(value="test")


@pytest.mark.django_db
def test_package():
    Package.objects.create(
        attribute_name_row=PackageAttributeNameFactory(),
        name_row=PackageNameFactory(),
        version_row=PackageVersionFactory(),
        channel_revision=ChannelRevisionFactory(),
    )


@pytest.mark.django_db
def test_package_duplicacte_attribute_name():
    p1 = Package.objects.create(
        attribute_name_row=PackageAttributeNameFactory(),
        name_row=PackageNameFactory(),
        version_row=PackageVersionFactory(),
        channel_revision=ChannelRevisionFactory(),
    )

    with pytest.raises(IntegrityError):
        PackageFactory(
            attribute_name_row=p1.attribute_name_row,
            channel_revision=p1.channel_revision,
        )


@pytest.mark.django_db
def test_package_custom_get_or_create():
    channel_revision = ChannelRevisionFactory()
    p, created = Package.get_or_create(
        attribute_name="my-package-name",
        name="some-package-name",
        version="123.456git",
        channel_revision=channel_revision,
    )

    assert created
    assert p.attribute_name == "my-package-name"
    assert p.name == "some-package-name"
    assert p.version == "123.456git"
    assert p.channel_revision == channel_revision

    p, created = Package.get_or_create(
        attribute_name="my-package-name",
        name="new-name",
        version="3456",
        channel_revision=channel_revision,
    )

    assert not created
    assert p.attribute_name == "my-package-name"
    assert p.name == "new-name"
    assert p.version == "3456"
    assert p.channel_revision == channel_revision
