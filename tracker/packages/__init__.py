import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import boto3
import brotli

NIX_RELEASES_BUCKET_NAME = "nix-releases"
NIX_RELEASES_OBJECT_PREFIX = "nixos"


@dataclass(frozen=True)
class Channel:
    # name of the channel
    name: str

    # bucket prefix for the channel, including trailing slash
    prefix: str


@dataclass(frozen=True)
class Revision:
    # name of the revision
    name: str

    # the prefix for the revision, including trailing slash
    prefix: str


def _remove_prefix(s: str, prefix: str) -> str:
    if not s.startswith(prefix):
        return s
    return s[len(prefix) :]


def get_s3_client():
    """
    Wrapper around boto3.client to retrieve S3 clients that respect
    a custom environment variable that points the client at an
    alternative S3 API endpoint.

    This is required for integration testing the code in a NixOS VM test.
    """
    endpoint_url = os.getenv("AWS_S3_ENDPOINT_URL", None)
    return boto3.client("s3", endpoint_url=endpoint_url)


def list_channels() -> Iterable[Channel]:
    client = get_s3_client()
    paginator = client.get_paginator("list_objects_v2")
    prefix = NIX_RELEASES_OBJECT_PREFIX + "/"
    for page in paginator.paginate(
        Bucket=NIX_RELEASES_BUCKET_NAME,
        Delimiter="/",
        Prefix=prefix,
    ):
        for object in page["CommonPrefixes"]:
            name = _remove_prefix(object["Prefix"], prefix).rstrip("/")
            if name in ["virtualbox-charon-images", "virtualbox-nixops-images"]:
                continue

            yield Channel(name, object["Prefix"])


def list_channel_revisions(channel: Channel) -> Iterable[Revision]:
    client = get_s3_client()
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(
        Bucket=NIX_RELEASES_BUCKET_NAME,
        Delimiter="/",
        Prefix=channel.prefix,
    ):
        for object in page.get("CommonPrefixes", []):
            name = _remove_prefix(object["Prefix"], channel.prefix).rstrip("/")
            yield Revision(name, object["Prefix"])


@dataclass(frozen=True)
class RevisionInfo:
    # name of the revision info
    name: str

    # date crated
    date_created: datetime

    # git revision
    git_revision: str

    # nixexprs.tar.{gz,xz,..} path in the S3 bucket
    nixexprs_path: str

    # packages.json{.br, ..} path in the S3 bucket
    packages_path: str


def get_revision_info(revision: Revision):
    client = get_s3_client()
    paginator = client.get_paginator("list_objects_v2")
    objects = {}
    oldest_date = None
    for page in paginator.paginate(
        Bucket=NIX_RELEASES_BUCKET_NAME, Prefix=revision.prefix
    ):
        for object in page["Contents"]:
            key = _remove_prefix(object["Key"], revision.prefix)
            objects[key] = object
            if oldest_date is None or object["LastModified"] < oldest_date:
                oldest_date = object["LastModified"]

    git_revision = (
        client.get_object(
            Key=objects["git-revision"]["Key"], Bucket=NIX_RELEASES_BUCKET_NAME
        )["Body"]
        .read()
        .decode()
    )

    return RevisionInfo(
        revision.name,
        oldest_date,
        git_revision,
        objects["nixexprs.tar.xz"]["Key"],
        objects["packages.json.br"]["Key"],
    )


def load_package_list(rev: RevisionInfo) -> dict:
    client = get_s3_client()
    data = client.get_object(Bucket=NIX_RELEASES_BUCKET_NAME, Key=rev.packages_path)[
        "Body"
    ].read()
    lz = brotli.decompress(data).decode()
    del data
    packages = json.loads(lz)
    del lz
    return packages["packages"]
