from typing import List

import pytest
from django.contrib.auth import get_user as auth_get_user
from django.contrib.auth.models import User
from django.urls import reverse
from pytest_django.asserts import assertRedirects, assertTemplateUsed

from ..models import Advisory
from ..views import list_advisories
from .factories import AdvisoryFactory, IssueFactory


@pytest.mark.django_db
def test_index(client):
    response = client.get(reverse("index"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_login(client):
    response = client.get(reverse("auth:login"))
    assert response.status_code == 200
    assertTemplateUsed(response, "registration/login.html")
    assert "form" in response.context

    username = "test"
    password = "mypassword"
    User.objects.create_user(username=username, password=password)

    form = response.context["form"].initial.copy()
    form["username"] = username
    form["password"] = password

    response = client.post(reverse("auth:login"), form)

    assert auth_get_user(client).is_authenticated
    assertRedirects(response, reverse("index"))


@pytest.mark.django_db
def test_list_empty_advisories(client):
    response = client.get("/advisories")
    assert response.status_code == 301
    response = client.get("/advisories/")
    assert response.status_code == 200


@pytest.mark.parametrize(
    "advisories", [[], ["advisory-123"], ["advisories-1234", "advisories-12345"]]
)
@pytest.mark.django_db
def test_list_advisories(rf, advisories: List[str]):

    Advisory.objects.all().delete()

    for name in advisories:
        adv = AdvisoryFactory(title=name)
        adv.save()

    assert Advisory.objects.all().count() == len(advisories)

    request = rf.get("/advisories")
    response = list_advisories(request)
    assert response.status_code == 200

    for name in advisories:
        assert name in response.content.decode("utf-8")


@pytest.mark.django_db
def test_list_empty_issues(client):
    response = client.get(reverse("issues"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_list_issues(client):
    issues = IssueFactory.create_batch(100)

    response = client.get(reverse("issues"))
    assert response.status_code == 200
    assertTemplateUsed(response, "issues/list.html")
    for issue in issues:
        assert issue.identifier in response.content.decode("utf-8")
        assert issue.description in response.content.decode("utf-8")
