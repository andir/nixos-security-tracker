import datetime

from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyDateTime
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
