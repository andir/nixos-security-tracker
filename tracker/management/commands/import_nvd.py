import datetime
import json
import os
from gzip import GzipFile
from typing import BinaryIO, Dict

import requests
from django.core.management.base import BaseCommand

from tracker.models import Issue


class Command(BaseCommand):
    help = "Import CVEs from the NVD databases"

    def add_arguments(self, parser):
        parser.add_argument(
            "url", nargs="*", type=str, help="URL of the NVD JSON in version 1.1"
        )

    def handle(self, *args, **options):
        urls = options["url"]
        env_urls = os.environ.get("NIXOS_SECURITY_TRACKER_NVD_URLS")
        if not urls and env_urls:
            urls = env_urls.split(";")

        if not urls:
            urls = [
                f"https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-{year}.json.gz"
                for year in range(2002, datetime.date.today().year + 1)
            ]

        for url in urls:
            self.stdout.write(self.style.NOTICE(f"Loading {url}"))
            response = requests.get(url, stream=True)
            assert response.status_code == 200
            data = gzip_decompress(response.raw)
            data = json.load(data)

            cves: Dict[str, str] = {}

            for cve_item in data["CVE_Items"]:
                cve = cve_item["cve"]
                identifier = cve["CVE_data_meta"]["ID"]

                # get the first 'en' description
                description = next(
                    entry["value"]
                    for entry in cve["description"]["description_data"]
                    if entry["lang"] == "en"
                )

                cves[identifier] = description

            cve_ids = set(cves.keys())
            existing_issues = Issue.objects.filter(identifier__in=cve_ids)
            missing_issues = cve_ids ^ set(i.identifier for i in existing_issues)

            # insert all the missing issues
            if missing_issues:
                Issue.objects.bulk_create(
                    (Issue(identifier=i, description=cves[i]) for i in missing_issues)
                )

            for issue in existing_issues:
                description = cves[issue.identifier]
                if issue.description != description:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Updating description of issue {issue.identifier}"
                        )
                    )

                    issue.description = description
                    issue.save()


def gzip_decompress(input: BinaryIO) -> BinaryIO:
    """
    gzip_decompress takes an input byte stream and returns a stream of the
    decompressed data.
    """
    return GzipFile(fileobj=input, mode="rb")
