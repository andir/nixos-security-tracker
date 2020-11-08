import os

import pytest
from django.urls import reverse

from .factories import IssueFactory

e2e = pytest.mark.skipif(
    os.getenv("SKIP_E2E_TESTS", False),
    reason="E2E tests are not supported in Nix builds",
)


@e2e
def test_index(live_server, browser):
    browser.get(live_server + "/")
    elem = browser.find_element_by_tag_name("h1")
    assert elem.text == "Advisories"


@e2e
def test_issue_list_links_to_issue(live_server, browser):
    issue = IssueFactory()
    browser.get(live_server + reverse("issues"))
    elem = browser.find_element_by_partial_link_text(issue.identifier)
    assert elem.get_attribute("href") == live_server + reverse(
        "issue_detail", args=[issue.identifier]
    )
