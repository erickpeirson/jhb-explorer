from django import template
from django.contrib.staticfiles.templatetags.staticfiles import static

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
