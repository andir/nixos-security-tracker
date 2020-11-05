import pytest
from .factories import AdvisoryFactory
from ..models import Advisory

from ..views import list_advisories


@pytest.mark.django_db
def test_list_empty_advisories(rf):
    request = rf.get("/advisories")
    response = list_advisories(request)
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    "advisories", [[], ["advisory-123"], ["advisories-123", "advisories-12345"]]
)
def test_list_advisories(rf, advisories):

    Advisory.objects.all().delete()

    for name in advisories:
        adv = AdvisoryFactory(title=name)
        adv.save()

    assert Advisory.objects.all().count() == 1

    request = rf.get("/advisories")
    response = list_advisories(request)
    assert response.status_code == 200

    for name in advisories:
        assert name in response.content.decode("utf-8")
