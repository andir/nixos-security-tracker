from django.urls import path, include
from .views import list_advisories, index, LoginView, list_issues

from django.contrib.auth import views as auth_views

auth_urls = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]

urlpatterns = [
    path("accounts/", include((auth_urls, "auth"))),
    path("advisories/", view=list_advisories, name="advisories"),
    path("issues/", view=list_issues, name="issues"),
    path("", view=list_advisories, name="index"),
]
