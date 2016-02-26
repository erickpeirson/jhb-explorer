# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TopicFrequency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('frequency', models.FloatField(default=0.0)),
                ('year', models.PositiveIntegerField(default=1900)),
                ('topic', models.ForeignKey(related_name='frequencies', to='explorer.Topic')),
            ],
        ),
        migrations.CreateModel(
            name='TopicJointFrequency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('frequency', models.FloatField(default=0.0)),
                ('year', models.PositiveIntegerField(default=1900)),
                ('topics', models.ManyToManyField(related_name='joint_frequencies', to='explorer.Topic')),
            ],
        ),
    ]
