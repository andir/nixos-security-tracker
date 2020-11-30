from django.contrib.auth import views as auth_views
from django.urls import include, path

from .views import (
    IssueDetail,
    IssueEdit,
    IssueList,
    LoginView,
    github_event,
    index,
    list_advisories,
)

auth_urls = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]

urlpatterns = [
    path("accounts/", include((auth_urls, "auth"))),
    path("advisories/", view=list_advisories, name="advisories"),
    path("issues/", IssueList.as_view(), name="issues"),
    path("issues/<str:identifier>", IssueDetail.as_view(), name="issue_detail"),
    path("issues/<str:identifier>/edit", IssueEdit.as_view(), name="issue_edit"),
    path("__github_event", github_event, name="github_event"),
    path("", view=index, name="index"),
]
