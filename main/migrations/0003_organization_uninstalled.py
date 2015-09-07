# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20150905_0012'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='uninstalled',
            field=models.BooleanField(default=False),
        ),
    ]
