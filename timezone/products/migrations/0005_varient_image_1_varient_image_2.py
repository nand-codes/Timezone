# Generated by Django 5.0.7 on 2024-08-16 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_alter_products_gender'),
    ]

    operations = [
        migrations.AddField(
            model_name='varient',
            name='image_1',
            field=models.ImageField(blank=True, null=True, upload_to='images'),
        ),
        migrations.AddField(
            model_name='varient',
            name='image_2',
            field=models.ImageField(blank=True, null=True, upload_to='images'),
        ),
    ]
