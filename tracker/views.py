from django.shortcuts import render, redirect
from django.urls import reverse

from .models import Advisory, Issue

from django.contrib.auth.views import LoginView as AuthLoginView


class LoginView(AuthLoginView):
    def get_success_url(self):
        return reverse("index")


def index(request):
    return redirect(reverse("advisories"))


def list_advisories(request):
    advisories = Advisory.objects.all()
    return render(request, "advisories/list.html", dict(advisories=advisories))


def list_issues(request):
    issues = Issue.objects.all()
    return render(request, "issues/list.html", dict(issues=issues))
