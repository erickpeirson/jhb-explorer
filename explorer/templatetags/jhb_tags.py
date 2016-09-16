from django import template
from django.contrib.staticfiles.templatetags.staticfiles import static

from explorer.models import *

import math
register = template.Library()


@register.filter
def format_taxon_name(taxon):
    orgString = ''
    if taxon.rank in ['species', 'genus', 'subgenus', None]:
        orgString += '<em>' + taxon.scientific_name + '</em>';
    else:
        orgString += taxon.scientific_name;
    return orgString


@register.filter
def permalink(doi):
    if doi.startswith('10.1007'):
        return u'http://link.springer.com/article/%s' % doi
    elif doi.startswith('10.2307'):
        return u'http://www.jstor.org/stable/%s' % doi


@register.filter
def taxonomy_permalink(taxon_id):
    return u'http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=%i' % taxon_id


@register.filter
def permalink_image(doi):
    if doi.startswith('10.1007'):
        return static('/static/explorer/images/springer_logo.png')
    elif doi.startswith('10.2307'):
        return static('/static/explorer/images/jstor_logo.jpg')


@register.filter
def plus_one(num):
    return int(num) + 1


@register.filter
def get_resource_icon(resource_type):
    icons = {
        ExternalResource.ISISCB: static('/static/explorer/images/IsisCB-80px.png'),
        ExternalResource.VIAF: static('/static/explorer/images/viaf.png'),
    }
    return icons.get(resource_type, None)


@register.filter
def get_resource_label(resource_type):
    types = {
        ExternalResource.ISISCB: 'IsisCB Explore',
        ExternalResource.VIAF: 'Virtual Internet Authority File',
    }
    return types.get(resource_type, None)


@register.filter
def get_absolute_url(model_name, instance_id):
    model_class = eval(model_name)
    return model_class.objects.get(pk=instance_id).get_absolute_url()
