from django.urls import path
from .views import list_advisories

urlpatterns = [path("advisories/", view=list_advisories)]
