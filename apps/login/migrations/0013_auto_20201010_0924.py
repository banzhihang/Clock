# Generated by Django 2.2.12 on 2020-10-10 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0012_auto_20201009_1127'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='photo',
            field=models.URLField(blank=True, max_length=300, null=True, verbose_name='图片名字'),
        ),
    ]
