# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0006_auto_20160226_0028'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxon',
            name='part_of',
            field=models.ForeignKey(related_name='contains', to='explorer.Taxon', null=True),
        ),
    ]
