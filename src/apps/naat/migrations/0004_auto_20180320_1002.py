# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-03-20 16:02
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('escuela', '0010_auto_20171117_0807'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cyd', '0019_auto_20170822_2059'),
        ('naat', '0003_auto_20180307_0751'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcesoNaat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_inicio', models.DateField(default=django.utils.timezone.now)),
                ('fecha_fin', models.DateField(default=django.utils.timezone.now)),
                ('capacitador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='procesos_naat', to=settings.AUTH_USER_MODEL)),
                ('escuela', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='procesos_naat', to='escuela.Escuela')),
            ],
            options={
                'verbose_name': 'Proceso de Naat',
                'verbose_name_plural': 'Procesos de Naat',
            },
        ),
        migrations.RenameField(
            model_name='sesionpresencial',
            old_name='ovservaciones',
            new_name='observaciones',
        ),
        migrations.RemoveField(
            model_name='sesionpresencial',
            name='capacitador',
        ),
        migrations.RemoveField(
            model_name='sesionpresencial',
            name='escuela',
        ),
        migrations.AlterField(
            model_name='asignacionnaat',
            name='capacitador',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='asignacionnaat',
            name='proceso',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='asignaciones', to='naat.ProcesoNaat'),
        ),
        migrations.AddField(
            model_name='sesionpresencial',
            name='proceso',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sesiones', to='naat.ProcesoNaat'),
        ),
        migrations.RemoveField(
            model_name='asignacionnaat',
            name='fecha_finalizacion',
        ),
        migrations.AlterUniqueTogether(
            name='asignacionnaat',
            unique_together=set([('participante', 'proceso')]),
        ),
    ]
