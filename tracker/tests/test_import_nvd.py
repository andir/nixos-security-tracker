import os
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
import requests
from django.core.management import call_command
from freezegun import freeze_time

from tracker.models import Issue, IssueReference

FIXTURE_DIR = Path(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")
)


def test_import_nvd_requires_valid_url():
    out = StringIO()
    with pytest.raises(requests.exceptions.MissingSchema):
        call_command("import_nvd", "not-a-url", stdout=out)


@pytest.fixture(name="nvd_json_data")
def nvd_json_data_fixture():
    return nvd_json_data()


def nvd_json_data():
    return open(FIXTURE_DIR / "nvdcve-1.1-2002.json.gz", "rb")


def mocked_nvd_response():
    mock = MagicMock()
    mock.status_code = 200
    mock.raw = nvd_json_data()
    return mock


@pytest.fixture(name="mocked_nvd_response")
def mocked_nvd_response_fixture():
    return mocked_nvd_response()


@patch("requests.get")
@pytest.mark.django_db
def test_import_nvd(request_get, mocked_nvd_response):
    url = "https://test-dat"
    request_get.return_value = mocked_nvd_response
    call_command("import_nvd", url)
    request_get.assert_called_once_with(url, stream=True)

    expected_identifiers = [
        (
            "CVE-1999-0001",
            "ip_input.c in BSD-derived TCP/IP implementations allows remote attackers to cause a denial of service (crash or hang) via crafted packets.",
            [
                "http://www.openbsd.org/errata23.html#tcpfix",
                "http://www.osvdb.org/5707",
            ],
        ),
        (
            "CVE-2002-2446",
            "GE Healthcare Millennium MG, NC, and MyoSIGHT has a password of insite.genieacq for the insite account that cannot be changed without disabling product functionality for remote InSite support, which has unspecified impact and attack vectors.",
            [
                "http://apps.gehealthcare.com/servlet/ClientServlet/2338955-100.pdf?REQ=RAA&DIRECTION=2338955-100&FILENAME=2338955-100.pdf&FILEREV=1&DOCREV_ORG=1",
                "http://apps.gehealthcare.com/servlet/ClientServlet/2354459-100.pdf?REQ=RAA&DIRECTION=2354459-100&FILENAME=2354459-100.pdf&FILEREV=4&DOCREV_ORG=4",
                "http://www.forbes.com/sites/thomasbrewster/2015/07/10/vulnerable-breasts/",
                "https://ics-cert.us-cert.gov/advisories/ICSMA-18-037-02",
                "https://twitter.com/digitalbond/status/619250429751222277",
            ],
        ),
    ]
    for (identifier, description, references) in expected_identifiers:
        issue = Issue.objects.get(identifier=identifier)
        assert issue, f"Issue {identifier} must exist in the database"
        assert issue.description == description

        persisted_references = [
            reference.uri for reference in IssueReference.objects.filter(issue=issue)
        ]
        for reference in references:
            assert reference in persisted_references


@patch("requests.get")
@patch.dict("os.environ", {"NIXOS_SECURITY_TRACKER_NVD_URLS": "https://test-data"})
@pytest.mark.django_db
def test_import_nvd_accepts_env_var(request_get, mocked_nvd_response):
    url = "https://test-data"
    request_get.return_value = mocked_nvd_response
    call_command("import_nvd")
    request_get.assert_called_once_with(url, stream=True)


@patch("requests.get")
@patch.dict("os.environ", {"NIXOS_SECURITY_TRACKER_NVD_URLS": "https://bogon"})
@pytest.mark.django_db
def test_import_nvd_accepts_prefers_cli_arguments(request_get, mocked_nvd_response):
    url = "https://test-data"
    request_get.return_value = mocked_nvd_response
    call_command("import_nvd", url)
    request_get.assert_called_once_with(url, stream=True)


@patch("requests.get")
@patch.dict(
    "os.environ",
    {"NIXOS_SECURITY_TRACKER_NVD_URLS": "https://test-data;https://another"},
)
@pytest.mark.django_db
def test_import_nvd_accepts_multiple_env_vars(request_get):
    request_get.side_effect = [mocked_nvd_response(), mocked_nvd_response()]
    call_command("import_nvd")
    request_get.assert_has_calls(
        [call("https://test-data", stream=True), call("https://another", stream=True)]
    )


@patch("requests.get")
@pytest.mark.django_db
def test_import_nvd_updates_description(request_get, mocked_nvd_response):
    url = "https://test-dat"
    identifier = "CVE-1999-0001"
    expected_description = "ip_input.c in BSD-derived TCP/IP implementations allows remote attackers to cause a denial of service (crash or hang) via crafted packets."

    Issue.objects.create(
        identifier=identifier, description="This is an outdated description"
    )

    request_get.return_value = mocked_nvd_response
    call_command("import_nvd", url)
    request_get.assert_called_once_with(url, stream=True)

    issue = Issue.objects.get(identifier=identifier)
    assert issue.description == expected_description


@patch("requests.get")
@pytest.mark.django_db
def test_import_nvd_removes_references(request_get, mocked_nvd_response):
    identifier = "CVE-1999-0001"
    issue = Issue.objects.create(identifier=identifier)
    IssueReference.objects.create(issue=issue, uri="please remove me")

    references = (
        IssueReference.objects.filter(issue=issue).values_list("uri", flat=True).all()
    )
    assert "please remove me" in references

    request_get.return_value = mocked_nvd_response
    call_command("import_nvd", "http://somewhere")

    references = (
        IssueReference.objects.filter(issue=issue).values_list("uri", flat=True).all()
    )
    assert "please remove me" not in references


@patch("requests.get")
@pytest.mark.django_db
def test_import_nvd_adds_missing_references(request_get, mocked_nvd_response):
    identifier = "CVE-1999-0001"
    issue = Issue.objects.create(identifier=identifier)

    assert IssueReference.objects.filter(issue=issue).count() == 0

    request_get.return_value = mocked_nvd_response
    call_command("import_nvd", "http://somewhere")

    references = (
        IssueReference.objects.filter(issue=issue).values_list("uri", flat=True).all()
    )
    assert "http://www.openbsd.org/errata23.html#tcpfix" in references
    assert "http://www.osvdb.org/5707" in references


@patch("requests.get")
@pytest.mark.django_db
@freeze_time("2003-01-01")
def test_import_nvd_falls_back_to_timerange(request_get):
    """
    Assert that the import script falls back to using the date range to today
    for the import. The first NVD database is from 2002 so this test is
    supposed to cause two requests.
    """
    request_get.side_effect = [mocked_nvd_response(), mocked_nvd_response()]
    call_command("import_nvd")
    request_get.assert_has_calls(
        [
            call(
                "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-2002.json.gz",
                stream=True,
            ),
            call(
                "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-2003.json.gz",
                stream=True,
            ),
        ]
    )
