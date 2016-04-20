from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.core.cache import caches
from django.template import RequestContext, loader
from django.utils.encoding import smart_text

cache = caches['default']

from explorer.models import Author, Topic, TopicDocumentAssignment

from math import log
from itertools import combinations, groupby
from collections import Counter, OrderedDict
import json


def _external_resources(author):
    queryset = author.resources.all()
    return queryset.values_list('resource__resource_location',
                                'resource__resource_type')





def _topic_authors(topic, top=5, min_weight=5.):
    queryset = topic.in_documents.filter(weight__gte=min_weight)
    fields = [
        'document__authors__id',
        'document__authors__surname',
        'document__authors__forename',
        'weight',
    ]

    results = queryset.values_list(*fields).order_by('-weight')

    counts = Counter()
    names = OrderedDict()
    for author_id, surname, forename, value in results:
        if not author_id:
            continue
        names[author_id] = u', '.join([surname, forename]).title()

        counts[author_id] += value

    authors, weights = zip(*counts.items())
    return sorted(zip(authors, weights, [smart_text(names[a]) for a in authors]), key=lambda a: a[1])[::-1][:top]


def _similar_authors(author, top=5, norm=True):
    """
    Find authors who have published on similar topics.
    """

    top_authors = OrderedDict()
    names = {}
    for topic, weight, _ in _author_topics(author, norm=True):
        # We'll use the number of documents containing this topic to weight
        #  similarities, below.
        topic_count = TopicDocumentAssignment.objects\
                        .filter(topic_id=topic, weight__gte=5)\
                        .count()

        candidates = _topic_authors(Topic.objects.get(pk=topic))

        for author_id, value, name in candidates:
            if author_id == author.id:
                continue
            names[author_id] = name

            # Similarity between authors is weighted by the prominance of the
            #  topic in the focal author's work, and by the overall prevalence
            #  of the topic in the corpus (number of documents in which it
            #  occurs). This should de-emphasize widespread topics focused on
            #  rhetorical patterns and emphasize more niche, content-oriented
            #  topics.
            top_authors[author_id] = value * weight / log(topic_count)

    if norm:
        max_weight = max(top_authors.values())
        top_authors = {k: 100.*v/max_weight for k, v in top_authors.iteritems()}

    # Take only the top ``top`` most similar authors.
    sorted_authors = sorted(top_authors.items(),
                            key=lambda row: row[1])[::-1][:top]

    # Have to pull these back apart so that we can include author names in the
    #  response.
    author_ids, weights = zip(*sorted_authors)
    combined_data = zip(author_ids, weights, [names[a] for a in author_ids])

    return combined_data#sorted(combined_data, key=lambda row: row[1])[::-1][:top]


def _author_topics(author, top=5, min_weight=5., norm=True):
    """
    Calculate the top topics about which an author has written.

    Returns the top ``top`` topics in descending order of weight (relative
    representation in pages written by this author).
    """

    queryset = author.works.filter(pages__contains_topic__weight__gte=min_weight)

    fields = [
        'pages__contains_topic__topic__id',
        'pages__contains_topic__weight',
        'pages__contains_topic__topic__label',
    ]

    # The resultset contains one item per Page,Topic pair, so we have to
    #  separate out the weights and sum them for each Topic.
    topic_counts, topic_labels = Counter(), {}
    topics, weights, labels = zip(*queryset.values_list(*fields))

    for topic_id, weight, label in zip(topics, weights, labels):
        # We'll use the number of documents containing this topic to weight
        #  similarities, below.
        topic_count = TopicDocumentAssignment.objects\
                        .filter(topic_id=topic_id, weight__gte=5)\
                        .count()

        # Using the log(count) gives us a smoother weighting than the raw
        #  count value.
        topic_counts[topic_id] += weight/log(topic_count)
        topic_labels[topic_id] = label

    if norm:
        # Topic weight is normalized by itself, since the number of pages per
        #  author will vary widely.
        max_weight = max(topic_counts.values())
        topic_counts = {k: 100.*v/max_weight for k, v in topic_counts.iteritems()}

    # We want these all together in a single iterable for ease of use in the
    #  template.
    combined_data = zip(topic_counts.keys(),    # Topic ids.
                        topic_counts.values(),  # Topic weights (normed).
                        topic_labels.values())  # Topic labels.

    # Sort by weight (descending).
    return sorted(combined_data, key=lambda o: o[1])[::-1][:top]


def author(request, author_id):
    """
    Detail view for authors.
    """

    author = get_object_or_404(Author, pk=author_id)

    template = loader.get_template('explorer/author.html')
    context = RequestContext(request, {
        'author': author,
        'documents': author.works.all().order_by('publication_date'),
        'topics': _author_topics(author),
        'similar_authors': _similar_authors(author),
        'active': 'authors',
        'resources': _external_resources(author),
    })
    return HttpResponse(template.render(context))


def authors(request):
    """
    Search interface for authors.
    """

    template = loader.get_template('explorer/authors.html')
    context = RequestContext(request, {
        'active': 'Authors'
    })
    return HttpResponse(template.render(context))
