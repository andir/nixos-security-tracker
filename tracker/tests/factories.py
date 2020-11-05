from factory.django import DjangoModelFactory
from factory import SubFactory

from tracker import models


class IssueFactory(DjangoModelFactory):
    class Meta:
        model = models.Issue


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
