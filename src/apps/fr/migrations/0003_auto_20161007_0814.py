# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-07 14:14
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('fr', '0002_auto_20161006_2013'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contacto',
            name='etiquetas',
            field=models.ManyToManyField(related_name='contacto', to='fr.Etiqueta'),
        ),
        migrations.AlterField(
            model_name='contacto',
            name='fecha_creacion',
            field=models.DateField(default=datetime.datetime(2016, 10, 7, 14, 14, 37, 853295, tzinfo=utc)),
        ),
    ]