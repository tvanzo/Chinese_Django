# Generated by Django 4.2.3 on 2023-07-23 08:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subplayer', '0004_alter_highlight_end_time_alter_highlight_start_time'),
    ]

    operations = [
        migrations.AddField(
           model_name='highlight',
    name='end_index',
         field=models.IntegerField(default=0),  # Change the default value to a valid integer
        ),
        migrations.AddField(
            model_name='highlight',
            name='end_sentence_index',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='highlight',
            name='start_index',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='highlight',
            name='start_sentence_index',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
