from django.contrib import admin
from models import *

class TopicCoLocationAdmin(admin.ModelAdmin):
    model = TopicCoLocation

    readonly_fields = ('pages',)

class TopicPageAssignmentAdmin(admin.ModelAdmin):
    model = TopicPageAssignment

    readonly_fields = ('page', 'topic')


class AuthorAdmin(admin.ModelAdmin):
    model = Author
    list_display = ('id', 'surname', 'forename',)
    search_fields = ('surname', 'forename')


admin.site.register(Document)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Page)
admin.site.register(Taxon)
admin.site.register(TaxonName)
admin.site.register(TaxonDocumentOccurrence)
admin.site.register(TaxonExternalResource)
admin.site.register(Topic)
admin.site.register(TopicAssociation)
admin.site.register(TopicPageAssignment, TopicPageAssignmentAdmin)
admin.site.register(TopicCoLocation, TopicCoLocationAdmin)

admin.site.register(ExternalResource)
