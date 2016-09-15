from django.core.management.base import BaseCommand

from explorer.search_indexes import *

from elasticsearch_dsl.connections import connections
import sys


class Command(BaseCommand):
    def handle(self, *args, **options):
        connections.create_connection(hosts=['localhost'])
        print(connections.get_connection().cluster.health())

        for model, smodel, factory in indices:
            for i, instance in enumerate(model.objects.all()):
                print '\r', model.__name__, ':', i,
                sinstance = factory(instance)
