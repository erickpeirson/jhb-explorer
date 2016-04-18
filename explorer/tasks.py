from __future__ import absolute_import

from django.conf import settings

from celery import shared_task
import urllib2
import json


@shared_task
def get_appellations_for_text(uri):
    request_url = '/'.join([settings.VOGONWEB, 'rest', 'appellation']) + '?format=json&text_uri=%s' % uri
    print request_url
    response = urllib2.urlopen(request_url)
    data = json.loads(response.read())

    return data


@shared_task
def process_appellations(appellations):
    for appellation in appellations:
        # do some stuff
        n 

def get_concept_by_id(id):
    request_url = '/'.join([settings.VOGONWEB, 'rest', 'concept', str(id)]) + '?format=json
