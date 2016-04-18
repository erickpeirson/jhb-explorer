from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Count

from explorer.models import *

import os
import csv
import networkx as nx
import json
import cPickle as pickle
import sys
from collections import defaultdict, Counter

from itertools import combinations


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('networkx_path', nargs=1, type=str)
        parser.add_argument('json_path', nargs=1, type=str)

    def handle(self, *args, **options):
        dates = range(1968, 2018)

        by_topic = {}
        for topic_id in Topic.objects.values_list('id', flat=True):
            queryset = TopicPageAssignment.objects.filter(topic_id=topic_id, weight__gte=5)
            date = 'page__belongs_to__publication_date'    # Yucky long field name.
            by_date = Counter(dict(queryset.values_list(date).annotate(Count(date))))

            # Adding 0 to a Counter initializes the corresponding key if there is no
            #  value. Turns out it also sorts the Counter by the order of assignment,
            #  so we get sorted values for free!
            for year in dates:
                by_date[year] += 0.
            by_topic[topic_id] = by_date

        # Now build JSON documents. Each document will represent the
        #  graph-state for a specific period (delimited by start and end).
        networkx_path = options.get('networkx_path')[0]
        json_path = options.get('json_path')[0]

        # The date range is inclusive of start, exclusive of end.
        for start, end in combinations(dates, 2):
            fname = 'topicgraph_%i_%i.graphml' % (start, end)
            fpath = os.path.join(networkx_path, fname)
            graph = nx.read_graphml(fpath)
            document = []

            def nonzero(d, s, e):
                for x in range(s, e):
                    if d[s] > 0:
                        return True
                return False

            nodes_present = set(graph.nodes()) & \
                            set([str(t) for t, counts in by_topic.iteritems()
                                 if any([counts[y] > 0 for y
                                         in xrange(start, end)])])

            # Each node represents a topic.
            for node, attrs in graph.nodes(data=True):
                if not node in nodes_present:
                    continue
                document.append({
                    "data": {
                        "id": str(node),
                        "label": None,
                        "weight": attrs['weight'],
                        "pos": {
                            "x": attrs['x'],
                            "y": attrs['y'],
                        },
                        # "terms": terms[int(node)],
                        # "documents": documents_by_range[int(node)][(start, end)],
                    }
                })

            # Each edge represents a colocation between topics on pages.
            for source, target, attrs in graph.edges(data=True):
                if not (source in nodes_present and target in nodes_present):
                    continue

                document.append({
                    "data": {
                        "source": str(source),
                        "target": str(target),
                        "weight": attrs['weight'],
                    }
                })

            jpath = os.path.join(json_path, 'topic_graph_%i_%i.json' % (start, end))
            with open(jpath, 'w') as f:
                json.dump(document, f)
            print '\r', fname,
