from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory

from tracker import models


class IssueFactory(DjangoModelFactory):
    class Meta:
        model = models.Issue

    identifier = Sequence(lambda n: f"CVE-{n}")
    description = Sequence(lambda n: f"description {n}")


class IssueReferenceFactory(DjangoModelFactory):
    class Meta:
        model = models.IssueReference

    issue = SubFactory(IssueFactory)
    uri = Sequence(lambda n: f"http://example.com/?reference={n}")


class AdvisoryFactory(DjangoModelFactory):
    class Meta:
        model = models.Advisory

    nsa_id = Sequence(lambda n: f"NSA{n}")
