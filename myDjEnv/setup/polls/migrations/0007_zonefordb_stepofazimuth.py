# Generated by Django 4.2 on 2023-10-05 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0006_zonefordb_longofcenter'),
    ]

    operations = [
        migrations.AddField(
            model_name='zonefordb',
            name='stepOfAzimuth',
            field=models.FloatField(default=0.25),
        ),
    ]