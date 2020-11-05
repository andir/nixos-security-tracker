from django.shortcuts import render

from .models import Advisory


def list_advisories(request):
    advisories = Advisory.objects.all()
    return render(request, "advisories/list.html", dict(advisories=advisories))
