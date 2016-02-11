from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from explorer.models import *
import os
import networkx as nx

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=str)

    def handle(self, *args, **options):
        datapath = os.path.join('explorer', 'fixtures', options['filename'][0])
        digraph = nx.read_graphml(datapath)
        for source_doi, target_doi in digraph.edges():

            source = Document.objects.get(doi=source_doi)
            target = Document.objects.get(doi=target_doi)
            source.cites.add(target)
            source.save()
            
