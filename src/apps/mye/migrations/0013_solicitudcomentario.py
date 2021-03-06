# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-04-04 18:07
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mye', '0012_auto_20171016_0835'),
    ]

    operations = [
        migrations.CreateModel(
            name='SolicitudComentario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comentario', models.TextField()),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('solicitud', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comentarios_solicitud', to='mye.Solicitud')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Comentario de Solicitud',
                'verbose_name_plural': 'Comentarios de Solicitud',
            },
        ),
    ]
