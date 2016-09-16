from django.core.management.base import BaseCommand
from django.conf import settings
from explorer.search_indexes import *

from elasticsearch_dsl.connections import connections
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Index


class Command(BaseCommand):
    def handle(self, *args, **options):
        connections.create_connection(hosts=[settings.ELASTICSEARCH_HOST])
        jhb_index = Index(settings.ELASTICSEARCH_INDEX)
        jhb_index.delete(ignore=404)

        client = Elasticsearch([settings.ELASTICSEARCH_HOST], port=settings.ELASTICSEARCH_PORT)
        client.indices.close(index=settings.ELASTICSEARCH_INDEX, ignore=404)
        SGeo.init()
        # client.indices.open(index=settings.ELASTICSEARCH_INDEX)
        for model, smodel, factory in indices:
            client.indices.close(index=settings.ELASTICSEARCH_INDEX)
            smodel.init()
            client.indices.open(index=settings.ELASTICSEARCH_INDEX)

            for i, instance in enumerate(model.objects.all()):
                print '\r', model.__name__, ':', i,
                sinstance = factory(instance)
