# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0010_location_alternate_names'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('author', models.ForeignKey(related_name='locations', to='explorer.Author')),
                ('document', models.ForeignKey(related_name='author_locations', to='explorer.Document')),
                ('location', models.ForeignKey(related_name='author_locations', to='explorer.Location')),
            ],
        ),
    ]
