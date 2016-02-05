from django.shortcuts import get_object_or_404, render, redirect
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q

from rest_framework.renderers import JSONRenderer
from django.core.cache import caches

cache = caches['default']

import json

from explorer.serializers import TopicSerializer
from explorer.models import *


def topics_json(request):
    """
    Generates a JSON response containing topic data.
    """
    queryset = Topic.objects.all()
    serializer = TopicSerializer(queryset, many=True)
    renderer = JSONRenderer()
    response_data = renderer.render(serializer.data,
                                    'application/json; indent=4')
    content_type = "application/json"
    return HttpResponse(response_data, content_type=content_type)


def topics_graph(request):
    """
    Generates a JSON response containing data for the topic co-location
    network visualization.
    """
    queryset = Topic.objects.all()
    response_data = cache.get('topic_graph')
    if response_data is None:
        elements = []
        minsize = 5000
        maxsize = 0
        for topic in queryset:
            terms = [term for term in topic.assigned_to.order_by('-weight')[:20]]
            max_weight = max([term.weight for term in terms])
            min_weight = min([term.weight for term in terms])

            documents = [doc for doc in topic.in_documents.order_by('-weight')[:5]]
            elements.append({
                'data': {
                    'id': str(topic.id),
                    'size': topic.in_documents.count(),
                    'terms': [
                        {
                            'id': assignment.id,
                            'term': assignment.term.term,
                            'weight': 8 + 10*(assignment.weight - min_weight)/(max_weight - min_weight)
                        }
                        for assignment in terms
                    ],
                    'documents': [
                        {
                            'id': occurrence.id,
                            'title': occurrence.document.title,
                            'pubdate': occurrence.document.publication_date,
                            'weight': occurrence.weight,
                        }
                        for occurrence in documents
                    ],
                }
            })

        edges = {}
        for colocate in TopicCoLocation.objects.all():
            pair = tuple(sorted([colocate.source.id, colocate.target.id]))
            if pair not in edges:
                documents = set([page.belongs_to for page in colocate.pages.all()[:10]])
                edges[pair] = {
                    'data': {
                        'id': 'colocate_' + str(colocate.id),
                        'source': str(colocate.source.id),
                        'target': str(colocate.target.id),
                        'weight': colocate.weight,
                        'documents': [
                            {
                                'id': doc.id,
                                'title': doc.title,
                                'pubdate': doc.publication_date
                            }
                            for doc in documents
                        ]
                    }
                }

        elements += edges.values()
        response_data = json.dumps(elements, indent=4)
        cache.set('topic_graph', response_data, 3600)
    content_type = "application/json"
    return HttpResponse(response_data, content_type=content_type)


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

    template = loader.get_template('explorer/topic.html')

    topic_colocates = []
    for colocated_topic in topic.colocated_with.all():
        colocation = TopicCoLocation.objects.get(Q(source_id=topic.id) & Q(target_id=colocated_topic.id))
        topic_colocates.append((colocated_topic, colocation))

    context = RequestContext(request, {
        'topic': topic,
        'associated_topics': topic.associated_with.all(),
        'topic_colocates': topic_colocates,
        'in_documents': topic.in_documents.filter(weight__gte=10).order_by('-weight'),
        'assigned_to': topic.assigned_to.order_by('-weight')[:20],
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

    document = get_object_or_404(JHBArticle, pk=document_id)
    data = request.GET.get('data', None)
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
