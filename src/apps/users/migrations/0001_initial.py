# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-06 20:37
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import easy_thumbnails.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Perfil',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dpi', models.CharField(max_length=20, unique=True)),
                ('public', models.BooleanField(default=True)),
                ('genero', models.CharField(choices=[('M', 'Masculino'), ('F', 'Femenino')], default='M', max_length=1)),
                ('fecha_nacimiento', models.DateField(blank=True, null=True)),
                ('direccion', models.CharField(blank=True, max_length=150, null=True)),
                ('foto', easy_thumbnails.fields.ThumbnailerImageField(blank=True, null=True, upload_to='perfil_usuario')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'perfil',
                'verbose_name_plural': 'perfiles',
            },
        ),
        migrations.CreateModel(
            name='PerfilTelefono',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=10)),
                ('principal', models.BooleanField(default=False)),
                ('perfil', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.Perfil')),
            ],
            options={
                'verbose_name': 'Teléfono de perfil',
                'verbose_name_plural': 'Teléfonos de perfil',
            },
        ),
    ]
