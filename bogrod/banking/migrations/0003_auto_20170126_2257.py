# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-26 21:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0002_account_account_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='account_type',
            field=models.CharField(choices=[('checking', 'Checking account'), ('savings', 'Savings account'), ('secondparty', 'Second party account'), ('other', 'Other account')], default='other', max_length=10),
        ),
        migrations.AlterField(
            model_name='account',
            name='iban',
            field=models.CharField(max_length=34, unique=True, verbose_name='iban'),
        ),
    ]
