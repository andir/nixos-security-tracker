import json
import logging

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, UpdateView
from django_tables2 import SingleTableView

from .models import Advisory, GitHubEvent, Issue, IssueReference
from .tables import IssueTable

logger = logging.getLogger(__name__)


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


@require_POST
@csrf_exempt
def github_event(request):
    if "X-Github-Event" not in request.headers:
        logger.info("Received GitHub event without event type")
        return HttpResponseBadRequest("Nope.")

    kind = request.headers["X-GitHub-Event"]
    if not kind:
        logger.error("Invalid event type received: %s", kind)
        return HttpResponseBadRequest("Go away.")

    try:
        data = json.loads(request.body)
        event = GitHubEvent(kind=kind, data=data)
        event.save()
    except json.JSONDecodeError as e:
        logger.error("Invalid body received: %s", e)
        return HttpResponseBadRequest("Not sure if you are serious.")

    return HttpResponse("Thanks!")
