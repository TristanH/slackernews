# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('posted_stories_raw', models.TextField(default=b'{}')),
                ('webhook_url', models.CharField(unique=True, max_length=256)),
                ('access_token', models.CharField(unique=True, max_length=256)),
                ('team_name', models.CharField(max_length=256)),
                ('channel_name', models.CharField(max_length=256)),
                ('config_url', models.CharField(max_length=256)),
                ('phrases_raw', models.TextField(default=b'{}')),
            ],
        ),
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('story_id', models.PositiveIntegerField(unique=True, db_index=True)),
                ('num_comments', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=511)),
            ],
        ),
    ]
