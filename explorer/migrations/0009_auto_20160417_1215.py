# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0008_auto_20160412_1007'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorExternalResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('confidence', models.FloatField(default=1.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ('author', models.ForeignKey(related_name='resources', to='explorer.Author')),
                ('resource', models.ForeignKey(related_name='authors', to='explorer.ExternalResource')),
            ],
        ),
        migrations.CreateModel(
            name='DocumentLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('document', models.ForeignKey(related_name='locations', to='explorer.Document')),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=255)),
                ('latitude', models.FloatField(default=0.0)),
                ('longitude', models.FloatField(default=0.0)),
                ('uri', models.URLField(max_length=1000)),
            ],
        ),
        migrations.AddField(
            model_name='documentlocation',
            name='location',
            field=models.ForeignKey(related_name='documents', to='explorer.Location'),
        ),
    ]
