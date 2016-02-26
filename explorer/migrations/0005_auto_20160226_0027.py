# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0004_taxondocumentoccurrence_weight'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxonExternalResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(max_length=1000)),
                ('link_name', models.CharField(max_length=255)),
                ('subject_type', models.CharField(max_length=255)),
                ('category', models.CharField(max_length=255)),
                ('attribute', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='TaxonResourceProvider',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('abbreviation', models.CharField(max_length=255)),
                ('url', models.URLField(max_length=1000)),
            ],
        ),
        migrations.AlterField(
            model_name='externalresource',
            name='resource_type',
            field=models.CharField(max_length=255, choices=[(b'VF', b'Virtual Internet Authority File (VIAF)'), (b'CP', b'Conceptpower'), (b'JS', b'JSTOR'), (b'IS', b'IsisCB Explore'), (b'TX', b'NCBI Taxonomy Database')]),
        ),
        migrations.AddField(
            model_name='taxonexternalresource',
            name='provider',
            field=models.ForeignKey(related_name='resources', to='explorer.TaxonResourceProvider'),
        ),
        migrations.AddField(
            model_name='taxonexternalresource',
            name='taxon',
            field=models.ForeignKey(related_name='resources', to='explorer.Taxon'),
        ),
    ]
