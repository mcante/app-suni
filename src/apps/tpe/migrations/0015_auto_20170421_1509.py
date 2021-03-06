# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-04-21 15:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tpe', '0014_auto_20170419_1616'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketreparacionrepuesto',
            name='rechazado',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='tickettransporte',
            name='ticket',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transportes', to='tpe.TicketSoporte'),
        ),
    ]
