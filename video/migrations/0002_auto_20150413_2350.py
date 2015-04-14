# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='motion_detection',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='source',
            name='motion_threshold',
            field=models.IntegerField(default=15),
        ),
    ]
