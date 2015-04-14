# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0002_auto_20150413_2350'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='device',
            field=models.ForeignKey(related_name='device', blank=True, to='video.LocalSource'),
        ),
    ]
