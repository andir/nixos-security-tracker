import os
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
import requests
from django.core.management import call_command

from tracker.models import Issue

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
        ),
        (
            "CVE-2002-2446",
            "GE Healthcare Millennium MG, NC, and MyoSIGHT has a password of insite.genieacq for the insite account that cannot be changed without disabling product functionality for remote InSite support, which has unspecified impact and attack vectors.",
        ),
    ]
    for (identifier, description) in expected_identifiers:
        obj = Issue.objects.get(identifier=identifier)
        assert obj, f"Issue {identifier} must exist in the database"
        assert obj.description == description


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
