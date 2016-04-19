from haystack import indexes
from explorer.models import *


class DocumentIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    title = indexes.EdgeNgramField(model_attr='title')
    result_type = indexes.FacetCharField()
    authors = indexes.FacetMultiValueField()
    topics = indexes.FacetMultiValueField()
    publication_date = indexes.FacetIntegerField(model_attr='publication_date')

    def prepare_authors(self, instance):
        return [', '.join([author.surname, author.forename]).title()
                for author in instance.authors.all()]

    def prepare_topics(self, instance):
        return []

    def prepare_result_type(self, instance):
        return instance.__class__.__name__

    def get_model(self):
        return Document


class TopicIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    title = indexes.EdgeNgramField()
    result_type = indexes.FacetCharField()

    def prepare_title(self, instance):
        """
        race races human racial hunt
        """
        return instance.__unicode__()

    def prepare_result_type(self, instance):
        return instance.__class__.__name__

    def get_model(self):
        return Topic


class AuthorIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True)
    title = indexes.EdgeNgramField()
    result_type = indexes.FacetCharField()

    def prepare(self, instance):
        data = super(AuthorIndex, self).prepare(instance)
        data['boost'] = 2
        return data

    def prepare_text(self, instance):
        document = u' '.join([instance.forename, instance.surname])
        document += u'\n' + u'\n'.join([title for title in instance.works.all().values_list('title', flat=True)])

        return document.lower()

    def prepare_result_type(self, instance):
        return instance.__class__.__name__

    def prepare_title(self, instance):
        """
        Forename M Surname.
        """
        return u' '.join([instance.forename, instance.surname]).title()

    def get_model(self):
        return Author


class TaxonIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True)
    title = indexes.EdgeNgramField()
    result_type = indexes.FacetCharField()

    def prepare_result_type(self, instance):
        return instance.__class__.__name__

    def prepare_text(self, instance):
        document = instance.scientific_name
        document += u'\n' + u'\n'.join([name.display_name for name in instance.names.all()])
        return document

    def prepare_title(self, instance):
        """
        Agrostis tenuis
        """
        return instance.scientific_name

    def get_model(self):
        return Taxon


class LocationIndex(indexes.SearchIndex, indexes.Indexable):
    """
    Index :class:`.Location`\s by name.
    """
    text = indexes.EdgeNgramField(document=True)
    title = indexes.EdgeNgramField()
    result_type = indexes.FacetCharField()

    def prepare_result_type(self, instance):
        return instance.__class__.__name__

    def prepare_text(self, instance):
        return instance.label + u'\n' + instance.alternate_names

    def prepare_title(self, instance):
        """
        Hellenic Republic
        """
        return instance.label

    def get_model(self):
        return Location
