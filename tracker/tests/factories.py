import datetime

from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyDateTime, FuzzyText
from pytz import UTC

from tracker import models


class IssueFactory(DjangoModelFactory):
    class Meta:
        model = models.Issue

    identifier = Sequence(lambda n: f"CVE-{n}")
    description = Sequence(lambda n: f"description {n}")
    published_date = FuzzyDateTime(datetime.datetime(1998, 1, 1, tzinfo=UTC))


class IssueReferenceFactory(DjangoModelFactory):
    class Meta:
        model = models.IssueReference

    issue = SubFactory(IssueFactory)
    uri = Sequence(lambda n: f"http://example.com/?reference={n}")


class AdvisoryFactory(DjangoModelFactory):
    class Meta:
        model = models.Advisory

    nsa_id = Sequence(lambda n: f"NSA{n}")


class ChannelFactory(DjangoModelFactory):
    class Meta:
        model = models.Channel

    name = Sequence(lambda n: f"Channel-{n}")


class ChannelRevisionFactory(DjangoModelFactory):
    class Meta:
        model = models.ChannelRevision

    name = Sequence(lambda n: f"Revision {n}")
    git_revision = Sequence(lambda n: f"{n}")
    channel = SubFactory(ChannelFactory)
    datetime_created = FuzzyDateTime(datetime.datetime(1998, 1, 1, tzinfo=UTC))


class PackageAttributeNameFactory(DjangoModelFactory):
    class Meta:
        model = models.PackageAttributeName

    value = FuzzyText(length=20)


class PackageNameFactory(DjangoModelFactory):
    class Meta:
        model = models.PackageName

    value = FuzzyText(length=20)


class PackageVersionFactory(DjangoModelFactory):
    class Meta:
        model = models.PackageVersion

    value = FuzzyText(length=5)


class PackageFactory(DjangoModelFactory):
    class Meta:
        model = models.Package

    attribute_name_row = SubFactory(PackageAttributeNameFactory)
    name_row = SubFactory(PackageNameFactory)
    version_row = SubFactory(PackageVersionFactory)
    channel_revision = SubFactory(ChannelRevisionFactory)
