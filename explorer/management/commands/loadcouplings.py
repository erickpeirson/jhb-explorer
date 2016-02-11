from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from explorer.models import Document, BibliographicCoupling
import os
import networkx as nx

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=str)

    def handle(self, *args, **options):
        datapath = os.path.join('explorer', 'fixtures', options['filename'][0])
        graph = nx.read_graphml(datapath)
        for source_doi, target_doi, attrs in graph.edges(data=True):
            try:
                source = Document.objects.get(doi=source_doi)
                target = Document.objects.get(doi=target_doi)
            except Document.DoesNotExist:
                continue

            BibliographicCoupling(
                source=source,
                target=target,
                weight=attrs['weight']).save()
