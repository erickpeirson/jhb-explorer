from django.conf.urls import include, url
from django.contrib import admin
from explorer.views.search import JHBSearchView, autocomplete

# from haystack.query import SearchQuerySet
#
# sqs = SearchQuerySet().facet('authors')

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'explorer.views.home', name='home'),
    url(r'^topics/$', 'explorer.views.topics.topics', name='topics'),
    url(r'^organisms/$', 'explorer.views.organisms.organisms', name='organisms'),
    url(r'^organisms/(?P<taxon_id>[0-9]+)/$', 'explorer.views.organisms.organism', name='organism_detail'),
    url(r'^topics/(?P<topic_id>[0-9]+)/$', 'explorer.views.topics.topic', name='topic_detail'),
    url(r'^documents/(?P<document_id>[0-9]+)/$', 'explorer.views.documents.document', name='document_detail'),
    url(r'^documents/(?P<document_doi>[0-9/\.]+/$)', 'explorer.views.documents.document_by_doi', name='document_by_doi'),
    url(r'^authors/(?P<author_id>[0-9]+)/$', 'explorer.views.authors.author', name='author_detail'),
    url(r'^locations/$', 'explorer.views.locations.locations', name='locations'),
    url(r'^locations/(?P<location_id>[0-9]+)/$', 'explorer.views.locations.location', name='location_detail'),
    url(r'^(?i)search/', JHBSearchView.as_view(), name='search'),
    url(r'^autocomplete/', autocomplete, name='autocomplete')
]
