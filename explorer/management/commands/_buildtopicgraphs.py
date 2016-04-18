from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from explorer.models import *
import os
import csv
import igraph
import json
import cPickle as pickle
import sys

from itertools import combinations


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Load these just once.
        topics = [topic for topic in Topic.objects.all()]
        terms = {topic.id: [term for term in topic.assigned_to.order_by('-weight').select_related('term')[:20]] for topic in topics}
        # with open(os.path.join(settings.BASE_DIR, 'explorer', 'topic_graphs', 'layouts.pickle'), 'r') as f:
        #     layouts = pickle.load(f)
        for startYear, endYear in combinations(range(1968, 2014), 2):

            node_data = []
            edge_data = []

            print '\r', startYear, endYear,
            sys.stdout.flush()
            fname = 'topicgraph_%i_%i.pickle' % (startYear, endYear)
            fpath = os.path.join(settings.BASE_DIR, 'explorer', 'topic_graphs', fname)
            with open(fpath, 'r') as f:
                graph = igraph.load(f)

            fname_layout = 'layout_%i_%i.csv' % (startYear, endYear)
            fpath_layout = os.path.join(settings.BASE_DIR, 'explorer', 'topic_graphs', 'layouts', fname_layout)
            with open(fpath_layout, 'r') as f:
                reader = csv.reader(f)
                layout = {int(l[0]): [float(l[1]), float(l[2])] for l in reader}

            # layout = graph.layout_fruchterman_reingold(weights=graph.es['weight'])
            # bbox = igraph.BoundingBox(900.,900.)
            # layout.fit_into(bbox)

            for topic in topics:
                max_weight = max([term.weight for term in terms[topic.id]])
                min_weight = min([term.weight for term in terms[topic.id]])
                x, y = tuple(layout[topic.id])
                node_data.append({
                    'data': {
                        'label': topic.label,
                        'id': str(topic.id),
                        'pos': {
                            'x': x,
                            'y': y,
                            },
                        'weight': graph.vs['weight'][topic.id],
                        'terms': [
                            {
                                'id': assignment.term.id,
                                'term': assignment.term.term,
                                'weight': 8 + 10 * (assignment.weight - min_weight)/(max_weight - min_weight)
                            }
                            for assignment in terms[topic.id]
                        ],
                        'documents': [
                            {
                                'id': assignment.document.id,
                                'pubdate': assignment.document.publication_date,
                                'title': assignment.document.title
                            }
                            for assignment in topic.in_documents.filter(weight__gte=0.05,
                                                                        document__publication_date__gte=startYear,
                                                                        document__publication_date__lte=endYear).select_related('document')
                        ]
                    }
                })

            edges = [(e.tuple, e.attributes()['weight']) for e in graph.es]
            for edge, weight in edges:
                edge_data.append({
                    'data': {
                        'source': str(edge[0]),
                        'target': str(edge[1]),
                        'weight': weight,
                    }
                })
            fname_json = 'topic_graph_%i_%i.json' % (startYear, endYear)
            outpath = os.path.join(settings.BASE_DIR, 'explorer', 'static', 'explorer', 'data', fname_json)
            with open(outpath, 'w') as f:
                f.write(json.dumps(node_data + edge_data, indent=4))
