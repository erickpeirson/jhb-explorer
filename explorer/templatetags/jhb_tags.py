from django import template

import math
register = template.Library()


@register.filter
def format_taxon_name(taxon):
    orgString = ''
    if taxon.rank in ['species', 'genus', 'subgenus', None]:
        orgString += '<em>' + taxon.scientific_name + '</em>';
    else:
        orgString += taxon.scientific_name;

    if taxon.rank:
         orgString += ' <span class="label label-default">' + taxon.rank + '</span>';
    return orgString
