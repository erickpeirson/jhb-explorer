from django import forms

# from haystack.forms import FacetedSearchForm
# from haystack.query import SQ
# from haystack.inputs import AutoQuery


class JHBSearchForm(forms.Form):
    """
    This is the main multi-content search form, used on the front (home) page
    and the main search view (/search/).
    """

    q = forms.CharField(max_length=255,
                        required=True,
                        widget=forms.TextInput(attrs={
                            'class': 'form-control',
                            'autocomplete':"off",
                            'placeholder': 'What are you looking for?'
                        }))

    def search(self):
        print 'q', self.cleaned_data.get('q')
        return super(JHBSearchForm, self).search()
