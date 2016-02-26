# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0003_taxon_taxondocumentoccurrence_taxonname'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxondocumentoccurrence',
            name='weight',
            field=models.FloatField(default=1.0),
        ),
    ]
