import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html

from .models import Issue


class IssueTable(tables.Table):
    class Meta:
        model = Issue
        fields = (
            "identifier",
            "description",
            "published_date",
        )
        template_name = "django_tables2/bootstrap4.html"

    def render_identifier(self, value) -> str:
        return format_html(
            '<a href="{url}">{identifier}</a>',
            url=reverse("issue_detail", kwargs={"identifier": value}),
            identifier=value,
        )

    def render_published_date(self, value) -> str:
        # pass through render method so the datetime format gets picked up
        return value
