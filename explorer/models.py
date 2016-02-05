from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class JHBArticle(models.Model):  # Done
    """
    Represents an article in the Journal of the History of Biology.
    """

    title = models.CharField(max_length=1000)
    publication_date = models.IntegerField(default=0)

    doi = models.CharField(max_length=50)
    """Document Object Identifier."""

    volume = models.CharField(max_length=10)
    """Volume of JHB in which the article was published."""

    issue = models.CharField(max_length=10)
    """Issue (in ``volume``) of JHB in which the article was published."""

    cites = models.ManyToManyField('JHBArticle', related_name='cited_by')

    authors = models.ManyToManyField('Author', related_name='works')

    def __unicode__(self):
        return self.title

    @property
    def number_of_pages(self):
        return self.pages.count()


class Author(models.Model):
    """
    Represents an author of JHB articles.
    """

    surname = models.CharField(max_length=255)
    forename = models.CharField(max_length=255)

    def __unicode__(self):
        return u'%s, %s' % (self.surname.title(), self.forename.title())


class Page(models.Model):    # Done
    belongs_to = models.ForeignKey('JHBArticle', related_name='pages')
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
        return u'Topic %i' % self.id



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

    document = models.ForeignKey('JHBArticle', related_name='contains_topic')
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
    document = models.ForeignKey('JHBArticle', related_name='contains_terms')
    weight = models.IntegerField(default=0)


class ExternalResource(models.Model):
    """

    """
    resource_location = models.URLField(max_length=500)
    """The URL of the human-usable resource."""

    JSTOR = 'JS'
    ISISCB = 'IS'
    VIAF = 'VF'
    CONCEPTPOWER = 'CP'
    RESOURCE_TYPES = (
        (VIAF, 'Virtual Internet Authority File (VIAF)'),
        (CONCEPTPOWER, 'Conceptpower'),
        (JSTOR, 'JSTOR'),
        (ISISCB, 'IsisCB Explore'),
    )
    resource_type = models.CharField(max_length=255, choices=RESOURCE_TYPES)


class Entity(models.Model):
    """
    """
    label = models.CharField(max_length=500)
    entity_type = models.CharField(max_length=100)
