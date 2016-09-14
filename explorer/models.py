from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.urlresolvers import reverse

from explorer import managers

import json



class Document(models.Model):  # Done
    """
    Represents an article in the Journal of the History of Biology.
    """

    title = models.CharField(max_length=1000)
    publication_date = models.IntegerField(default=0)

    doi = models.CharField(max_length=50)
    """Document Object Identifier."""

    volume = models.CharField(max_length=10, null=True, blank=True)
    """Volume of JHB in which the article was published."""

    issue = models.CharField(max_length=10, null=True, blank=True)
    """Issue (in ``volume``) of JHB in which the article was published."""

    cites = models.ManyToManyField('Document', related_name='cited_by')

    authors = models.ManyToManyField('Author', related_name='works')

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('document_detail', args=(self.id,))

    @property
    def number_of_pages(self):
        return self.pages.count()

    @property
    def top_topics(self):
        return self.contains_topic.filter(weight__gte=5).order_by('-weight')[:10]

    objects = managers.DocumentManager()


class Author(models.Model):
    """
    Represents an author of a Document.
    """

    surname = models.CharField(max_length=255)
    forename = models.CharField(max_length=255)

    def __unicode__(self):
        return u'%s, %s' % (self.surname.title(), self.forename.title())

    def get_absolute_url(self):
        return reverse('author_detail', args=(self.id,))


class Page(models.Model):    # Done
    """
    Represents a single page in a :class:`.Document`\.

    The topic model was fit to the corpus using individual pages as separate
    documents. We don't provide a separate view for pages, but still need to
    represent them in the database.
    """
    belongs_to = models.ForeignKey('Document', related_name='pages')
    page_number = models.IntegerField(default=0)

    def __unicode__(self):
        return u'Page %i of %s' % (self.page_number, self.belongs_to.title)


class Topic(models.Model):   # Done
    """
    Represents a topic in the LDA topic model.
    """

    label = models.CharField(max_length=255, blank=True, null=True)
    """A brief label, provided by domain experts."""

    description = models.TextField()
    """Additional information about the topic."""


    associated_with = models.ManyToManyField('Topic',
                                             through='TopicAssociation',
                                             through_fields=('source',
                                                             'target'),
                                             related_name='associates')

    colocated_with = models.ManyToManyField('Topic',
                                            through='TopicCoLocation',
                                            through_fields=('source',
                                                            'target'),
                                            related_name='colocates')

    def __unicode__(self):
        if self.label:
            return self.label
        terms = self.assigned_to.order_by('-weight')\
                                .values_list('term__term', flat=True)[:5]
        return u' '.join(terms)

    def get_absolute_url(self):
        return reverse('topic_detail', args=(self.id,))

    @property
    def for_display(self):
        if self.label:
            return self.label
        terms = self.assigned_to.order_by('-weight')\
                                .values_list('term__term', flat=True)[:5]
        return u', '.join(terms)

    @property
    def top_term_assignments(self):
        return self.assigned_to.order_by('-weight')[:100]

    @property
    def prominence(self):
        """
        This should be replaced with something more interesting.
        """
        return 1.*self.on_pages.count()



class TopicAssociation(models.Model):
    """
    Represents an association or similarity between two topics, on the basis
    of their constituent terms.
    """

    source = models.ForeignKey(Topic,
                               on_delete=models.CASCADE,
                               related_name='associations_from')
    target = models.ForeignKey(Topic,
                               on_delete=models.CASCADE,
                               related_name='associations_to')

    weight = models.FloatField(default=0.0,
                               validators=[MinValueValidator(0.0),
                                           MaxValueValidator(1.0)])
    """
    Relative strength of the association.
    """


class TopicCoLocation(models.Model):
    """
    Represents an association or similarity between two topics, on the basis
    of colocation in documents.
    """

    source = models.ForeignKey(Topic,
                               on_delete=models.CASCADE,
                               related_name='colocates_from')
    target = models.ForeignKey(Topic,
                               on_delete=models.CASCADE,
                               related_name='colocates_to')

    weight = models.FloatField(default=0.0,
                               validators=[MinValueValidator(0.0),
                                           MaxValueValidator(1.0)])
    """
    Relative strength of the association.
    """

    pages = models.ManyToManyField('Page',
                                   related_name='jointly_contains')
    """
    Documents in which the constituent topics are colocated.
    """

    def __unicode__(self):
        return u'Colocation of %s and %s' % (self.source.__unicode__(), self.target.__unicode__())


class TopicPageAssignment(models.Model):     # Done
    """
    Represents the association between a page and a topic.
    """

    page = models.ForeignKey('Page', related_name='contains_topic')
    """The page to which ``topic`` is assigned."""

    topic = models.ForeignKey('Topic', related_name='on_pages')
    weight = models.FloatField(default=0.0)


class TopicDocumentAssignment(models.Model):     # Done
    """
    Represents the association between a document and a topic.
    """

    document = models.ForeignKey('Document', related_name='contains_topic')
    """The document to which ``topic`` is assigned."""

    topic = models.ForeignKey('Topic', related_name='in_documents')
    weight = models.FloatField(default=0.0)

    # @property
    def weight_normed(self):
        return self.weight / self.document.number_of_pages


class Term(models.Model):    # Done
    """
    Represents a term (e.g. a word) in the corpus vocabulary.
    """

    term = models.CharField(max_length=255)
    """
    The term itself.
    """


class TermTopicAssignment(models.Model):
    term = models.ForeignKey('Term', related_name='topic_assignments')
    topic = models.ForeignKey('Topic', related_name='assigned_to')
    weight = models.FloatField(default=0.0)


class TermPageAssignment(models.Model):     # Done
    term = models.ForeignKey('Term', related_name='occurs_on')
    page = models.ForeignKey('Page', related_name='contains_terms')
    weight = models.IntegerField(default=0)


class TermDocumentAssignment(models.Model):  # Done
    term = models.ForeignKey('Term', related_name='occurs_in')
    document = models.ForeignKey('Document', related_name='contains_terms')
    weight = models.IntegerField(default=0)


class AuthorExternalResource(models.Model):
    author = models.ForeignKey('Author', related_name='resources')
    resource = models.ForeignKey('ExternalResource', related_name='authors')
    confidence = models.FloatField(default=1.0,
                                   validators=[MinValueValidator(0.0),
                                               MaxValueValidator(1.0)])


class ExternalResource(models.Model):
    """
    """

    resource_location = models.URLField(max_length=500)
    """The URL of the human-usable resource."""

    JSTOR = 'JS'
    ISISCB = 'IS'
    VIAF = 'VF'
    TAXONOMY = 'TX'
    CONCEPTPOWER = 'CP'
    RESOURCE_TYPES = (
        (VIAF, 'Virtual Internet Authority File (VIAF)'),
        (CONCEPTPOWER, 'Conceptpower'),
        (JSTOR, 'JSTOR'),
        (ISISCB, 'IsisCB Explore'),
        (TAXONOMY, 'NCBI Taxonomy Database'),
    )
    resource_type = models.CharField(max_length=255, choices=RESOURCE_TYPES)


class Location(models.Model):
    """
    A geographic location.
    """

    label = models.CharField(max_length=255)
    alternate_names = models.TextField(blank=True, null=True)

    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    uri = models.URLField(max_length=1000)
    """E.g. GeoNames URI."""

    def __unicode__(self):
        return self.label

    def get_absolute_url(self):
        return reverse('location_detail', args=(self.id,))

    @property
    def articles(self):
        """
        All of the articles associated with this location.
        """
        return self.documents.document.values_list('id', flat=True)

    def geojson(self):
        """
        """
        return json.dumps({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "label": self.label,
                "articles": self.articles,
                "uri": self.uri,
                "class": 'location',
            }
        })


class DocumentLocation(models.Model):
    """
    Captures a thematic (content) relation between a :class:`.Document` and a
    :clas:`.Location`
    """
    document = models.ForeignKey('Document', related_name='locations')
    location = models.ForeignKey('Location', related_name='documents')


class AuthorLocation(models.Model):
    """
    Captures the :class:`.Location` of an :class:`.Author` at the time of
    publication of a :class:`.Document`\.
    """
    document = models.ForeignKey('Document', related_name='author_locations')
    author = models.ForeignKey('Author', related_name='locations')
    location = models.ForeignKey('Location', related_name='author_locations')


class Entity(models.Model):
    """
    """
    label = models.CharField(max_length=500)
    entity_type = models.CharField(max_length=100)


class BibliographicCoupling(models.Model):
    """
    Represents the fact that the references of two :class:`.Document`\s are
    overlapping.

    This is a symmetric relation, but we use ``source`` and ``target`` to keep
    Django happy.
    """

    source = models.ForeignKey('Document', related_name='couplings_from')
    target = models.ForeignKey('Document', related_name='couplings_to')
    weight = models.FloatField(default=0.0,
                               validators=[MinValueValidator(0.0),
                                           MaxValueValidator(1.0)])
    """
    Mean percent overlap of the two bibliographies.
    """


class TopicFrequency(models.Model):
    """
    Pre-calculated per-page frequency for topics on an annual basis.
    """

    topic = models.ForeignKey('Topic', related_name='frequencies')
    frequency = models.FloatField(default=0.0)
    year = models.PositiveIntegerField(default=1900)


class TopicJointFrequency(models.Model):
    """
    Pre-calculated per-page joint frequency for pairs of topics on an annual
    basis.
    """

    topics = models.ManyToManyField('Topic', related_name='joint_frequencies')
    frequency = models.FloatField(default=0.0)
    year = models.PositiveIntegerField(default=1900)


class TaxonName(models.Model):
    name_for = models.ForeignKey('Taxon', related_name='names')
    name_type = models.CharField(max_length=255)
    """e.g. Authority"""
    display_name = models.CharField(max_length=255)
    """e.g. Western red cedar"""


class Taxon(models.Model):
    scientific_name = models.CharField(max_length=255)
    rank = models.CharField(max_length=255, blank=True, null=True)
    division = models.CharField(max_length=255, blank=True, null=True)
    """
    e.g. Plants, Animals, Viruses.
    """

    part_of = models.ForeignKey('Taxon', related_name='contains', null=True)

    lineage = models.TextField(blank=True)

    def get_absolute_url(self):
        return reverse('organism_detail', args=(self.id,))

    def get_lineage(self):
        try:
            return [Taxon.objects.get(pk=pk) for pk in json.loads(self.lineage)]
        except ValueError:
            return []

    def set_lineage(self, value):
        if type(value) is not list:
            raise ValueError('value of lineage must be a list of Taxon IDs')
        self.lineage = json.dumps(value)

    def children(self):
        def traverse_down(taxon):
            result = [taxon]
            if taxon.contains.count() > 0:
                for tax in taxon.contains.all():
                    result += traverse_down(tax)
            return result
        return traverse_down(self)

    def parents(self):
        def traverse_up(taxon):
            result = [taxon]
            if taxon.part_of:
                return result + traverse_up(taxon.part_of)
            return result
        return traverse_up(self)

    def tree(self, depth_up=2, depth_down=None):
        def traverse_up(taxon, level):
            result = [taxon]
            if taxon.contains.count() < 2:
                level -= 1
            if level < depth_up and taxon.part_of:
                result += traverse_up(taxon.part_of, level + 1)
            return result

        def traverse_down(taxon, level):
            as_leaf = {"id": taxon.id, "scientific_name": taxon.scientific_name, "rank": taxon.rank, "count": taxon.occurrences.count() }
            if level < depth_down or depth_down is None:
                results = [traverse_down(ctaxon, level + 1) for ctaxon in taxon.contains.all()]
                if len(results) == 1:
                    as_leaf = results[0]
                elif len(results) > 0:
                    as_leaf["children"] = results
            return as_leaf
        return [traverse_down(traverse_up(self, 0)[::-1][0], 0)]


class TaxonDocumentOccurrence(models.Model):
    taxon = models.ForeignKey('Taxon', related_name='occurrences')
    document = models.ForeignKey('Document', related_name='taxon_occurrences')
    weight = models.FloatField(default=1.)


class TaxonResourceProvider(models.Model):
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)
    url = models.URLField(max_length=1000)


class TaxonExternalResource(models.Model):
    """
    Represents LinkOut resources from the NCBI Taxonomy database.
    """
    taxon = models.ForeignKey('Taxon', related_name='resources')

    url = models.URLField(max_length=1000)
    link_name = models.CharField(max_length=255, null=True, blank=True)
    subject_type = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=255)
    attribute = models.CharField(max_length=255)
    provider = models.ForeignKey('TaxonResourceProvider', related_name='resources')


# class EntityOccurrence(models.Model):
#     entity = models.ForeignKey('Entity', related_name='occurrences')
#     page = models.ForeignKey('Page', related_name='entities')
#     weight = models.FloatField(default=0.0)
#     """
#     Frequency of entity occurrences on the Page.
#     """
