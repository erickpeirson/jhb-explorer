# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0007_taxon_part_of'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='issue',
            field=models.CharField(max_length=10, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='document',
            name='volume',
            field=models.CharField(max_length=10, null=True, blank=True),
        ),
    ]
