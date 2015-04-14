# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0003_auto_20150414_0052'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='device',
            field=models.ForeignKey(related_name='device', blank=True, to='video.LocalSource', null=True),
        ),
    ]
