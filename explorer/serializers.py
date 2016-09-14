from rest_framework import serializers

from explorer.models import *

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'label', 'description', 'prominence']
