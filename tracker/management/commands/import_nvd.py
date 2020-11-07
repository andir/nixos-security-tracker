import json
from gzip import GzipFile
from typing import BinaryIO

import requests
from django.core.management.base import BaseCommand

from tracker.models import Issue


class Command(BaseCommand):
    help = "Import CVEs from the NVD databases"

    def add_arguments(self, parser):
        parser.add_argument(
            "url", nargs="+", type=str, help="URL of the NVD JSON in version 1.1"
        )

    def handle(self, *args, **options):
        for url in options["url"]:
            response = requests.get(url, stream=True)
            assert response.status_code == 200
            data = gzip_decompress(response.raw)
            data = json.load(data)

            for cve_item in data["CVE_Items"]:
                cve = cve_item["cve"]
                identifier = cve["CVE_data_meta"]["ID"]

                # get the first 'en' description
                description = next(
                    entry["value"]
                    for entry in cve["description"]["description_data"]
                    if entry["lang"] == "en"
                )

                (issue, created) = Issue.objects.get_or_create(
                    identifier=identifier, defaults={"description": description}
                )
                if not created:
                    self.stdout.write(
                        self.style.NOTICE(f"Updating description of issue {identifier}")
                    )
                    if issue.description != description:
                        issue.description = description
                        issue.save()


def gzip_decompress(input: BinaryIO) -> BinaryIO:
    """
    gzip_decompress takes an input byte stream and returns a stream of the
    decompressed data.
    """
    return GzipFile(fileobj=input, mode="rb")
