# Generated by Django 4.2.2 on 2023-10-07 03:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notion_auth', '0002_alter_lineuser_eeclass_password_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lineuser',
            name='eeclass_db_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
