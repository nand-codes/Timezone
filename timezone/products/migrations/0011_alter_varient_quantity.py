# Generated by Django 5.0.7 on 2024-09-09 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0010_rename_discount_brandoffer_discount_percentage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='varient',
            name='quantity',
            field=models.PositiveIntegerField(),
        ),
    ]
