from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.core.cache import caches
from django.template import RequestContext, loader
from django.conf import settings

from explorer.models import Document, Location

import json

cache = caches['default']


def _locations_data(start=1968, end=2017, topic=None, author=None):
    """

    """
    queryset = Document.objects.filter(publication_date__gte=start,
                                       publication_date__lt=end)
    if topic:
        queryset = queryset.filter(contains_topic__topic__id=topic)
    if author:
        queryset = queryset.filter(authors__id=author)

    return queryset.geojson()


def locations(request):
    """
    Displays a geovisualization showing where articles are set.
    """

    data = request.GET.get('data', None)
    start = request.GET.get('start', 1968)
    end = request.GET.get('end', 2017)
    author = request.GET.get('author', None)
    try:
        topic = int(request.GET.get('topic', None))
    except TypeError:
        topic = None

    if data == 'json':
        response_data, content_type = _locations_data(start, end, topic, author), 'application/json'
    else:
        template = loader.get_template('explorer/locations.html')
        context_data = {
            'data': u'?data=json',
            'start': start,
            'end': end,
            'active': 'locations',
            'MAPBOX_TOKEN': settings.MAPBOX_TOKEN,
        }
        if topic:
            context_data.update({'topic': topic})
        context = RequestContext(request, context_data)
        response_data, content_type = template.render(context), 'text/html'
    return HttpResponse(response_data, content_type=content_type)


def location(request, location_id):
    location = get_object_or_404(Location, pk=location_id)

    data = request.GET.get('data', None)
    start = request.GET.get('start', 1968)
    end = request.GET.get('end', 2017)
    topic = request.GET.get('topic', None)

    if data == 'json':
        fields = [
            'document__id',
            'document__title',
            'document__publication_date'
        ]
        response_data = json.dumps({
            'documents': [{
                'id': result['document__id'],
                'title': result['document__title'],
                'date': result['document__publication_date']
            } for result in location.documents.values(*fields)]
        })

        return HttpResponse(response_data, content_type='application/json')
    return HttpResponseRedirect(reverse('locations'))
