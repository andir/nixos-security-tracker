import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from selenium import webdriver


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
    password = "amazing password!@312^%"
    user = User.objects.create_user(username="selenium-user", password=password)
    return user.username, password


@pytest.fixture
def user():
    return User.objects.create_user("pytest-user")


@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user)
    return client
