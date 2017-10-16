# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-10-16 14:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('escuela', '0007_auto_20171013_0827'),
    ]

    operations = [
        migrations.AlterField(
            model_name='escpoblacion',
            name='alumna',
            field=models.PositiveIntegerField(default=0, verbose_name='Estudiantes mujeres'),
        ),
        migrations.AlterField(
            model_name='escpoblacion',
            name='alumno',
            field=models.PositiveIntegerField(default=0, verbose_name='Estudiantes varones'),
        ),
        migrations.AlterField(
            model_name='escpoblacion',
            name='maestra',
            field=models.PositiveIntegerField(default=0, verbose_name='Docentes mujeres'),
        ),
        migrations.AlterField(
            model_name='escpoblacion',
            name='maestro',
            field=models.PositiveIntegerField(default=0, verbose_name='Dicentes varones'),
        ),
        migrations.AlterField(
            model_name='escpoblacion',
            name='total_alumno',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Total de estudiantes'),
        ),
        migrations.AlterField(
            model_name='escpoblacion',
            name='total_maestro',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Total de docentes'),
        ),
    ]
