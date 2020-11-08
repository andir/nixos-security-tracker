from unittest.mock import MagicMock

import pytest
from django.template import Context, Template


def test_active_tag_loads():
    t = Template("{% load nav %}")
    t.render(Context({}))


@pytest.mark.parametrize(
    "match,path,expected",
    [
        ("", "", " active"),
        ("advisories", "/advisories/", " active"),
        ("advisories", "/issues/", ""),
    ],
)
def test_active_tag(match, path, expected):
    t = Template("{% load nav %}{% active '" + match + "' %}")
    mock = MagicMock()
    mock.path = path
    t = t.render(Context({"request": mock}))
    assert t == expected
