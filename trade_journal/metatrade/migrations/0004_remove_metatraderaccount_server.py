# Generated by Django 5.1.4 on 2024-12-10 13:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('metatrade', '0003_metatraderaccount_server'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='metatraderaccount',
            name='server',
        ),
    ]
