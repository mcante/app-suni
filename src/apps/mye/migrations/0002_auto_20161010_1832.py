# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-10 18:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('escuela', '0002_escuela_cooperante_asignado'),
        ('mye', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='escuelacooperante',
            unique_together=set([('escuela', 'cooperante')]),
        ),
    ]
