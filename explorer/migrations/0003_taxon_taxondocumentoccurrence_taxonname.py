# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0002_topicfrequency_topicjointfrequency'),
    ]

    operations = [
        migrations.CreateModel(
            name='Taxon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('scientific_name', models.CharField(max_length=255)),
                ('rank', models.CharField(max_length=255, null=True, blank=True)),
                ('division', models.CharField(max_length=255, null=True, blank=True)),
                ('lineage', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='TaxonDocumentOccurrence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('document', models.ForeignKey(related_name='taxon_occurrences', to='explorer.Document')),
                ('taxon', models.ForeignKey(related_name='occurrences', to='explorer.Taxon')),
            ],
        ),
        migrations.CreateModel(
            name='TaxonName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name_type', models.CharField(max_length=255)),
                ('display_name', models.CharField(max_length=255)),
                ('name_for', models.ForeignKey(related_name='names', to='explorer.Taxon')),
            ],
        ),
    ]
