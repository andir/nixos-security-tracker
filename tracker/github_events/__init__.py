import logging
import re
from typing import Iterator, List, Optional, Tuple

from ..models import GitHubEvent

logger = logging.getLogger(__name__)

CVE_REGEXP = re.compile(r"\b(?P<id>CVE-[0-9]+-[0-9]+)\b")


def get_body(obj: GitHubEvent) -> Optional[str]:
    """
    Get the body (aka the message) of the given GitHubEvent.
    Returns None of the kind is not supported.
    """
    kind = obj.kind

    if kind == "issue_comment":
        return obj.data["comment"]["body"]

    return None


def find_cve_identifiers(body: str) -> List[str]:
    """
    Find all the CVE identifiers in the given string.
    """
    return CVE_REGEXP.findall(body)


def search_for_cve_references() -> Iterator[Tuple[GitHubEvent, List[str]]]:
    """
    Search through all the recorded GitHubEvent's (of a supported kind) and
    yield tuples of (event, identifiers) where event is the GitHubEvent and
    identifiers is a list of CVE identifiers as strings.
    """
    events = GitHubEvent.objects.filter(kind__in=["issue_comment"])

    for event in events:
        body = get_body(event)
        if not body:
            logger.info("Skipping %s as it doesn't seem to have a body", event)
            continue

        identifiers = find_cve_identifiers(body)
        if not identifiers:
            logger.debug("No CVE identifiers in %s, skipping it", event)
            continue

        yield (event, identifiers)
