# Generated by Django 5.0.7 on 2024-08-31 08:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0010_wallet_transaction'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wallet',
            name='user',
        ),
        migrations.DeleteModel(
            name='Transaction',
        ),
        migrations.DeleteModel(
            name='Wallet',
        ),
    ]
