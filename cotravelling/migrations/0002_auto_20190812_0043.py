# Generated by Django 2.2.3 on 2019-08-11 21:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cotravelling', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trip',
            name='source',
            field=models.CharField(default='', max_length=30),
        ),
        migrations.AlterField(
            model_name='trip',
            name='target',
            field=models.CharField(default='', max_length=30),
        ),
        migrations.AlterField(
            model_name='trip',
            name='vehicle',
            field=models.CharField(default='', max_length=30),
        ),
    ]
