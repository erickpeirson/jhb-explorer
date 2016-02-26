# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0005_auto_20160226_0027'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxonexternalresource',
            name='link_name',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxonexternalresource',
            name='subject_type',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
