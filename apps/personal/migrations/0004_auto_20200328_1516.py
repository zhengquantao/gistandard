# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2020-03-28 15:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personal', '0003_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(max_length=10, verbose_name='订单号'),
        ),
    ]
