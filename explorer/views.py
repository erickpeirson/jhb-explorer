from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, render, redirect
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q, Avg, Max, Min, Sum, Count
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils.encoding import smart_text

from rest_framework.renderers import JSONRenderer
from django.core.cache import caches

from collections import Counter, defaultdict, OrderedDict
from itertools import combinations, groupby
from math import log, floor

cache = caches['default']

import json
import os

from explorer.serializers import TopicSerializer
from explorer.models import *


def npmi(f_xy, f_x, f_y):
    pmi = log(f_xy/(f_x * f_y))
    try:
        npmi = pmi/(-1. * log(f_xy))
    except ZeroDivisionError:
        # This occurs when the joint probability estimator (frequency) is zero.
        # The limit of npmi  as p_xy -> 0. (for p_x > 0 and p_y > 0) is -1.,
        #  complete antipathy.
        npmi = -1.


def home(request):
    """
    Provides the root view of the application.
    """

    template = loader.get_template('explorer/home.html')
    context = RequestContext(request, {})
    response_data = template.render(context)
    content_type = "text/html; charset=utf-8"
    return HttpResponse(response_data, content_type=content_type)


def _organism_topics(taxon):
    """
    Related topics for a specific organism.
    """

    queryset = TopicPageAssignment.objects.filter(weight__gte=5, page__belongs_to__taxon_occurrences__taxon__id__in=[t.id for t in taxon.children()])
    fields = [
        'weight',
        'topic__id',
        'topic__label',
    ]


    # topic_count = Counter()
    # for tid, ntaxa in TopicPageAssignment.objects.annotate(num_taxa=Count('page__belongs_to__taxon_occurrences')).filter(weight__gte=5).values_list('topic__id', 'num_taxa'):
    #     topic_count[tid] += ntaxa
    topic_count = Counter(TopicPageAssignment.objects.filter(weight__gte=5).values_list('topic__id', flat=True))

    topic_weights = Counter()
    for weight, topic_id, label in queryset.values_list(*fields):
        topic_weights[(topic_id, label)] += weight/topic_count[topic_id]

    if len(topic_weights) == 0:
        return []

    topics, weights = zip(*topic_weights.items())
    topic_ids, topic_labels = zip(*topics)
    return sorted(zip(topic_ids, topic_labels, [100.*w/max(weights) for w in weights]), key=lambda r: r[2])[::-1][:5]


def organism(request, taxon_id):
    """
    The detail view for a single taxon.
    """

    data = request.GET.get('data', None)
    start = request.GET.get('start', 1968)
    end = request.GET.get('end', 2018)
    taxon = get_object_or_404(Taxon, pk=taxon_id)

    if data == 'time':  # Data about the occurrence of the taxon over time.
        cache_key = 'organism__time__%s__%i_%i' % (taxon_id, start, end)
        response_data = cache.get(cache_key)
        if response_data is None:

            filter_params = {
                # We include occurrences of all child taxa.
                'taxon_id__in': [child.id for child in taxon.children()],
                # Date ranges are inclusive of the start date...
                'document__publication_date__gte': start,
                # ...and exclusive of the end date.
                'document__publication_date__lt': end
            }
            # We only need the pubdate, so values() saves us database overhead.
            results = TaxonDocumentOccurrence.objects.filter(**filter_params)\
                            .values('document__publication_date')

            # Counter won't yield values for intermediate years that don't have
            #  occurrences, so....
            by_date = Counter([r['document__publication_date']
                               for r in results])
            # We have to explicitly fill in those years with 0 values.
            for i in xrange(start, end + 1):
                by_date[i] += 0.

            response_data = json.dumps({
                'taxon': taxon_id,
                'dates': by_date.keys(),
                'values': by_date.values()
            })
            cache.set(cache_key, response_data, 3600)
        content_type = "application/json"

    elif data == 'tree':    # Yields local lineage data for the focal taxon.
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

    elif data == 'json':    # Yields data about the documents in which the
                            #  taxon occurs.
        document_queryset = TaxonDocumentOccurrence.objects\
            .filter(taxon_id__in=taxon.children())\
            .order_by('-weight')\
            .filter(document__publication_date__gte=start)\
            .filter(document__publication_date__lt=end)\
            .select_related('document')

        weight_agg = document_queryset.aggregate(max_weight=Max('weight'))
        response_data = json.dumps({
            'id': taxon.id,
            'label': taxon.scientific_name,
            'document_count': document_queryset.count(),
            'max_weight': weight_agg['max_weight'],
            'documents': [{
                'id': assignment.document.id,
                'title': assignment.document.title,
                'pubdate': assignment.document.publication_date,
                'weight': assignment.weight
            } for assignment in document_queryset]
        })
        content_type = "application/json"

    else:   # Provides the templated detail view for this Taxon.
        template = loader.get_template('explorer/organism.html')

        names = []
        categories = []
        for n, resources in groupby(sorted(taxon.resources.all(),
                                           key=lambda g: g.category),
                                    lambda g: g.category):
            types = []
            sresources = []
            for s, subresources in groupby(sorted(resources,
                                                  key=lambda r: r.subject_type),
                                           lambda r: r.subject_type):
                types.append(s)
                sresources.append(list(subresources))
            names.append(n)
            categories.append(zip(types, sresources))
        resourcegroups = zip(range(len(names)), names, categories)

        context = RequestContext(request, {
            'taxon': taxon,
            'active': 'organisms',
            'resourcegroups': resourcegroups,
            'topics': _organism_topics(taxon)
        })
        response_data = template.render(context)
        content_type = "text/html; charset=utf-8"
    return HttpResponse(response_data, content_type=content_type)


def organisms(request):
    """
    Displays the root view of the taxon browser.
    """

    data = request.GET.get('data', None)
    start = request.GET.get('start', 1968)
    end = request.GET.get('end', 2018)
    division = request.GET.get('division', None)

    if data == 'time':
        division_series = []
        for value in Taxon.objects.all().values('division').distinct():
            if value['division'] is None:
                continue
            queryset = TaxonDocumentOccurrence.objects.filter(taxon__division=value['division']).values('document__publication_date')
            by_date = Counter([v['document__publication_date'] for v in queryset])
            for i in xrange(start, end):
                by_date[i] += 0
            division_series.append((value['division'], by_date))

        response_data = json.dumps({
            'divisions': [{
                'division': division,
                'dates': counts.keys(),
                'values': counts.values()
            } for division, counts in division_series]
        })
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
        content_type = "text/html; charset=utf-8"
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
    """
    params = {
        'topic_id': topic_id,
        'weight__gte': min_weight,
    }

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
    return [{
        'id': result['page__belongs_to__id'],
        'pubdate': result['page__belongs_to__publication_date'],
        'title': result['page__belongs_to__title'],
        'weight': result['weight']
    } for result in queryset.distinct('page__belongs_to__id').values(*document_fields)]


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
            'label': topic.__unicode__(),
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
            'topic_colocates': topic_colocates,
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


def authors(request):
    """
    Search interface for authors.
    """

    template = loader.get_template('explorer/authors.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))


def _topic_authors(topic, top=20, min_weight=5.):
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
        # print names[author_id]

        counts[author_id] += value

    authors, weights = zip(*counts.items())
    return sorted(zip(authors, weights, [smart_text(names[a]) for a in authors]), key=lambda a: a[1])[::-1][:top]


def _similar_authors(author, top=20, norm=True):
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
                            key=lambda row: row[1])[::-1][:20]

    # Have to pull these back apart so that we can include author names in the
    #  response.
    author_ids, weights = zip(*sorted_authors)
    combined_data = zip(author_ids, weights, [names[a] for a in author_ids])

    return combined_data#sorted(combined_data, key=lambda row: row[1])[::-1][:top]


def _author_topics(author, top=20, min_weight=5., norm=True):
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
    })
    return HttpResponse(template.render(context))


def documents(request):
    """
    A search/filter interface for articles in the dataset.
    """
    template = loader.get_template('explorer/documents.html')
    context = RequestContext(request, {})
    return HttpResponse()


def document_by_doi(request, document_doi):
    """
    Wrapper for :meth:`document` that uses ``doi`` rather than ``pk``.
    """
    document_id = Document.objects.filter(doi=document_doi[:-1]).values_list('id', flat=True)[0]
    return document(request, document_id)


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


def _locations_data(start=1968, end=2017, topic=None, author=None):
    """

    """
    queryset = Document.objects.filter(publication_date__gte=start, publication_date__lt=end)
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
