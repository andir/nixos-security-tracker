import os
import sys

import pytest

e2e = pytest.mark.skipif(
    os.getenv("SKIP_E2E_TESTS", False),
    reason="E2E tests are not supported in Nix builds",
)

print(os.environ, file=sys.stderr)


@e2e
def test_index(live_server, browser):
    browser.get(live_server + "/")
    elem = browser.find_element_by_tag_name("h1")
    assert elem.text == "Advisories"
