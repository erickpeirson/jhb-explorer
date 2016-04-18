"""
Custom model managers.
"""

from django.db import models
import json


class DocumentQuerySet(models.QuerySet):
    def _to_feature(self, obj):
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [obj.get('locations__location__longitude'),
                                obj.get('locations__location__latitude')]
            },
            "properties": {
                "id": obj.get('locations__location__id'),
                "label": obj.get('locations__location__label'),
                "articles": [],
                "uri": obj.get('locations__location__uri'),
                "class": 'location',
            }
        }

    def geojson(self):
        """
        Generate a GeoJSON representation.
        """

        fields = [
            'locations__location__id',
            'locations__location__label',
            'locations__location__uri',
            'locations__location__longitude',
            'locations__location__latitude',
            'id',
        ]
        features = {}
        for result in self.values(*fields):
            if not result['locations__location__id']:
                continue
            location_id = result['locations__location__id']
            if location_id not in features:
                features[location_id] = self._to_feature(result)
            features[location_id]['properties']['articles'].append(result['id'])

        return  json.dumps({
            "type": "FeatureCollection",
            "features": features.values(),
        })


class DocumentManager(models.Manager):
    def get_queryset(self):
        return DocumentQuerySet(self.model, using=self._db)
