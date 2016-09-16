from django.conf import settings


def google_analytics_config(request):
    """
    Add Google analytics tracking config variables to the request context.
    """
    return {
        'google_analytics_id': settings.GOOGLE_ANALYTICS_ID,
    }


def timeline_dates(request):
    print 'asdf'*40
    # startYear = request.GET.get('start', None)
    # endYear = request.GET.get('end', None)
    # print 'timeline_dates', 'in request', startYear, endYear
    # if startYear is not None:
    #     request.session.set('startYear', startYear)
    # else:
    #     startYear = request.session.get('startYear', 1975)
    #
    # if endYear is not None:
    #     request.session.set('endYear', endYear)
    # else:
    #     endYear = request.session.get('endYear', 1990)
    #
    # print 'timeline_dates', 'in final context', startYear, endYear
    print '!!!', request.startYear
    return {
        'startYear': getattr(request, 'startYear') or 1975,
        'endYear': getattr(request, 'endYear') or 1990)
    }
