# Generated by Django 4.2.2 on 2023-10-06 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notion_auth', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lineuser',
            name='eeclass_password',
            field=models.CharField(max_length=255, null=''),
        ),
        migrations.AlterField(
            model_name='lineuser',
            name='eeclass_username',
            field=models.CharField(max_length=255, null=''),
        ),
    ]