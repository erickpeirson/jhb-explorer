from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from explorer.models import *
import re
import os
import networkx as nx

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=str)

    def handle(self, *args, **options):
        datapath = os.path.join('explorer', 'fixtures', options['filename'][0])
        digraph = nx.read_graphml(datapath)

        def match_document(name):
            fullname, date = re.search('(\w+).+([0-9]{4})', name).groups()
            surname, date = name.split('_')[0], int(date)
            return Document.objects.filter(publication_date=date, authors__surname__icontains=surname)[0]

        for source_name, target_name in digraph.edges():

            # source_doi = match_document(source_name)[0].doi
            # target_doi = match_document(target_name)[0].doi
            try:
                source = match_document(source_name)# Document.objects.get(doi=source_doi)
                target = match_document(target_name)# Document.objects.get(doi=target_doi)
                source.cites.add(target)
                source.save()
            except IndexError:
                pass
