from django.core.management.base import BaseCommand
from django.db import transaction

from tracker.models import (
    Channel,
    ChannelRevision,
    Package,
    PackageAttributeName,
    PackageName,
    PackageVersion,
)
from tracker.packages import (
    get_revision_info,
    list_channel_revisions,
    list_channels,
    load_package_list,
)


class Command(BaseCommand):
    help = "Import Nix channels into the local database"

    def handle(self, *args, **options):
        for channel in list_channels():
            if any(
                channel.name.startswith(x)
                for x in [
                    "14.04",
                    "14.12",
                    "13.10",
                    "15.",
                    "16.",
                    "17.03",
                    "17.09",
                    "18.03",
                    "18.09",
                    "19.03",
                    "19.09",
                ]
            ):
                continue

            print("channel: ", channel)
            channel_obj, _ = Channel.objects.get_or_create(name=channel.name)
            for revision in list_channel_revisions(channel):
                print("\t", revision.name)
                info = get_revision_info(revision)

                with transaction.atomic():
                    revision_obj, created = ChannelRevision.objects.get_or_create(
                        name=revision.name,
                        channel=channel_obj,
                        defaults={
                            "datetime_created": info.date_created,
                            "git_revision": info.git_revision,
                        },
                    )

                    print("\t\tinfo: ", info)
                    packages = load_package_list(info)
                    print("\t\tpackages: ", len(packages["packages"]))

                    for attribute_name, package in packages["packages"].items():
                        name = package.get("pname")
                        if name is None:
                            name = package["name"].rsplit("-", 1)[0]
                        version = package.get("version")
                        if version is None:
                            version = package["name"].rsplit("-", 1)[1]

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
