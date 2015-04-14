# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0004_auto_20150414_0054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='recognizer',
            field=models.ForeignKey(related_name='recognizer', blank=True, to='detect.Recognizer', null=True),
        ),
    ]
