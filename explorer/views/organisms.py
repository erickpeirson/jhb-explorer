from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.core.cache import caches
from django.template import RequestContext, loader
from django.db.models import Max, Count
cache = caches['default']

from explorer.models import Taxon, TopicPageAssignment, TaxonDocumentOccurrence

from itertools import combinations, groupby
from collections import Counter
import json


def _organism_topics(taxon):
    """
    Related topics for a specific organism.
    """

    # Select pages in which this taxon and all of its descendants occur.
    child_ids = [t.id for t in taxon.children()]
    params = {
        'weight__gte': 5,
        'page__belongs_to__taxon_occurrences__taxon__id__in': child_ids,
    }
    queryset = TopicPageAssignment.objects.filter(**params)
    fields = [
        'weight',
        'topic__id',
        'topic__label',
    ]

    # Normalize topic weights by the overall frequency of each topic.
    topics = TopicPageAssignment.objects.filter(weight__gte=5)
    topic_count = Counter(topics.values_list('topic__id', flat=True))

    topic_weights = Counter()
    for weight, topic_id, label in queryset.values_list(*fields):
        # The more of the page occupied by the Topic (weight), the more likely
        #  the topic and the organism are discussed together.
        topic_weights[(topic_id, label)] += weight/topic_count[topic_id]

    if len(topic_weights) == 0:
        return []

    # Repackage for easy iteration in the template.
    topics, weights = zip(*topic_weights.items())
    topic_ids, topic_labels = zip(*topics)

    # We want weights to be relative to the most prominent topic for this
    #  particular organism.
    renormalized_weights = [100.*w/max(weights) for w in weights]
    combined = zip(topic_ids, topic_labels, renormalized_weights)

    return sorted(combined, key=lambda r: r[2])[::-1][:5]


def _organism_time(taxon, **kwargs):
    """
    Generate time-series data about the occurrence of a :class:`.Taxon`
    (including its children) across the corpus.

    Parameters
    ----------
    taxon : :class:`.Taxon`

    Returns
    -------
    dict
        ```{'taxon': int, 'dates': list, 'values': list}```
    """

    start = kwargs.get('start')
    end = kwargs.get('end')

    filter_params = {
        # We include occurrences of all child taxa.
        'taxon_id__in': [child.id for child in taxon.children()],
        # Date ranges are inclusive of the start date...
        'document__publication_date__gte': start,
        # ...and exclusive of the end date.
        'document__publication_date__lt': end
    }
    # We only need the pubdate, so values_list() saves us database overhead.
    results = TaxonDocumentOccurrence.objects.filter(**filter_params)\
                    .values_list('document__publication_date', flat=True)

    by_date = Counter(results)
    # Counter won't yield values for intermediate years that don't have
    #  occurrences, so we have to explicitly fill in those years with 0 values.
    #  This also sorts the Counter, so we get dates and values in order below.
    for i in xrange(start, end + 1):
        by_date[i] += 0.

    return {
        'taxon': taxon.id,
        'dates': by_date.keys(),
        'values': by_date.values()
    }


def _organism_tree(taxon, **kwargs):
    depth = kwargs.get('depth', 2)

    return {
        'focal': taxon.id,
        'direct': [t.id for t in taxon.parents()],
        'data': taxon.tree(depth_up=depth)
    }


def _organism_json(taxon, **kwargs):
    start = kwargs.get('start')
    end = kwargs.get('end')

    document_queryset = TaxonDocumentOccurrence.objects\
        .filter(taxon_id__in=taxon.children())\
        .order_by('document', '-weight')\
        .filter(document__publication_date__gte=start)\
        .filter(document__publication_date__lt=end)\
        .select_related('document')

    weight_agg = document_queryset.aggregate(max_weight=Max('weight'))
    documents = []
    for pk, document_group in groupby(document_queryset, key=lambda o: o.document.id):
        # The groupby iterator is consumed on the first pass, and we need it
        #  for several things.
        assignments = [asn for asn in document_group]
        weight = sum([asn.weight for asn in assignments])
        documents.append({
            'id': assignments[0].document.id,
            'title': assignments[0].document.title,
            'pubdate': assignments[0].document.publication_date,
            'weight': weight
        })

    return {
        'id': taxon.id,
        'label': taxon.scientific_name,
        'document_count': document_queryset.count(),
        'max_weight': weight_agg['max_weight'],
        'documents': documents,
    }


def _organism_resources(taxon, **kwargs):
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
    return zip(range(len(names)), names, categories)


def _divisions_time(**kwargs):
    start = kwargs.get('start')
    end = kwargs.get('end')

    division_series = []
    divisions = Taxon.objects.all().values_list('division', flat=True)\
                    .distinct()     # SQL is faster than Python.

    for division_id in divisions:
        if division_id is None:
            continue

        params = {'taxon__division': division_id}
        queryset = TaxonDocumentOccurrence.objects.filter(**params)
        results = queryset.values_list('document__publication_date',
                                       flat=True)
        by_date = Counter(results)

        # Fill in empty years with 0 values. This also sorts the counter.
        for i in xrange(start, end):
            by_date[i] += 0
        division_series.append((division_id, by_date))

    return {
        'divisions': [{
            'division': division,
            'dates': counts.keys(),
            'values': counts.values()
        } for division, counts in division_series]
    }


def _organisms_json(**kwargs):
    start = kwargs.get('start')
    end = kwargs.get('end')
    N = kwargs.get('N', 20)
    division = kwargs.get('division', None)

    params = {
        'occurrences__document__publication_date__gte': start,
        'occurrences__document__publication_date__lte': end
    }

    queryset = Taxon.objects.filter(**params)
    if division and division != 'null' and division != 'undefined':
        queryset = queryset.filter(division=division);

    queryset = queryset.annotate(num_occurrences=Count('occurrences'))\
        .order_by('-num_occurrences')[:N]

    return {
        'data': [{
            'id': obj.id,
            'scientific_name': obj.scientific_name,
            'occurrences': obj.num_occurrences,
            'rank': obj.rank,
        } for obj in queryset]
    }


def organism(request, taxon_id):
    """
    The detail view for a single taxon.

    Response content is determined by the ``data`` GET parameter.

    * ``'time'`` : application/json
    * ``'tree'`` : application/json
    * ``'json'`` : application/json
    * else : text/html

    Parameters
    ----------
    request : :class:`django.http.request.HttpRequest`
    taxon_id : int
        Primary key for :class:`.Taxon` instance.

    Returns
    -------
    :class:`django.http.response.HttpResponse`
    """

    data = request.GET.get('data', None)
    start = int(request.GET.get('start', request.session.get('startYear', 1968)))
    end = int(request.GET.get('end', request.session.get('endYear', 2018)))
    depth = int(request.GET.get('depth', 2))

    cache_key = 'organism__%s__%s__%i_%i__%i' % (data, taxon_id,
                                                 start, end, depth)
    response_data = None#cache.get(cache_key)
    if data:
        content_type = 'application/json'
    else:
        content_type = "text/html; charset=utf-8"

    if response_data is not None:
        return HttpResponse(response_data, content_type)

    taxon = get_object_or_404(Taxon, pk=taxon_id)

    if data == 'time':      # Data about the occurrence of the taxon over time.
        response_data = json.dumps(_organism_time(taxon, start=1968, end=2018))
    elif data == 'tree':    # Local lineage data for the focal taxon.
        response_data = json.dumps(_organism_tree(taxon, depth=depth))
    elif data == 'json':    # Data about the documents where the taxon occurs.
        response_data = json.dumps(_organism_json(taxon, start=start, end=end))
    else:                   # Provides the templated detail view for this Taxon.
        template = loader.get_template('explorer/organism.html')
        context = RequestContext(request, {
            'taxon': taxon,
            'active': 'organisms',
            'resourcegroups': _organism_resources(taxon),
            'topics': _organism_topics(taxon)
        })
        response_data = template.render(context)

    cache.set(cache_key, response_data, 3600)
    return HttpResponse(response_data, content_type=content_type)


def organisms(request):
    """
    Displays the root view of the taxon browser.
    """

    data = request.GET.get('data', None)
    start = int(request.GET.get('start', request.session.get('startYear', 1975)))
    end = int(request.GET.get('end', request.session.get('endYear', 1990)))
    division = request.GET.get('division', None)

    if data is not None:
        if data == 'time':
            raw_data = _divisions_time(start=1968, end=2018)

        elif data == 'json':
            raw_data = _organisms_json(start=request.startYear, end=request.endYear, division=division)

        content_type = "application/json"
        response_data = json.dumps(raw_data)
    else:
        template = loader.get_template('explorer/organisms.html')
        context = RequestContext(request, {
            'divisions': Taxon.objects.all().values('division').distinct(),
            'active': 'organisms',
        })
        response_data = template.render(context)
        content_type = "text/html; charset=utf-8"

    return HttpResponse(response_data, content_type=content_type)
