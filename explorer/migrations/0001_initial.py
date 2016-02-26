# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('surname', models.CharField(max_length=255)),
                ('forename', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='BibliographicCoupling',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('weight', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
            ],
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=1000)),
                ('publication_date', models.IntegerField(default=0)),
                ('doi', models.CharField(max_length=50)),
                ('volume', models.CharField(max_length=10)),
                ('issue', models.CharField(max_length=10)),
                ('authors', models.ManyToManyField(related_name='works', to='explorer.Author')),
                ('cites', models.ManyToManyField(related_name='cited_by', to='explorer.Document')),
            ],
        ),
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=500)),
                ('entity_type', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='ExternalResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resource_location', models.URLField(max_length=500)),
                ('resource_type', models.CharField(max_length=255, choices=[(b'VF', b'Virtual Internet Authority File (VIAF)'), (b'CP', b'Conceptpower'), (b'JS', b'JSTOR'), (b'IS', b'IsisCB Explore')])),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('page_number', models.IntegerField(default=0)),
                ('belongs_to', models.ForeignKey(related_name='pages', to='explorer.Document')),
            ],
        ),
        migrations.CreateModel(
            name='Term',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='TermDocumentAssignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('weight', models.IntegerField(default=0)),
                ('document', models.ForeignKey(related_name='contains_terms', to='explorer.Document')),
                ('term', models.ForeignKey(related_name='occurs_in', to='explorer.Term')),
            ],
        ),
        migrations.CreateModel(
            name='TermPageAssignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('weight', models.IntegerField(default=0)),
                ('page', models.ForeignKey(related_name='contains_terms', to='explorer.Page')),
                ('term', models.ForeignKey(related_name='occurs_on', to='explorer.Term')),
            ],
        ),
        migrations.CreateModel(
            name='TermTopicAssignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('weight', models.FloatField(default=0.0)),
                ('term', models.ForeignKey(related_name='topic_assignments', to='explorer.Term')),
            ],
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=255, null=True, blank=True)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='TopicAssociation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('weight', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ('source', models.ForeignKey(related_name='associations_from', to='explorer.Topic')),
                ('target', models.ForeignKey(related_name='associations_to', to='explorer.Topic')),
            ],
        ),
        migrations.CreateModel(
            name='TopicCoLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('weight', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ('pages', models.ManyToManyField(related_name='jointly_contains', to='explorer.Page')),
                ('source', models.ForeignKey(related_name='colocates_from', to='explorer.Topic')),
                ('target', models.ForeignKey(related_name='colocates_to', to='explorer.Topic')),
            ],
        ),
        migrations.CreateModel(
            name='TopicDocumentAssignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('weight', models.FloatField(default=0.0)),
                ('document', models.ForeignKey(related_name='contains_topic', to='explorer.Document')),
                ('topic', models.ForeignKey(related_name='in_documents', to='explorer.Topic')),
            ],
        ),
        migrations.CreateModel(
            name='TopicPageAssignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('weight', models.FloatField(default=0.0)),
                ('page', models.ForeignKey(related_name='contains_topic', to='explorer.Page')),
                ('topic', models.ForeignKey(related_name='on_pages', to='explorer.Topic')),
            ],
        ),
        migrations.AddField(
            model_name='topic',
            name='associated_with',
            field=models.ManyToManyField(related_name='associates', through='explorer.TopicAssociation', to='explorer.Topic'),
        ),
        migrations.AddField(
            model_name='topic',
            name='colocated_with',
            field=models.ManyToManyField(related_name='colocates', through='explorer.TopicCoLocation', to='explorer.Topic'),
        ),
        migrations.AddField(
            model_name='termtopicassignment',
            name='topic',
            field=models.ForeignKey(related_name='assigned_to', to='explorer.Topic'),
        ),
        migrations.AddField(
            model_name='bibliographiccoupling',
            name='source',
            field=models.ForeignKey(related_name='couplings_from', to='explorer.Document'),
        ),
        migrations.AddField(
            model_name='bibliographiccoupling',
            name='target',
            field=models.ForeignKey(related_name='couplings_to', to='explorer.Document'),
        ),
    ]
