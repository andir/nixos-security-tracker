from django.contrib.auth.views import LoginView as AuthLoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView

from .models import Advisory, Issue


class LoginView(AuthLoginView):
    def get_success_url(self):
        return reverse("index")


def index(request):
    return redirect(reverse("advisories"))


def list_advisories(request):
    advisories = Advisory.objects.all()
    return render(request, "advisories/list.html", dict(advisories=advisories))


class IssueDetail(DetailView):
    model = Issue
    slug_field = "identifier"
    slug_url_kwarg = "identifier"
    template_name = "issues/detail.html"


class IssueListView(ListView):
    paginate_by = 15
    model = Issue
    template_name = "issues/list.html"
