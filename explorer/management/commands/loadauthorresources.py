from django.core.management.base import BaseCommand

from explorer.models import Author, AuthorExternalResource, ExternalResource

import os
import csv


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=str)


    def handle(self, *args, **options):
        sources = {
            'viaf': ExternalResource.VIAF,
            'isiscb': ExternalResource.ISISCB,
        }
        locations = {
            'viaf': 'http://viaf.org/viaf/%s/',
            'isiscb': 'http://data.isiscb.org/isis/%s/',
        }
        filename = options.get('filename')[0]
        data_path = os.path.join('explorer', 'fixtures', filename)

        with open(data_path, 'rU') as f:
            reader = csv.reader(f)
            data = [line for line in reader][1:]

        for pk, name, identifier, source, confidence in data:
            if not source or not identifier:    # No data for this author.
                continue
            print pk, '|', name, '|', identifier, source, confidence


            location = locations[source.lower()] % identifier
            defaults = {
                'resource_type': sources[source.lower()],
                'resource_location': location,
            }
            resource,_ = ExternalResource.objects.get_or_create(resource_location=location, defaults=defaults)

            if confidence:
                confidence = float(confidence)
            else:
                confidence = 1.0

            AuthorExternalResource(
                author_id=pk,
                resource=resource,
                confidence=confidence
            ).save()
