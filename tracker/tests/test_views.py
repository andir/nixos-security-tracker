import itertools
from typing import List

import pytest
from django.conf import settings
from django.contrib.auth import get_user as auth_get_user
from django.contrib.auth.models import User
from django.urls import reverse
from pytest_django.asserts import assertRedirects, assertTemplateUsed

from ..models import Advisory, Issue
from ..views import list_advisories
from .factories import AdvisoryFactory, IssueFactory


@pytest.mark.django_db
def test_index(client):
    response = client.get(reverse("index"), follow=True)
    assert response.status_code == 200
    assert len(response.redirect_chain) == 1


@pytest.mark.django_db
def test_login_button_visible(client):
    """
    Unauthenticated users should be presented with a login link.
    """
    response = client.get(reverse("index"), follow=True)
    assert reverse("auth:login") in response.content.decode("utf-8")


@pytest.mark.django_db
def test_logout_button_visible(authenticated_client):
    """
    Authenticated users should be presented with a logout link.
    """
    response = authenticated_client.get(reverse("index"), follow=True)
    assert reverse("auth:logout") in response.content.decode("utf-8")


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

    response = client.post(reverse("auth:login"), form, follow=True)

    assert auth_get_user(client).is_authenticated
    assert response.redirect_chain[0] == (reverse("index"), 302)


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
    num_pages = 3
    issues = IssueFactory.create_batch(settings.PAGINATE_BY * num_pages)
    issues.sort(key=lambda issue: issue.identifier)

    i = iter(issues)
    slices = [itertools.islice(iter(i), settings.PAGINATE_BY) for _ in range(num_pages)]

    for page, issue_chunk in enumerate(slices, start=1):
        response = client.get(reverse("issues"), {"page": page})
        assert response.status_code == 200
        assertTemplateUsed(response, "issues/list.html")
        content = response.content.decode("utf-8")

        for issue in issue_chunk:
            assert issue.identifier in content
            assert issue.description in content


@pytest.mark.django_db
def test_detail_issue(client):
    issue = IssueFactory()
    response = client.get(issue.get_absolute_url())
    assert response.status_code == 200
    assert issue.identifier in response.content.decode("utf-8")
    assert issue.description in response.content.decode("utf-8")


@pytest.mark.django_db
def test_edit_issue_requires_login(client):
    assert not auth_get_user(client).is_authenticated
    issue = IssueFactory(note="this is a note")
    response = client.get(
        reverse("issue_edit", kwargs={"identifier": issue.identifier})
    )
    assert response.status_code == 302  # redirec to login page
    assert response.url.startswith(reverse("auth:login"))


@pytest.mark.django_db
def test_edit_issue(authenticated_client):
    issue = IssueFactory(note="this is a note")
    response = authenticated_client.get(
        reverse("issue_edit", kwargs={"identifier": issue.identifier})
    )
    assert response.status_code == 200
    assertTemplateUsed(response, "issues/edit.html")
    assert issue.note in response.content.decode("utf-8")

    assert "form" in response.context
    form = response.context["form"].initial.copy()
    form["note"] = "another note"

    response = authenticated_client.post(
        reverse("issue_edit", kwargs={"identifier": issue.identifier}),
        form,
        follow=True,
    )

    assert response.status_code == 200
    assert response.redirect_chain[0][0] == issue.get_absolute_url()
    assert "another note" in response.content.decode("utf-8")
    issue.refresh_from_db()
    assert issue.note == "another note"
