# Generated by Django 2.2.12 on 2020-10-01 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0005_auto_20200930_1637'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='photo',
            field=models.URLField(null=True, verbose_name='图片地址'),
        ),
    ]
