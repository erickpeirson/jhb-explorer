from django.shortcuts import get_object_or_404, render, redirect
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q, Avg, Max, Min
from django.conf import settings
from django.db.models import Sum
from django.db.models import Count
from django.contrib.staticfiles.templatetags.staticfiles import static

from rest_framework.renderers import JSONRenderer
from django.core.cache import caches

from collections import Counter, defaultdict
from itertools import combinations
from math import log, floor

cache = caches['default']

import json
import igraph
import os

from explorer.serializers import TopicSerializer
from explorer.models import *


def npmi(f_xy, f_x, f_y):
    pmi = log(f_xy/(f_x * f_y))
    try:
        npmi = pmi/(-1. * log(f_xy))
    except ZeroDivisionError:
        npmi = 0.


def home(request):
    """
    Provides the root view of the application.
    """

    template = loader.get_template('explorer/home.html')
    context = RequestContext(request, {})
    response_data = template.render(context)
    content_type = "text/html"
    return HttpResponse(response_data, content_type=content_type)

def organism(request, taxon_id):
    """
    Displays the detail view for a single taxon.
    """
    data = request.GET.get('data', None)
    start = request.GET.get('start', 1968)
    end = request.GET.get('end', 2013)
    taxon = get_object_or_404(Taxon, pk=taxon_id)

    if data == 'time':
        cache_key = 'organism__time__%s__%i_%i' % (taxon_id, start, end)
        response_data = cache.get(cache_key)
        if response_data is None:
            queryset = TaxonDocumentOccurrence.objects.filter(
                taxon_id__in=[child.id for child in taxon.children()],
                document__publication_date__gte=start,
                document__publication_date__lte=end).values('document__publication_date')

            by_date = Counter([v['document__publication_date'] for v in queryset])

            # Fill in years with no occurrences.
            for i in xrange(start, end + 1):
                by_date[i] += 0.

            response_data = json.dumps({'taxon': taxon_id, 'dates': by_date.keys(), 'values': by_date.values()})
            cache.set(cache_key, response_data, 3600)
        content_type = "application/json"

    elif data == 'tree':
        depth = request.GET.get('depth', 2)
        cache_key = 'organism__tree__%s__%i_%i__%i' % (taxon_id, start, end, depth)
        response_data = cache.get(cache_key)
        if response_data is None:
            response_data = json.dumps({
                'focal': taxon_id,
                'direct': [t.id for t in taxon.parents()],
                'data': taxon.tree(depth_up=depth)
            })
            cache.set(cache_key, response_data, 3600)
        content_type = "application/json"
    elif data == 'json':
        document_queryset = TaxonDocumentOccurrence.objects\
            .filter(taxon_id__in=taxon.children())\
            .order_by('-weight')\
            .filter(document__publication_date__gte=start)\
            .filter(document__publication_date__lt=end)\
            .select_related('document')

        response_data = json.dumps({
            'id': taxon.id,
            'label': taxon.scientific_name,
            'document_count': document_queryset.count(),
            'max_weight': document_queryset.aggregate(max_weight=Max('weight'))['max_weight'],
            'documents': [{
                'id': assignment.document.id,
                'title': assignment.document.title,
                'pubdate': assignment.document.publication_date,
                'weight': assignment.weight
            } for assignment in document_queryset]
        })
        content_type = "application/json"
    else:

        template = loader.get_template('explorer/organism.html')
        context = RequestContext(request, {
            'taxon': taxon,
            'active': 'organisms',
        })
        response_data = template.render(context)
        content_type = "text/html"
    return HttpResponse(response_data, content_type=content_type)


def organisms(request):
    """
    Displays the root view of the taxon browser.
    """

    data = request.GET.get('data', None)
    start = request.GET.get('start', 1968)
    end = request.GET.get('end', 2013)
    division = request.GET.get('division', None)

    if data == 'time':

        division_series = []
        for value in Taxon.objects.all().values('division').distinct():
            if value['division'] is None:
                continue
            queryset = TaxonDocumentOccurrence.objects.filter(taxon__division=value['division']).values('document__publication_date')
            by_date = Counter([v['document__publication_date'] for v in queryset])
            for i in xrange(start, end + 1):
                by_date[i] += 0
            division_series.append((value['division'], by_date))

        response_data = json.dumps({'divisions': [{'division': division, 'dates': counts.keys(), 'values': counts.values()} for division, counts in division_series]})
        content_type = "application/json"

    elif data == 'json':
        queryset = Taxon.objects.filter(occurrences__document__publication_date__gte=start, occurrences__document__publication_date__lte=end)
        if division and division != 'null' and division != 'undefined':
            queryset = queryset.filter(division=division);
        queryset = queryset.annotate(num_occurrences=Count('occurrences')).order_by('-num_occurrences')[:20]

        response_data = json.dumps({
            'data': [{
                'id': obj.id,
                'scientific_name': obj.scientific_name,
                'occurrences': obj.num_occurrences,
                'rank': obj.rank,
            } for obj in queryset]
        })
        content_type = "application/json"

    else:

        template = loader.get_template('explorer/organisms.html')
        context = RequestContext(request, {
            'divisions': Taxon.objects.all().values('division').distinct(),
            'active': 'organisms',
        })
        response_data = template.render(context)
        content_type = "text/html"
    return HttpResponse(response_data, content_type=content_type)


def topic_colocates(startYear=None, endYear=None, criterion=0.1):
    queryset = Document.objects.all()
    if startYear:
        queryset = queryset.filter(publication_date__gte=startYear)
    if endYear:
        queryset = queryset.filter(publication_date__lte=endYear)

    N = queryset.count()
    colocate_counts = Counter()
    colocate_documents = defaultdict(list)
    occurrence_counts = Counter()
    for document in queryset:
        for assignmentA, assignmentB in combinations(document.contains_topic.all(), 2):
            pair = tuple(sorted([assignmentA.topic.id, assignmentB.topic.id]))
            colocate_counts[pair] += 1.
            colocate_documents[pair].append(document.id)
        for assignment in document.contains_topic.all():
            occurrence_counts[assignment.topic.id] += 1.

    nPMI = {}
    colocate_documents_select = {}
    for pair, cocount in colocate_counts.iteritems():
        f_xy = cocount/N
        f_x = occurrence_counts[pair[0]]/N
        f_y = occurrence_counts[pair[1]]/N

        pmi = log(f_xy/(f_x * f_y))
        try:
            npmi = pmi/(-1. * log(f_xy))
        except ZeroDivisionError:
            npmi = 0.

        if npmi >= criterion:
            nPMI[pair] = npmi
            colocate_documents_select[pair] = colocate_documents[pair]
    return nPMI, colocate_documents_select


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


def topic_time(request, topic_id, start=None, end=None, normed=True):
    """
    Genereate a JSON response containing time-series data for a single topic.
    """

    queryset = TopicFrequency.objects.filter(topic_id=topic_id).order_by('year')

    if start:
        queryset = queryset.filter(year__gte=start)
    if end:
        queryset = queryset.filter(year__lt=end)

    by_date = Counter({instance.year: instance.frequency for instance in queryset})

    if start is not None:
        for year in xrange(start, max(by_date.keys())):
            by_date[year] += 0.
    if end is not None:
        for year in xrange(min(by_date.keys()), end + 1):
            by_date[year] += 0.

    values = by_date.values()

    return {'dates': by_date.keys(), 'values': values, 'topic': topic_id}


def topics_time(request):
    """
    Generates a JSON response containing information about the representation of
    topics over time.
    """

    response_data =  cache.get('topics_time')
    if response_data is None:
        queryset = Topic.objects.all()
        data = [topic_time(request, topic.id, start=1968, end=2013) for topic in queryset]
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
    endYear = int(floor(float(request.GET.get('endyear', 2013))))

    fname = 'topic_graph_%i_%i.json' % (startYear, endYear)
    fpath = '/'.join(['explorer', 'data', fname])
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
        content_type = "text/html"
    return HttpResponse(response_data, content_type=content_type)


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
    start_year = request.GET.get('start', None)
    end_year = request.GET.get('end', None)
    min_weight = request.GET.get('weight', 5)

    document_queryset = topic.in_documents.order_by('-weight')
    if start_year:
        document_queryset = document_queryset.filter(document__publication_date__gte=start_year)
    if end_year:
        document_queryset = document_queryset.filter(document__publication_date__lt=end_year)
    document_queryset = document_queryset.filter(weight__gte=min_weight).select_related('document')

    term_queryset = topic.assigned_to.order_by('-weight')

    if data == 'json':
        data = {
            'id': topic.id,
            'label': topic.__unicode__(),
            'document_count': document_queryset.count(),
            'terms': [{
                'term': assignment.term.term,
                'weight': assignment.weight,
                } for assignment in term_queryset[:20]],
            'documents': [{
                'id': assignment.document.id,
                'title': assignment.document.title,
                'pubdate': assignment.document.publication_date,
                'weight': assignment.weight
            } for assignment in document_queryset]
        }
        return HttpResponse(json.dumps(data), content_type='application/json')
    elif data == 'time':
        return HttpResponse(json.dumps(topic_time(request, topic_id)), content_type='application/json')
    else:   # Render HTML view.
        template = loader.get_template('explorer/topic.html')

        topic_colocates = []
        for colocated_topic in topic.colocated_with.all():
            colocation = TopicCoLocation.objects.get(Q(source_id=topic.id) & Q(target_id=colocated_topic.id))
            topic_colocates.append((colocated_topic, colocation))

        context = RequestContext(request, {
            'topic': topic,
            'associated_topics': topic.associated_with.all(),
            'topic_colocates': topic_colocates,
            'in_documents': document_queryset,
            'assigned_to': term_queryset[:20],
            'active': 'topics',
        })
        return HttpResponse(template.render(context))


def authors(request):
    """
    Search interface for authors.
    """

    template = loader.get_template('explorer/authors.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))


def author(request, author_id):
    """
    Detail view for authors.
    """

    author = get_object_or_404(Author, pk=author_id)

    template = loader.get_template('explorer/author.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))


def documents(request):
    """
    A search/filter interface for articles in the dataset.
    """
    template = loader.get_template('explorer/documents.html')
    context = RequestContext(request, {})
    return HttpResponse()


def document(request, document_id):
    """
    Displays details about a single article, including topics contained therein,
    distribution of topics across individual pages, citations, etc.
    """

    document = get_object_or_404(Document, pk=document_id)
    data = request.GET.get('data', None)
    initialTopic = request.GET.get('topic', None)
    pages = document.pages.order_by('page_number')
    topics = [page.contains_topic.filter(weight__gte=10).order_by('-weight') for page in pages]
    weights = []
    allTopics = sorted(list(set([assignment.topic.id for page in topics for assignment in page])))
    for assignments in topics:
        tweights = {}
        for topic in allTopics:
            assignmentHash = {assignment.topic.id: assignment.weight for assignment in assignments}
            if topic in assignmentHash:
                tweights[topic] = assignmentHash[topic]
            else:
                tweights[topic] = 0.
        weights.append(tweights)

    if data == 'chart':
        elements = {
            'allTopics': allTopics,
            'pages': [page.page_number for page in pages],
            'weights': weights,
        }

        response_data = json.dumps(elements, indent=4)
        return HttpResponse(response_data, content_type="application/json")
    else:
        template = loader.get_template('explorer/document.html')
        context = RequestContext(request, {
            'document': document,
            'pages': zip(pages, topics),
            'active': 'documents',
        })
        if initialTopic:
            context['initialTopic'] = initialTopic
        return HttpResponse(template.render(context))


def entities(request):
    """
    Search/filter interface for entities.
    """

    template = loader.get_template('explorer/entities.html')
    context = RequestContext(request, {})
    return HttpResponse()


def entity(request, entity_id):
    """
    Display details about an entity, including documents/pages in which it
    occurs, associated topics, authority information, etc.
    """

    entity = get_object_or_404(Entity, pk=entity_id)

    template = loader.get_template('explorer/entity.html')
    context = RequestContext(request, {
        'entity': entity,
    })
    return HttpResponse()


def terms(request):
    """
    Search/filter interface for terms.
    """

    template = loader.get_template('explorer/terms.html')
    context = RequestContext(request, {})
    return HttpResponse()


def term(request, term_id):
    """
    Display details about a term, including documents/pages where it occurs,
    topics with which it is associated, etc.
    """
    term = get_object_or_404(Term, pk=term_id)

    template = loader.get_template('explorer/term.html')
    context = RequestContext(request, {
        'term': term,
    })
    return HttpResponse()


def citations(request):
    """
    Displays a DAG showing citations among JHB articles. Overlays for topics.
    """

    template = loader.get_template('explorer/citations.html')
    context = RequestContext(request, {})
    return HttpResponse()
