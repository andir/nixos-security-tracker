import json
import os
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command

from tracker.github_events import find_cve_identifiers, search_for_cve_references
from tracker.github_events.signature import compute_github_hmac, verify_github_signature
from tracker.models import GitHubEvent

shared_secret = b"00000000000"
signature = "sha1-76f675f5babc40e8cc64405dcaa9049541380c18"


def test_compute_github_hmac():
    hmac = compute_github_hmac(shared_secret, "test".encode())
    assert hmac == signature


def test_verify_github_signature():
    assert verify_github_signature(shared_secret, signature, "test".encode())


@pytest.mark.parametrize(
    "string, result",
    [
        ("CVE-1998-123 CVE-1988-1234", ["CVE-1998-123", "CVE-1988-1234"]),
        ("CVE-1998-123", ["CVE-1998-123"]),
        ("CVE-1998-123!", ["CVE-1998-123"]),
        ("CVE-2010-1234", ["CVE-2010-1234"]),
        ("Something CVE-1998-123 else", ["CVE-1998-123"]),
        ("xxxCVE-2010-1234", None),
        ("CVE-2010-1234xxx", None),
        ("trash", None),
        ("", None),
    ],
)
def test_cve_regexp(string, result):
    m = find_cve_identifiers(string)
    if result:
        assert m, "Expected a match but got none"
        assert m == result
    else:
        assert not m, "Expected no result but got something"


@pytest.fixture
def issue_comment_json():
    """Returns the parsed result of the issue_comment JSON example as
    given in the GitHub Webhook documentation. The difference here is
    that we added CVE identifier into the file so our tests can match
    against that. The CVE identifier in the comment is CVE-1998-1234.
    """
    dir = Path(os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures"))
    with open(dir / "issue_comment.json") as fh:
        yield json.load(fh)


@pytest.mark.django_db
def test_search_cve_references(issue_comment_json):
    event = GitHubEvent.objects.create(kind="issue_comment", data=issue_comment_json)
    references = list(search_for_cve_references())
    assert len(references) == 1
    assert references[0][0] == event


@pytest.mark.django_db
def test_search_cve_references_command(issue_comment_json):
    out = StringIO()
    GitHubEvent.objects.create(kind="issue_comment", data=issue_comment_json)

    call_command("search_cve_references", stdout=out)

    assert "CVE-1988-1234" in out.getvalue()
    assert "issue_comment" in out.getvalue()
