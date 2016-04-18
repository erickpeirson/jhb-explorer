# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0009_auto_20160417_1215'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='alternate_names',
            field=models.TextField(null=True, blank=True),
        ),
    ]
