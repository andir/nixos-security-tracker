import logging
import re
from typing import Iterator, List, Tuple

from ..exceptions import GitHubEventBodyNotSupported
from ..models import GitHubEvent

logger = logging.getLogger(__name__)

CVE_REGEXP = re.compile(r"\b(?P<id>CVE-[0-9]+-[0-9]+)\b")


def find_cve_identifiers(text: List[str]) -> Iterator[str]:
    """
    Find all the CVE identifiers in the given string.
    """
    results = []
    for s in text:
        results += CVE_REGEXP.findall(s)
    return set(results)


def search_for_cve_references() -> Iterator[Tuple[GitHubEvent, Iterator[str]]]:
    """
    Search through all the recorded GitHubEvent's (of a supported kind) and
    yield tuples of (event, identifiers) where event is the GitHubEvent and
    identifiers is a list of CVE identifiers as strings.
    """
    events = GitHubEvent.objects.filter(kind__in=["issue_comment", "pull_request"])

    for event in events:
        try:
            identifiers = find_cve_identifiers(event.text)
            if not identifiers:
                logger.debug("No CVE identifiers in %s, skipping it", event)
                continue

            yield (event, identifiers)
        except GitHubEventBodyNotSupported:
            logger.info("Skipping %s as it doesn't seem to have a body", event)
            continue
