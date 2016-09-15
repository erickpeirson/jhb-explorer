from explorer.models import *
from elasticsearch_dsl import DocType, String, Date, Integer
import datetime

class SDocument(DocType):
    label = String(analyzer='snowball', fields={'raw': String(index='not_analyzed')})
    body = String(analyzer='snowball')
    authors = String(index='not_analyzed')
    topics = String(index='not_analyzed')
    model = String(index='not_analyzed')
    publication_date = Date()

    class Meta:
        index = 'jhb_index'


class STopic(DocType):
    label = String(analyzer='snowball', fields={'raw': String(index='not_analyzed')})
    body = String(analyzer='snowball')
    model = String(index='not_analyzed')
    documents = Integer(index='not_analyzed')

    class Meta:
        index = 'jhb_index'


class SAuthor(DocType):
    label = String(analyzer='snowball', fields={'raw': String(index='not_analyzed')})
    body = String(analyzer='snowball')
    model = String(index='not_analyzed')
    topics = Integer(index='not_analyzed')
    documents = Integer(index='not_analyzed')

    class Meta:
        index = 'jhb_index'


class STaxon(DocType):
    label = String(analyzer='snowball', fields={'raw': String(index='not_analyzed')})
    body = String(analyzer='snowball')
    model = String(index='not_analyzed')
    documents = Integer(index='not_analyzed')
    rank = String(index='not_analyzed')
    division = String(index='not_analyzed')

    class Meta:
        index = 'jhb_index'


class SLocation(DocType):
    label = String(analyzer='snowball', fields={'raw': String(index='not_analyzed')})
    body = String(analyzer='snowball')
    model = String(index='not_analyzed')
    documents = Integer(index='not_analyzed')

    class Meta:
        index = 'jhb_index'


def _document_from_model_instance(document):
    sdocument = SDocument(
        meta={'id': document.id},
        label=document.title,
        body=document.title,
        model='Document',
        publication_date=datetime.datetime(document.publication_date, 1, 1))
    sdocument.save()
    return sdocument


def _topic_from_model_instance(topic):
    stopic = STopic(
        meta={'id': topic.id},
        label=topic.label,
        body=topic.label,    # TODO: more terms?
        model='Topic',
        documents=list(topic.in_documents.filter(weight__gte=5).values_list('document__id', flat=True)),
    )
    stopic.save()
    return stopic


def _author_from_model_instance(author):
    sauthor = SAuthor(
        meta={'id': author.id},
        label='%s %s' % (author.forename, author.surname),
        documents=list(author.works.values_list('id', flat=True)),
        model='Author',
    )
    sauthor.body = u'\n'.join([
        '%s %s' % (author.forename, author.surname),    # Document info?
    ] + [document.title for document in author.works.all()])
    sauthor.save()
    return sauthor


def _taxon_from_model_instance(taxon):
    staxon = STaxon(
        meta={'id': taxon.id},
        label=taxon.scientific_name,
        model='Taxon',
        rank=taxon.rank,
        division=taxon.division,
        documents=list(taxon.occurrences.values_list('document__id', flat=True)),
    )
    staxon.body = u'\n'.join([
        taxon.scientific_name,
    ] + list(taxon.names.values_list('display_name', flat=True)))


indices = [
    (Document, SDocument, _document_from_model_instance),
    (Topic, STopic, _topic_from_model_instance),
    (Author, SAuthor, _author_from_model_instance),
    (Taxon, STaxon, _taxon_from_model_instance),

]
