# Generated by Django 3.0.6 on 2020-05-20 15:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_auto_20200519_1254'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='blog.User'),
            preserve_default=False,
        ),
    ]
