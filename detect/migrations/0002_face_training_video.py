# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('detect', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='face',
            name='training_video',
            field=models.FileField(default=b'', upload_to=b'videos/%Y/%m/%d'),
        ),
    ]
