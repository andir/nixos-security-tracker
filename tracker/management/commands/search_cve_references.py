from django.core.management.base import BaseCommand

from tracker.github_events import search_for_cve_references


class Command(BaseCommand):
    help = "Search the database for CVE references in the received GitHub events"

    def handle(self, *args, **options):
        for (event, cves) in search_for_cve_references():
            self.stdout.write(f"{event.kind} - {cves}")
