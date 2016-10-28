# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-12 21:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('escuela', '0003_escuela_proyecto_asignado'),
    ]

    operations = [
        migrations.CreateModel(
            name='Poblacion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alumna', models.IntegerField()),
                ('alumno', models.IntegerField()),
                ('maestra', models.IntegerField()),
                ('maestro', models.IntegerField()),
                ('total_alumno', models.IntegerField(blank=True, null=True)),
                ('total_maestro', models.IntegerField(blank=True, null=True)),
                ('fecha', models.DateField(default=django.utils.timezone.now)),
                ('escuela', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poblacion', to='escuela.Escuela')),
            ],
        ),
    ]