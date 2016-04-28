from django.conf import settings


def google_analytics_config(request):
    """
    Add Google analytics tracking config variables to the request context.
    """
    return {
        'google_analytics_id': settings.GOOGLE_ANALYTICS_ID,
    }
