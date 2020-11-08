from django.contrib.auth import views as auth_views
from django.urls import include, path

from .views import LoginView, index, list_advisories, list_issues

auth_urls = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]

urlpatterns = [
    path("accounts/", include((auth_urls, "auth"))),
    path("advisories/", view=list_advisories, name="advisories"),
    path("issues/", view=list_issues, name="issues"),
    path("", view=index, name="index"),
]
