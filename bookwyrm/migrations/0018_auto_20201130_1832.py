# Generated by Django 3.0.7 on 2020-11-30 18:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bookwyrm', '0017_auto_20201130_1819'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='following',
        ),
        migrations.RemoveField(
            model_name='user',
            name='private_key',
        ),
        migrations.RemoveField(
            model_name='user',
            name='public_key',
        ),
    ]