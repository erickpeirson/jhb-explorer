from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.core.cache import caches
from django.template import RequestContext, loader
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db.models import Q, Count

from explorer.models import (Topic, TermTopicAssignment, TopicPageAssignment,
                             TopicCoLocation, Page)
from explorer.serializers import TopicSerializer

from rest_framework.renderers import JSONRenderer

from math import floor
from collections import Counter
from itertools import groupby
import json

from authors import _topic_authors

cache = caches['default']


def topics_json(request):
    """
    Generates a JSON response containing topic data.
    """
    queryset = Topic.objects.all()
    serializer = TopicSerializer(queryset, many=True)
    renderer = JSONRenderer()
    response_data = renderer.render(serializer.data,
                                    'application/json; indent=4')
    return HttpResponse(response_data, content_type="application/json")


def topic_time(request, topic_id, start=1968, end=2016, norm={}):
    """
    Genereate a JSON response containing time-series data for a single topic.
    """

    queryset = TopicPageAssignment.objects.filter(topic_id=topic_id, weight__gte=5)

    if start:
        queryset = queryset.filter(page__belongs_to__publication_date__gte=start)
    if end:
        queryset = queryset.filter(page__belongs_to__publication_date__lt=end)

    date = 'page__belongs_to__publication_date'    # Yucky long field name.
    by_date = Counter(dict(queryset.values_list(date).annotate(Count(date))))

    # Adding 0 to a Counter initializes the corresponding key if there is no
    #  value. Turns out it also sorts the Counter by the order of assignment,
    #  so we get sorted values for free!
    for year in xrange(start, end + 1):
        by_date[year] += 0.

    if norm:
        by_date = {k: v/norm.get(k, 1.) for k, v in by_date.iteritems()}

    values = by_date.values()

    return {'dates': by_date.keys(), 'values': values, 'topic': topic_id}


def topics_time(request):
    """
    Generates a JSON response containing information about the representation of
    topics over time.
    """

    response_data =  cache.get('topics_time')
    if response_data is None:
        # N_documents = Counter(Document.objects.values_list('publication_date', flat=True))
        Npages =  dict(Page.objects.values_list('belongs_to__publication_date').annotate(Count('belongs_to__publication_date')))

        # queryset = Topic.objects.values_list('id', flat=True)
        queryset = TopicPageAssignment.objects.filter(weight__gte=5).order_by('page__belongs_to__publication_date')

        # if start:
        #     queryset = queryset.filter(page__belongs_to__publication_date__gte=start)
        # if end:
        #     queryset = queryset.filter(page__belongs_to__publication_date__lt=end)

        results = queryset.values_list('topic__id', 'page__belongs_to__publication_date').annotate(Count('page__belongs_to__publication_date'))

        def rebuild(d):
            """
            Rebuilds 3-tuples in ``d`` into a result dict suitable for
            inclusion in the response.
            """

            # The 3-tuple is comprised of topic id, year, and count.
            t, y, v = zip(*d)

            # We have to order the results by topic in order to use groupby
            #  (see below), but as a result we lose sorting by date. We also
            #  need to fill in 0 values for years with no occurrences. It turns
            #  out that a Counter will keep the order in which it was last
            #  assigned, so by adding 0 to each year in order we kill two birds
            #  with one stone.
            counts = Counter(dict(zip(y, v)))
            for i in xrange(1968, 2017):    # TODO: don't hardcode.
                counts[i] += 0.
            y, v = zip(*counts.items())
            return {'topic': t[0], 'values': v, 'dates': y}

        # We have a flat result set of 3-tuples, with each topic-date pair
        #  occurring as a separate tuple. Groupby allows us to cluster tuples
        #  together by topic. This only works if the iterable is sorted by
        #  topic id, otherwise we get several clusters per topic.
        data = [rebuild(g) for k, g in groupby(results.order_by('topic__id'), lambda r: r[0])]

        # This is now the most time-consuming part of the function!
        response_data = json.dumps({'topics': data})
        cache.set('topics_time', response_data, 36000)

    return HttpResponse(response_data, content_type='application/json')


def topics_graph(request):
    """
    Generates a JSON response containing data for the topic co-location
    network visualization.
    """
    # queryset = Topic.objects.all()
    startYear = int(floor(float(request.GET.get('startyear', 1968))))
    endYear = int(floor(float(request.GET.get('endyear', 2017))))

    fname = 'topic_graph_%i_%i.json' % (startYear, endYear)
    fpath = '/'.join(['explorer', 'data', 'json', fname])
    return HttpResponseRedirect(static(fpath))


def topics(request):
    """
    Displays all of the topics in the model (as a graph), with links to the
    ``topic`` view.
    """

    data = request.GET.get('data', None)
    if data == 'json':
        return topics_json(request)
    elif data == 'graph':
        return topics_graph(request)
    elif data == 'time':
        return topics_time(request)
    else:
        queryset = Topic.objects.all()
        template = loader.get_template('explorer/topics.html')
        context = RequestContext(request, {
            'topics': queryset,
            'active': 'topics',
        })
        response_data = template.render(context)
        content_type = "text/html; charset=utf-8"
    return HttpResponse(response_data, content_type=content_type)


def topic_terms(topic_id, top=20):
    """
    Provides data about the terms associated with a particular topic.

    Parameters
    ----------
    topic_id : int
        pk for a :class:`.Topic` instance.
    top : int
        Number of results to return.

    Returns
    -------
    list
        Each element is a ``dict`` containing data about the associated term.

    Examples
    --------
    ::

        >>> topic_terms(1, 10)
        [{'id': 5039, 'term': 'evolution', 'weight': 0.025}, ...]

    """

    params = params = {
        'topic_id': topic_id,
    }
    term_fields = [
        'term__id',
        'term__term',
        'weight',
    ]

    queryset = TermTopicAssignment.objects.filter(**params).order_by('-weight')
    return [{
        'id': result['term__id'],
        'term': result['term__term'],
        'weight': result['weight']
    } for result in queryset.values(*term_fields)[:top]]


def topic_documents(topic_id, min_weight=5.0, start=None, end=None):
    """
    Provides data about the documents in which a particular topic occurs.

    Parameters
    ----------
    topic_id : int
        Primary key for a :class:`.Topic` instance.
    min_weight : float
        Minimum weight for :class:`.TopicPageAssignment`\.
    start : int
        Starting publication date (inclusive).
    end : int
        Ending publication date (exclusive).

    Returns
    -------
    list
        ```[{'id', 'pubdate', 'title', 'weight'}]```
    """
    params = {'topic_id': topic_id, 'weight__gte': min_weight}
    if start:
        params.update({'page__belongs_to__publication_date__gte': start})
    if end:
        params.update({'page__belongs_to__publication_date__lt': end})

    queryset = TopicPageAssignment.objects.filter(**params)
    document_fields = [
        'weight',
        'page__belongs_to__id',
        'page__belongs_to__title',
        'page__belongs_to__publication_date',
    ]
    results = queryset.distinct('page__belongs_to__id').values(*document_fields)

    # Convert composite column names to simpler keys.
    combined = [{
        'id': result['page__belongs_to__id'],
        'pubdate': result['page__belongs_to__publication_date'],
        'title': result['page__belongs_to__title'],
        'weight': result['weight']
    } for result in results]

    # Sorted by weight (descending).
    return sorted(combined, key=lambda r: r['weight'])[::-1]


def _topic_geo(topic):
    """
    Returns data about the geographic distribution of articles containing a
    specific topic.
    """

    return


def topic(request, topic_id):
    """
    Displays details about a single topic, including articles in which the topic
    occurs, top associated terms, associated entities, etc.
    """
    topic = get_object_or_404(Topic, pk=topic_id)
    data = request.GET.get('data', None)

    # These are used to bound the representative documents for this topic. In
    #  the future, this could also apply to terms if a DTM is used. Start and
    #  end follow the usual inclusive/exclusive Python range behavior,
    #  respectively.
    start = request.GET.get('start', None)
    end = request.GET.get('end', None)
    min_weight = request.GET.get('weight', 5)

    document_queryset = topic.on_pages.all()
    if start:
        document_queryset = document_queryset.filter(page__belongs_to__publication_date__gte=start)
    if end:
        document_queryset = document_queryset.filter(page__belongs_to__publication_date__lt=end)
    document_queryset = document_queryset.filter(weight__gte=min_weight)

    term_queryset = topic.assigned_to.order_by('-weight')
    term_fields = [
        'term__term',
        'weight',
    ]
    terms = term_queryset.values(*term_fields)[:20]

    document_fields =[
        'page__belongs_to__id',
        'page__belongs_to__title',
        'page__belongs_to__publication_date',
        'weight'
    ]
    documents = document_queryset.values(*document_fields).distinct('page__belongs_to__id')

    if data == 'json':
        raw_data = {
            'id': topic.id,
            'label': topic.label,
            'document_count': document_queryset.count(),
            'terms': [{
                'term': assignment['term__term'],
                'weight': assignment['weight']/terms[0]['weight'],
            } for assignment in terms],
            'documents': sorted([{
                'id': assignment['page__belongs_to__id'],
                'title': assignment['page__belongs_to__title'],
                'pubdate': assignment['page__belongs_to__publication_date'],
                'weight': assignment['weight']
            } for assignment in documents], key=lambda a: a['weight'])[::-1],
        }
        response_data, content_type = json.dumps(raw_data), 'application/json'

    elif data == 'time':
        response_data = json.dumps(topic_time(request, topic_id))
        content_type = 'application/json'

    # Provides data about the documents in which this topic occurs.
    elif data == 'documents':
        response_data = json.dumps({
            'documents': topic_documents(topic_id, start=start, end=end)
        })
        content_type = 'application/json'
    elif data == 'terms':
        response_data = json.dumps({
            # Consumer can control the number of terms via a GET parameter.
            'id': topic_id,
            'label': topic.label,
            'terms': topic_terms(topic_id, top=request.GET.get('top', 20))
        })
        content_type = 'application/json'
    else:   # Render HTML view.
        template = loader.get_template('explorer/topic.html')

        topic_colocates = []
        for colocated_topic in topic.colocated_with.all():
            colocation = TopicCoLocation.objects.get(Q(source_id=topic.id) & Q(target_id=colocated_topic.id))
            topic_colocates.append((colocated_topic, colocation))

        authors = _topic_authors(topic)

        context = RequestContext(request, {
            'topic': topic,
            'associated_topics': topic.associated_with.all(),
            'topic_colocates': sorted(topic_colocates, key=lambda tc: tc[1].weight)[::-1],
            'in_documents': document_queryset,
            'assigned_to': [{
                'term': assignment['term__term'],
                'weight': assignment['weight']/terms[0]['weight'],
            } for assignment in terms],
            'active': 'topics',
            'authors': authors,
        })
        response_data, content_type = template.render(context), 'text/html'

    return HttpResponse(response_data, content_type=content_type)
