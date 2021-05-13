import json

import boto3
import brotli
import pytest
from moto import mock_s3

from tracker.packages import (
    NIX_RELEASES_BUCKET_NAME,
    NIX_RELEASES_OBJECT_PREFIX,
    Channel,
    get_revision_info,
    list_channel_revisions,
    list_channels,
    load_package_list,
)


@pytest.fixture
def fake_nix_release_bucket():

    prefix = "/".join([NIX_RELEASES_OBJECT_PREFIX, "nixos-20.09", "nixos-20.09-12345"])
    contents = {
        f"{prefix}/git-revision": "12345",
        f"{prefix}/nixexprs.tar.xz": "12345",
        f"{prefix}/packages.json.br": {
            "packages": {
                "some-package": "foo",
                "another-package": "bar",
            }
        },
    }

    with mock_s3():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=NIX_RELEASES_BUCKET_NAME)
        for key, value in contents.items():
            if type(value) is str:
                client.put_object(Bucket=NIX_RELEASES_BUCKET_NAME, Key=key, Body=value)
            elif type(value) is dict:
                value = json.dumps(value)
                if key.endswith(".br"):
                    value = brotli.compress(value.encode(), quality=0)
                    print(value)
                client.put_object(Bucket=NIX_RELEASES_BUCKET_NAME, Key=key, Body=value)

        yield


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
