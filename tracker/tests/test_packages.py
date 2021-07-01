from tracker.packages import (
    NIX_RELEASES_OBJECT_PREFIX,
    Channel,
    get_revision_info,
    list_channel_revisions,
    list_channels,
    load_package_list,
)


def test_list_channels(fake_nix_release_bucket):
    """
    List all the channels that are found in the S3 buckets
    """

    channels = list(list_channels())

    assert len(channels) == 1
    assert channels[0].name == "nixos-20.09"
    assert channels[0].prefix == f"{NIX_RELEASES_OBJECT_PREFIX}/nixos-20.09/"


def test_channel_revision(fake_nix_release_bucket):
    prefix = f"{NIX_RELEASES_OBJECT_PREFIX}/nixos-20.09/"
    revisions = list(list_channel_revisions(Channel(name="nixos-20.09", prefix=prefix)))

    assert len(revisions) == 1
    assert revisions[0].name == "nixos-20.09-12345"
    assert revisions[0].prefix == f"{prefix}{revisions[0].name}/"

    revision_info = get_revision_info(revisions[0])

    packages = load_package_list(revision_info)

    assert len(packages) == 2
    assert packages.keys() == {"some-package", "another-package"}
