# Generated by Django 2.2.12 on 2020-11-10 17:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0020_auto_20201110_1752'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='address',
            field=models.CharField(default='', max_length=100, verbose_name='打卡地址'),
        ),
    ]