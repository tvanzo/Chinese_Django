# Generated by Django 4.2.6 on 2025-01-24 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_profile_stripe_customer_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='stripe_subscription_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
