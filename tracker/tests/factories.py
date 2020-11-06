from factory.django import DjangoModelFactory
from factory import SubFactory, Sequence

from tracker import models


class IssueFactory(DjangoModelFactory):
    class Meta:
        model = models.Issue

    identifier = Sequence(lambda n: f"CVE-{n}")


class ReleaseFactory(DjangoModelFactory):
    class Meta:
        model = models.Release


class SCMRevisionFactory(DjangoModelFactory):
    class Meta:
        model = models.SCMRevision

    release = SubFactory(ReleaseFactory)


class PackageFactory(DjangoModelFactory):
    class Meta:
        model = models.Package

    revision = SubFactory(SCMRevisionFactory)


class AdvisoryFactory(DjangoModelFactory):
    class Meta:
        model = models.Advisory

    nsa_id = Sequence(lambda n: f"NSA{n}")
