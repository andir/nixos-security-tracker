import pytest
from selenium import webdriver


@pytest.fixture
def browser():

    options = webdriver.FirefoxOptions()
    options.headless = True

    with webdriver.Firefox(options=options) as b:
        yield b
