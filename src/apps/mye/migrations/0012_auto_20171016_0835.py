# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-10-16 14:35
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mye', '0011_validacion_fotos_link'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='escuelacooperante',
            name='cooperante',
        ),
        migrations.RemoveField(
            model_name='escuelacooperante',
            name='escuela',
        ),
        migrations.RemoveField(
            model_name='escuelaproyecto',
            name='escuela',
        ),
        migrations.RemoveField(
            model_name='escuelaproyecto',
            name='proyecto',
        ),
        migrations.DeleteModel(
            name='EscuelaCooperante',
        ),
        migrations.DeleteModel(
            name='EscuelaProyecto',
        ),
    ]
