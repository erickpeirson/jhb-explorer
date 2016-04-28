from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.core.cache import caches
from django.template import RequestContext, loader
from django.http import Http404

from explorer.models import Document, TopicDocumentAssignment

import json
from collections import Counter, defaultdict

cache = caches['default']



def document_by_doi(request, document_doi):
    """
    Wrapper for :meth:`document` that uses ``doi`` rather than ``pk``.
    """
    try:
        document_id = Document.objects.filter(doi=document_doi[:-1]).values_list('id', flat=True)[0]
    except IndexError:
        raise Http404('No such document')
    return document(request, document_id)


def _related_documents(document):
    """
    Retrieve data about :class:`.Document`\s that are related to ``document``
    by virtue of shared prominent topics.

    Returns a list of 7-tuples intended for use in the "related documents"
    component of ``document.html``.
    """

    fields = [
        'weight',
        'topic__in_documents__document__id',
        'topic__in_documents__document__title',
        'topic__in_documents__document__publication_date',
        'topic__in_documents__weight',
        'topic__in_documents__topic__id',
        'topic__in_documents__topic__label',
    ]

    # Iterating over Pages would be more precise, but is way too costly. This
    #  gets us pretty darn good results.
    results = document.contains_topic.filter(weight__gte=5).values_list(*fields)
    document_weights = Counter()
    topic_weights = {}              # Overall prevalance in the corpus.
    topic_ids = defaultdict(set)    # Topics that are the basis for a match.
    topic_labels = {}

    for result in results:
        # QuerySet.values_list() returns an N-tuple, where N is the number of
        #  fields SELECTed.
        this_weight, doc_id, doc_title, doc_pd, weight, topic_id, topic_label = result

        # We expect to find the focal document quite a bit here.
        if doc_id == document.id:
            continue

        # We need to weight shared topics by their overall prevalance.
        if topic_id not in topic_weights:
            topic_labels[topic_id] = topic_label
            topic_weights[topic_id] = TopicDocumentAssignment.objects\
                                        .filter(topic_id=topic_id,
                                                weight__gte=5)\
                                        .count()

        if this_weight > 5 and weight > 5:
            document_weights[(doc_id, doc_title, doc_pd)] += 1./topic_weights[topic_id]
            topic_ids[doc_id].add(topic_id)

    # We want all results together in a single iterator for ease of use in the
    #  template.
    docs, weights = zip(*sorted(document_weights.items(),
                                key=lambda dw: dw[1])[::-1][:20])
    ids, titles, dates = zip(*docs)
    # Topics are (label, id) 2-tuples.
    topics = [[(topic_labels[tid], tid) for tid in list(topic_ids[i])] for i in ids]
    return zip(ids, titles, dates, weights, topics)


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
    elif data == 'json':
        response_data = json.dumps({
            'id': document.id,
            'title': document.title,
            'date': document.publication_date,
        }, indent=4)
        return HttpResponse(response_data, content_type="application/json")

    else:
        template = loader.get_template('explorer/document.html')
        context = RequestContext(request, {
            'document': document,
            'pages': zip(pages, topics),
            'active': 'documents',
            'related_documents': _related_documents(document),
        })
        if initialTopic:
            context['initialTopic'] = initialTopic
        return HttpResponse(template.render(context))
