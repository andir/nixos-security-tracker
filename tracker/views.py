from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import DetailView, UpdateView
from django_tables2 import SingleTableView

from .models import Advisory, Issue, IssueReference
from .tables import IssueTable


class LoginView(AuthLoginView):
    def get_success_url(self):
        url = self.get_redirect_url()
        if url:
            return url
        return reverse("index")


def index(request):
    return redirect(reverse("advisories"))


def list_advisories(request):
    advisories = Advisory.objects.all()
    return render(request, "advisories/list.html", dict(advisories=advisories))


class IssueList(SingleTableView):
    model = Issue
    table_class = IssueTable
    paginate_by = settings.PAGINATE_BY
    template_name = "issues/list.html"


class IssueDetail(DetailView):
    model = Issue
    slug_field = "identifier"
    slug_url_kwarg = "identifier"
    template_name = "issues/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["references"] = IssueReference.objects.filter(issue=self.object)
        return context


class IssueEdit(LoginRequiredMixin, UpdateView):
    model = Issue
    slug_field = "identifier"
    slug_url_kwarg = "identifier"
    template_name = "issues/edit.html"

    fields = ["status", "status_reason", "note"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["references"] = IssueReference.objects.filter(issue=self.object)
        return context
