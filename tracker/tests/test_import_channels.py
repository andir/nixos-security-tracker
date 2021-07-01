import re

import pytest
from django.core.management import call_command

from tracker.management.commands.import_channels import DEFAUL_CHANNEL_FILTER_REGEX
from tracker.models import Channel


@pytest.mark.parametrize(
    "channel_name, matches",
    [
        ("nixos-20.03", False),
        ("nixos-20.03-small", False),
        ("nixos-20.09", True),
        ("nixos-20.09-small", True),
        ("nixos-21.05", True),
        ("nixos-unstable", True),
        ("nixos-unstable-small", True),
        ("nixos-something", False),
    ],
)
def test_default_regex(channel_name, matches):
    m = re.compile(DEFAUL_CHANNEL_FILTER_REGEX).match(channel_name)
    if matches:
        assert m is not None
    else:
        assert m is None


@pytest.mark.django_db
def test_initial_import(
    fake_nix_release_bucket,
):
    qs = Channel.objects.filter(name="nixos-20.09")
    assert not qs.exists()
    call_command("import_channels")
    assert qs.exists()
    channel = qs.get()
    assert channel.revisions.count() == 1
    revision = channel.revisions.first()
    assert revision.name == "nixos-20.09-12345"
    assert revision.git_revision == "12345"
    assert revision.packages.count() == 2

    # running the import again shouldn't change anything
    call_command("import_channels")
    assert Channel.objects.count() == 1
    assert qs.exists()
    channel = qs.get()
    assert channel.revisions.count() == 1
    revision = channel.revisions.first()
    assert revision.name == "nixos-20.09-12345"
    assert revision.git_revision == "12345"
    assert revision.packages.count() == 2
