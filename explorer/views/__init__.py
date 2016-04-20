from __future__ import unicode_literals

from django.template import RequestContext, loader
from django.http import HttpResponse

from explorer.forms import JHBSearchForm


def home(request):
    """
    Provides the root view of the application.
    """

    template = loader.get_template('explorer/home.html')
    search_form = JHBSearchForm()
    context = RequestContext(request, {
        'search_form': search_form,
    })
    response_data = template.render(context)
    content_type = "text/html; charset=utf-8"
    return HttpResponse(response_data, content_type=content_type)


def citations(request):
    """
    Displays a DAG showing citations among JHB articles. Overlays for topics.
    """

    template = loader.get_template('explorer/citations.html')
    context = RequestContext(request, {})
    return HttpResponse()
