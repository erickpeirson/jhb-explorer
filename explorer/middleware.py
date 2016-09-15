class StartEndYearMiddleWare(object):
    """
    Ensures that date ranges used to select data are propagated consistently
    across views.
    """
    def process_request(self, request):
        startYear = request.GET.get('start', None)
        endYear = request.GET.get('end', None)
        if startYear is not None:
            request.session['startYear'] = startYear
        else:
            startYear = request.session.get('startYear', 1975)

        if endYear is not None:
            request.session['endYear'] = endYear
        else:
            endYear = request.session.get('endYear', 1990)
        request.startYear = startYear
        request.endYear = endYear
        return None
