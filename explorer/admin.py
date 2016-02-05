from django.contrib import admin
from models import *

class TopicCoLocationAdmin(admin.ModelAdmin):
    model = TopicCoLocation

    readonly_fields = ('pages',)

class TopicPageAssignmentAdmin(admin.ModelAdmin):
    model = TopicPageAssignment

    readonly_fields = ('page', 'topic')

admin.site.register(JHBArticle)
admin.site.register(Author)
admin.site.register(Page)
admin.site.register(Topic)
admin.site.register(TopicAssociation)
admin.site.register(TopicPageAssignment, TopicPageAssignmentAdmin)
admin.site.register(TopicCoLocation, TopicCoLocationAdmin)

admin.site.register(ExternalResource)
