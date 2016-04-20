from django import forms

from haystack.forms import FacetedSearchForm
from haystack.query import SQ
from haystack.inputs import AutoQuery


class JHBSearchForm(FacetedSearchForm):
    """
    This is the main multi-content search form, used on the front (home) page
    and the main search view (/search/).
    """
    q = forms.CharField(max_length=255, required=False,
                        widget=forms.TextInput(attrs={
                            'class': 'form-control',
                            'autocomplete':"off",
                            'placeholder': 'What are you looking for?'
                        }))
