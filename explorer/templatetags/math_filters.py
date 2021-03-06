from django import template

import math
register = template.Library()


@register.filter
def multiply(x, y):
    return (1.*x)*y


@register.filter
def weight_to_fontsize(weight):
    return max(2, 4*weight)

@register.filter
def round_weight(weight):
    return round(weight, 4)


@register.filter
def round_representation(weight):
    return int(round(weight, 0))
