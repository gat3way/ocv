# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('detect', '0002_face_training_video'),
    ]

    operations = [
        migrations.CreateModel(
            name='LocalSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(max_length=200)),
                ('name', models.CharField(max_length=200)),
                ('height', models.IntegerField()),
                ('width', models.IntegerField()),
                ('fps', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Sink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('short_id', models.CharField(default=None, unique=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(max_length=200)),
                ('name', models.CharField(max_length=200)),
                ('device', models.ForeignKey(related_name='device', to='video.LocalSource')),
                ('overlay_sink', models.ForeignKey(related_name='overlay', to='video.Sink')),
                ('raw_sink', models.ForeignKey(related_name='raw', to='video.Sink')),
                ('recognizer', models.ForeignKey(related_name='recognizer', blank=True, to='detect.Recognizer')),
            ],
        ),
        migrations.CreateModel(
            name='Storage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('backend', models.CharField(max_length=10, choices=[(b'local', b'Local filesystem'), (b'http', b'HTTP upload'), (b'ftp', b'FTP upload')])),
                ('url', models.CharField(max_length=200)),
                ('username', models.CharField(max_length=200, blank=True)),
                ('password', models.CharField(max_length=200, blank=True)),
                ('remote_dir', models.CharField(max_length=200, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='source',
            name='storage',
            field=models.ForeignKey(related_name='storage', to='video.Storage'),
        ),
    ]
