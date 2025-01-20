# Generated by Django 5.1.4 on 2025-01-20 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_customuser_disabled'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='disabled',
        ),
        migrations.AddField(
            model_name='tradeaccount',
            name='disabled',
            field=models.BooleanField(default=False),
        ),
    ]
