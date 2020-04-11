# Generated by Django 2.2.11 on 2020-04-10 13:33

import django.core.validators
from django.db import migrations, models
import pomodorr.users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_remove_user_auxiliary_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=models.FileField(null=True, upload_to=pomodorr.users.models.user_upload_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])], verbose_name='avatar'),
        ),
    ]
