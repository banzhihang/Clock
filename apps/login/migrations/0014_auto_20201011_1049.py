# Generated by Django 2.2.12 on 2020-10-11 10:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0013_auto_20201010_0924'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='photo',
            field=models.CharField(blank=True, max_length=300, null=True, verbose_name='图片名字'),
        ),
    ]