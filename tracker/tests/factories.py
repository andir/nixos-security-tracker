from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory

from tracker import models


class IssueFactory(DjangoModelFactory):
    class Meta:
        model = models.Issue

    identifier = Sequence(lambda n: f"CVE-{n}")
    description = Sequence(lambda n: f"description {n}")


class AdvisoryFactory(DjangoModelFactory):
    class Meta:
        model = models.Advisory

    nsa_id = Sequence(lambda n: f"NSA{n}")
