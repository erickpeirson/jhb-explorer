from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.core.cache import caches
from django.template import RequestContext, loader

from django.http import HttpResponse
from django.conf import settings
from explorer.models import *
from explorer.search_indexes import *

# from explorer.forms import JHBSearchForm

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
import json
from collections import Counter


def search(request):
    """
    Handle search queries.
    """
    template = loader.get_template("search/search.html")
    query = request.GET.get("q", None)
    limit = request.GET.get("limit", settings.SEARCH_PAGE_SIZE)
    offset = request.GET.get("offset", 0)

    context = RequestContext(request, {'query': query, 'limit': limit, 'offset':offset})

    if query:
        client = Elasticsearch([settings.ELASTICSEARCH_HOST], port=settings.ELASTICSEARCH_PORT)
        q = Q("multi_match", query=query, boost=1, fields=['label', 'body', 'model']) | (Q("multi_match", query=query, fields=['label', 'body', 'model']) & Q("match", model={'query': 'Topic', 'boost': 2}))
        print q
        search = Search(index=settings.ELASTICSEARCH_INDEX, using=client)
        search = search.query(q)[offset:offset+limit]
        print search
        results = search.execute()
        context.update({'results': results})
    return HttpResponse(template.render(context))



# class JHBSearchView(FacetedSearchView):
#     facet_fields = ['authors', 'publication_date', 'result_type']
#     # queryset = SearchQuerySet()
#     results_per_page = 40
#     form_class = JHBSearchForm
#     template_name = "search/search.html"
#
#     def get_queryset(self):
#         queryset = super(FacetedSearchView, self).get_queryset()
#
#         # Haystack doesn't support range facets at the moment, so we need to do
#         #  this ourself.
#         start = self.request.GET.get('publication_date__start', None)
#         end = self.request.GET.get('publication_date__end', None)
#         if start:
#             queryset = queryset.exclude(publication_date__lt=start)
#         if end:
#             queryset = queryset.exclude(publication_date__gt=end)
#         return queryset
#
#     def form_invalid(self, form):
#         context = self.get_context_data(**{
#             self.form_name: form,
#             'object_list': [],
#         })
#         return self.render_to_response(context)
#
#     def get_context_data(self, *args, **kwargs):
#         cdata = super(FacetedSearchView, self).get_context_data(*args, **kwargs)
#         page = cdata['page_obj']
#         if len(cdata['object_list']) == 0:
#             return cdata
#
#         # If we don't strip the page number from the base URL for facet links,
#         #  we are likely to end up on non-existant pages. E.g. for a result-set
#         #  that spans two pages, if the user is on page 2 and selects an author
#         #  facet with only five results (less than a full page), they would end
#         #  up at ?page=2&selected_facet=key:value -> 404.
#         # For page links (e.g. next/previous), leaving the ``page`` parameter
#         #  means that we'll just keep appending additional ``page`` params to
#         #  the end of the URL. This wouldn't technically break anything (since
#         #  only the last value would be used), but it would be super tacky.
#         def pared_url(baseurl, params, exclude, **extra):
#             """
#             Parameters
#             ----------
#             baseurl : str
#             params : list
#                 List of key, value 2-tuples.
#             exclude : func
#                 Takes key, value, **extra; returns bool.
#             extra : kwargs
#                 Additional arguments that will be passed to ``exclude``.
#             """
#
#             return baseurl + u'?' + \
#                 '&'.join(['='.join([key, value])
#                           for key, value in params
#                           if not exclude(key, value, **extra)])
#
#         base = self.request.get_full_path().split('?')[0]
#         # We want to be able to consider each parameter independently, so we
#         #  flatten the query parameters into separate key, value 2-tuples.
#         base_params = [(key, value)
#                        for key, values
#                        in cdata['form'].data.lists()
#                        for value in values]
#         facet_base_url = pared_url(base, base_params,
#                                    lambda k, v, **e: k == 'page')
#
#         # We want to be able to show the user which facets they have selected,
#         #  and give them the option of removing that facet selection.
#         selected_facets = cdata['form'].data.getlist('selected_facets')
#         if len(selected_facets) > 0:
#             # Each facet selection needs a different "remove" URL -- this is
#             #  just the current URL less the current selected facet.
#             criterion = lambda k, v, **e: k == 'page' or v == e.get('facet')
#             facet_remove = [pared_url(base, base_params, criterion, facet=facet)
#                             for facet in selected_facets]
#
#             # We zip the type, value, and remove URL together for easy
#             #  iteration in the template.
#             facet_types, facet_values = zip(*[tuple(facet.split(':'))
#                                               for facet in selected_facets])
#
#             # Convert facet types to displayable labels.
#             pretty_types = {
#                 'result_type': 'Type',
#                 'authors': 'Author',
#             }
#             facet_types = [pretty_types.get(ft, ft) for ft in facet_types]
#             active_facets = zip(facet_types, facet_values, facet_remove)
#         else:
#             active_facets = None
#
#         # Haystack doesn't support range facets at the moment, so we need to do
#         #  this ourself. To build the range selection widget, we need to know
#         #  the min and max pubdates available in the result set.
#         publication_date = cdata['facets']['fields']['publication_date']
#         if len(publication_date) > 0:
#             years, yearcounts = zip(*sorted(publication_date, key=lambda d: d[0]))
#             years_base_url = pared_url(base, base_params,
#                                        lambda k, v, **e: k == 'page' or 'publication_date' in k)
#             cdata.update({
#                 'years_base_url': years_base_url,
#                 'minYear': min(years),
#                 'maxYear': max(years),
#             })
#
#         cdata.update({
#             'active': 'search',
#             'result_start': 1 + ((page.number - 1) * page.paginator.per_page),
#             'result_end': min((page.number) * page.paginator.per_page,
#                               page.paginator._count),
#             'result_total': page.paginator._count,
#             'page_previous': max(1, page.number - 1),
#             'page_current': page.number,
#             'page_next': min(page.paginator._num_pages, page.number + 1),
#             'page_last': page.paginator._num_pages,
#             'facet_base_url': facet_base_url,
#             'active_facets': active_facets,
#         })
#
#         return cdata


def suggest_topics(terms_raw, N=5):
    counts = Counter()
    for term_raw in terms_raw:
        qs = Term.objects.filter(term__icontains=term_raw)
        for tpk, weight in qs.values_list('topic_assignments__topic', 'topic_assignments__weight'):
            if tpk is None:
                continue
            counts[tpk] += weight if weight is not None else 1.
    if len(counts) > 0:
        return zip(*sorted(counts.items(), key=lambda o: o[1])[::-1][:N])[0]
    return []


def autocomplete(request):
    models = {
        'Topic': (Topic, 'label', 'icontains'),
        'Document': (Document, 'title', 'istartswith'),
        'Author': (Author, 'surname', 'istartswith'),
    }
    query = request.GET.get('q', '')
    model_name = request.GET.get('model', None)
    if not query:
        suggestions = []
    else:
        params = {'title': query}

    if model_name == 'Topic':
        pks = suggest_topics(query.split())
        qs = Topic.objects.filter(pk__in=pks)
        suggestions = list(qs.values('label', 'id')[:5])
    elif model_name is not None:
        model, field, lookup = models[model_name]
        qs = model.objects.filter(**{'%s__%s' % (field, lookup): query})
        suggestions = list(qs.values(field, 'id')[:5])
    else:
        suggestions = []
        for model, field, lookup in models.values():
            if model_name == 'Topic':
                pks = suggest_topics(query.split())
                qs = Topic.objects.filter(pk__in=pks)
                suggestions = list(qs.values('label', 'id')[:5])
            else:
                qs = model.objects.filter(**{'%s__%s' % (field, lookup): query})
                suggestions += list(qs.values(field, 'id', flat=True)[:5])

    data = {'results': suggestions}
    return HttpResponse(json.dumps(data), content_type='application/json')


# def autocomplete(request):
#     query = request.GET.get('q', '')
#     model = request.GET.get('model', None)
#     if not query:
#         suggestions = []
#     else:
#         params = {'title': query}
#         if model:
#             params.update({'result_type': model})
#         sqs = SearchQuerySet().autocomplete(**params)[:5]
#         suggestions = [result.title for result in sqs]
#
#     response_data = json.dumps({'results': suggestions})
#     return HttpResponse(response_data, content_type='application/json')
