# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-04 21:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('escuela', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='esccontactomail',
            name='contacto',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mail', to='escuela.EscContacto'),
        ),
        migrations.AlterField(
            model_name='esccontactotelefono',
            name='contacto',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='telefono', to='escuela.EscContacto'),
        ),
        migrations.AlterField(
            model_name='esccontactotelefono',
            name='telefono',
            field=models.IntegerField(),
        ),
    ]
