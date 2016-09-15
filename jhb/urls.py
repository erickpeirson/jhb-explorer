from django.conf.urls import include, url
from django.contrib import admin
from explorer.views.search import JHBSearchView, autocomplete
import explorer
from explorer.views import topics, organisms, documents, authors, locations
# from haystack.query import SearchQuerySet
#
# sqs = SearchQuerySet().facet('authors')

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', explorer.views.home, name='home'),
    url(r'^topics/$', topics.topics, name='topics'),
    url(r'^organisms/$', organisms.organisms, name='organisms'),
    url(r'^organisms/(?P<taxon_id>[0-9]+)/$', organisms.organism, name='organism_detail'),
    url(r'^topics/(?P<topic_id>[0-9]+)/$', topics.topic, name='topic_detail'),
    url(r'^documents/(?P<document_id>[0-9]+)/$', documents.document, name='document_detail'),
    url(r'^documents/(?P<document_doi>[0-9/\.]+/$)', documents.document_by_doi, name='document_by_doi'),
    url(r'^authors/(?P<author_id>[0-9]+)/$', authors.author, name='author_detail'),
    url(r'^locations/$', locations.locations, name='locations'),
    url(r'^locations/(?P<location_id>[0-9]+)/$', locations.location, name='location_detail'),
    url(r'^(?i)search/', JHBSearchView.as_view(), name='search'),
    url(r'^autocomplete/', autocomplete, name='autocomplete'),
    url(r'^about/$', explorer.views.about, name='about'),
    url(r'^methods/$', explorer.views.about, name='methods'),
]
