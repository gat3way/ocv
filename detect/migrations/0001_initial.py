# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Face',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('active', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Recognizer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('rtype', models.CharField(max_length=20, choices=[(b'facial', b'Facial Recognition')])),
            ],
        ),
        migrations.AddField(
            model_name='face',
            name='recognizer',
            field=models.ForeignKey(related_name='f_recognizer', to='detect.Recognizer'),
        ),
    ]
