import re

import tqdm
from django.core.management.base import BaseCommand

from tracker.models import Channel, ChannelRevision, Package
from tracker.packages import (
    get_revision_info,
    list_channel_revisions,
    list_channels,
    load_package_list,
)

# Allow all NixOS version > 20.03, including unstable and the small flavor
# In the long run this should probably be more flexible and support releases >= year 2030
DEFAUL_CHANNEL_FILTER_REGEX = (
    r"^nixos-((20\.09)|(unstable)|([2-9][1-9])\.[0-9]+)(-small)?$"
)


class Command(BaseCommand):
    help = "Import Nix channels into the local database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--channel-regex",
            type=str,
            help="regex that a channels name must match to be included. The default includes all version >=20.03",
            default=DEFAUL_CHANNEL_FILTER_REGEX,
        )

    def handle(self, *args, **options):
        match_re = re.compile(options["channel_regex"])
        for channel in list_channels():
            if match_re.match(channel.name) is None:
                continue

            channel_obj, _ = Channel.objects.get_or_create(name=channel.name)
            for revision in tqdm.tqdm(list(list_channel_revisions(channel))):
                info = get_revision_info(revision)

                revision_obj, created = ChannelRevision.objects.get_or_create(
                    name=revision.name,
                    channel=channel_obj,
                    defaults={
                        "datetime_created": info.date_created,
                        "git_revision": info.git_revision,
                    },
                )
                packages = load_package_list(info)
                for attribute_name in tqdm.tqdm(packages.keys()):
                    package = packages[attribute_name]
                    name = package.get("pname")
                    if name is None:
                        name = package["name"].rsplit("-", 1)[0]
                    version = package.get("version")
                    if version is None:
                        version = package["name"].rsplit("-", 1)[1]

                    # reduce the lookup costs (for already existing rows)
                    # to a single query.
                    if not Package.objects.filter(
                        attribute_name_row__value=attribute_name,
                        name_row__value=name,
                        version_row__value=version,
                        channel_revision=revision_obj,
                    ).exists():
                        Package.get_or_create(
                            attribute_name=attribute_name,
                            name=name,
                            version=version,
                            channel_revision=revision_obj,
                        )
