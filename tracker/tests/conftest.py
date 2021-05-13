import json

import boto3
import brotli
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from moto import mock_s3
from selenium import webdriver

from tracker.packages import NIX_RELEASES_BUCKET_NAME, NIX_RELEASES_OBJECT_PREFIX


@pytest.fixture
def fake_nix_release_bucket():

    prefix = "/".join([NIX_RELEASES_OBJECT_PREFIX, "nixos-20.09", "nixos-20.09-12345"])
    contents = {
        f"{prefix}/git-revision": "12345",
        f"{prefix}/nixexprs.tar.xz": "12345",
        f"{prefix}/packages.json.br": {
            "packages": {
                "some-package": {
                    "pname": "some-package",
                    "version": "1234a.dev0",
                },
                "another-package": {
                    "pname": "bar",
                    "version": "1234a.dev0-foo",
                },
            }
        },
    }

    with mock_s3():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=NIX_RELEASES_BUCKET_NAME)
        for key, value in contents.items():
            if type(value) is str:
                client.put_object(Bucket=NIX_RELEASES_BUCKET_NAME, Key=key, Body=value)
            elif type(value) is dict:
                value = json.dumps(value)
                if key.endswith(".br"):
                    value = brotli.compress(value.encode(), quality=0)
                    print(value)
                client.put_object(Bucket=NIX_RELEASES_BUCKET_NAME, Key=key, Body=value)

        for path in ["virtualbox-charon-images", "virtualbox-nixops-images"]:
            key = "/".join([NIX_RELEASES_OBJECT_PREFIX, path, ".keep"])
            client.put_object(Bucket=NIX_RELEASES_BUCKET_NAME, Key=key, Body="nope")

        yield


@pytest.fixture
def browser():

    options = webdriver.FirefoxOptions()
    options.headless = True

    with webdriver.Firefox(options=options) as b:
        yield b


@pytest.fixture
def browser_logged_in(live_server, browser, user_and_password):
    """
    Return a browser object where the current session is already logged in
    """

    user, password = user_and_password

    browser.get(live_server + reverse("auth:login"))
    username_field = browser.find_element_by_css_selector('form input[name="username"]')
    password_field = browser.find_element_by_css_selector('form input[name="password"]')

    username_field.send_keys(user)
    password_field.send_keys(password)

    submit = browser.find_element_by_css_selector('form button[type="submit"]')
    submit.click()

    return browser, live_server


@pytest.fixture
def user_and_password():
    password = "amazing password!@312^%"  # nosec B105
    user = User.objects.create_user(username="selenium-user", password=password)
    return user.username, password


@pytest.fixture
def user():
    return User.objects.create_user("pytest-user")


@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user)
    return client
