from django.conf.urls import include, url
from django.contrib import admin
from explorer import views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', views.home, name='home'),
    url(r'^topics/$', views.topics, name='topics'),
    url(r'^organisms/$', views.organisms, name='organisms'),
    url(r'^organisms/(?P<taxon_id>[0-9]+)/$', views.organism, name='organism_detail'),
    url(r'^topics/(?P<topic_id>[0-9]+)/$', views.topic, name='topic_detail'),
    url(r'^documents/$', views.documents, name='documents'),
    url(r'^documents/(?P<document_id>[0-9]+)/$', views.document, name='document_detail'),
    url(r'^entities/$', views.entities, name='entities'),
    url(r'^entities/(?P<entity_id>[0-9]+)/$', views.entity, name='entity_detail'),
    url(r'^terms/$', views.terms, name='terms'),
    url(r'^terms/(?P<term_id>[0-9]+)/$', views.entity, name='term_detail'),
    url(r'^authors/$', views.authors, name='entities'),
    url(r'^authors/(?P<author_id>[0-9]+)/$', views.author, name='author_detail'),
]
