from django.http import HttpResponse

from explorer.forms import JHBSearchForm

from haystack.generic_views import FacetedSearchView
from haystack.query import SearchQuerySet

import json


class JHBSearchView(FacetedSearchView):
    facet_fields = ['authors', 'publication_date', 'result_type']
    queryset = SearchQuerySet()
    results_per_page = 40
    form_class = JHBSearchForm
    template_name = "search/search.html"

    def get_queryset(self):
        queryset = super(FacetedSearchView, self).get_queryset()

        # Haystack doesn't support range facets at the moment, so we need to do
        #  this ourself.
        start = self.request.GET.get('publication_date__start', None)
        end = self.request.GET.get('publication_date__end', None)
        if start:
            queryset = queryset.exclude(publication_date__lt=start)
        if end:
            queryset = queryset.exclude(publication_date__gt=end)
        return queryset

    def get_context_data(self, *args, **kwargs):
        cdata = super(FacetedSearchView, self).get_context_data(*args, **kwargs)
        page = cdata['page_obj']

        # If we don't strip the page number from the base URL for facet links,
        #  we are likely to end up on non-existant pages. E.g. for a result-set
        #  that spans two pages, if the user is on page 2 and selects an author
        #  facet with only five results (less than a full page), they would end
        #  up at ?page=2&selected_facet=key:value -> 404.
        # For page links (e.g. next/previous), leaving the ``page`` parameter
        #  means that we'll just keep appending additional ``page`` params to
        #  the end of the URL. This wouldn't technically break anything (since
        #  only the last value would be used), but it would be super tacky.
        def pared_url(baseurl, params, exclude, **extra):
            """
            Parameters
            ----------
            baseurl : str
            params : list
                List of key, value 2-tuples.
            exclude : func
                Takes key, value, **extra; returns bool.
            extra : kwargs
                Additional arguments that will be passed to ``exclude``.
            """

            return baseurl + u'?' + \
                '&'.join(['='.join([key, value])
                          for key, value in params
                          if not exclude(key, value, **extra)])

        base = self.request.get_full_path().split('?')[0]
        # We want to be able to consider each parameter independently, so we
        #  flatten the query parameters into separate key, value 2-tuples.
        base_params = [(key, value)
                       for key, values
                       in cdata['form'].data.lists()
                       for value in values]
        facet_base_url = pared_url(base, base_params,
                                   lambda k, v, **e: k == 'page')

        # We want to be able to show the user which facets they have selected,
        #  and give them the option of removing that facet selection.
        selected_facets = cdata['form'].data.getlist('selected_facets')
        if len(selected_facets) > 0:
            # Each facet selection needs a different "remove" URL -- this is
            #  just the current URL less the current selected facet.
            criterion = lambda k, v, **e: k == 'page' or v == e.get('facet')
            facet_remove = [pared_url(base, base_params, criterion, facet=facet)
                            for facet in selected_facets]

            # We zip the type, value, and remove URL together for easy
            #  iteration in the template.
            facet_types, facet_values = zip(*[tuple(facet.split(':'))
                                              for facet in selected_facets])

            # Convert facet types to displayable labels.
            pretty_types = {
                'result_type': 'Type',
                'authors': 'Author',
            }
            facet_types = [pretty_types.get(ft, ft) for ft in facet_types]
            active_facets = zip(facet_types, facet_values, facet_remove)
        else:
            active_facets = None

        # Haystack doesn't support range facets at the moment, so we need to do
        #  this ourself. To build the range selection widget, we need to know
        #  the min and max pubdates available in the result set.
        years, yearcounts = zip(*sorted(cdata['facets']['fields']['publication_date'], key=lambda d: d[0]))
        years_base_url = pared_url(base, base_params,
                                   lambda k, v, **e: k == 'page' or 'publication_date' in k)

        cdata.update({
            'active': 'search',
            'result_start': 1 + ((page.number - 1) * page.paginator.per_page),
            'result_end': min((page.number) * page.paginator.per_page,
                              page.paginator._count),
            'result_total': page.paginator._count,
            'page_previous': max(1, page.number - 1),
            'page_current': page.number,
            'page_next': min(page.paginator._num_pages, page.number + 1),
            'page_last': page.paginator._num_pages,
            'facet_base_url': facet_base_url,
            'years_base_url': years_base_url,
            'active_facets': active_facets,

            'minYear': min(years),
            'maxYear': max(years),
        })

        return cdata


def autocomplete(request):
    query = request.GET.get('q', '')
    if not query:
        suggestions = []
    else:
        sqs = SearchQuerySet().autocomplete(title=query)[:5]
        suggestions = [result.title for result in sqs]

    response_data = json.dumps({'results': suggestions})
    return HttpResponse(response_data, content_type='application/json')
