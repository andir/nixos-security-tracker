import datetime
import json
import os
from gzip import GzipFile
from typing import BinaryIO, Dict

import requests
from django.core.management.base import BaseCommand

from tracker.models import Issue, IssueReference


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

                references = [
                    data["url"] for data in cve["references"]["reference_data"]
                ]

                cves[identifier] = {
                    "description": description,
                    "references": sorted(references),
                }

            cve_ids = set(cves.keys())
            existing_issues = list(
                Issue.objects.prefetch_related("references").filter(
                    identifier__in=cve_ids
                )
            )
            missing_issues = cve_ids ^ set(i.identifier for i in existing_issues)

            # insert all the missing issues
            if missing_issues:
                Issue.objects.bulk_create(
                    (
                        Issue(identifier=i, description=cves[i]["description"])
                        for i in missing_issues
                    )
                )

                missing_issues_with_references = dict(
                    (i, cves[i]["references"])
                    for i in missing_issues
                    if cves[i]["references"]
                )

                if missing_issues_with_references:
                    objs = Issue.objects.filter(
                        identifier__in=missing_issues_with_references.keys()
                    )
                    references_to_create = []
                    for issue in objs:
                        references = missing_issues_with_references[issue.identifier]

                        references_to_create += [
                            IssueReference(issue=issue, uri=uri) for uri in references
                        ]
                    IssueReference.objects.bulk_create(references_to_create)

            for issue in existing_issues:
                cve = cves[issue.identifier]
                description = cve["description"]

                if issue.description != description:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Updating metadata of issue {issue.identifier}"
                        )
                    )

                    issue.description = description
                    issue.save()

                references = set(cve["references"])

                existing_uris = set(r.uri for r in issue.references.all())

                # the difference between the two sets, this yield missing and "exceeding" items
                diff_uris = existing_uris ^ references

                # filter the diff into missing and exceeding (to be removed) items
                missing_uris = diff_uris & references
                to_be_removed_uris = diff_uris & existing_uris

                if to_be_removed_uris:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Removing {len(to_be_removed_uris)} references from issue {issue.identifier}"
                        )
                    )
                    IssueReference.objects.filter(
                        issue=issue, uri__in=to_be_removed_uris
                    ).delete()

                if missing_uris:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Creating {len(references)} references from issue {issue.identifier}"
                        )
                    )
                    IssueReference.objects.bulk_create(
                        IssueReference(issue=issue, uri=uri) for uri in missing_uris
                    )


def gzip_decompress(input: BinaryIO) -> BinaryIO:
    """
    gzip_decompress takes an input byte stream and returns a stream of the
    decompressed data.
    """
    return GzipFile(fileobj=input, mode="rb")
