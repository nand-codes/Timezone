# Generated by Django 5.0.7 on 2024-08-06 17:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0003_alter_products_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='products',
            name='brand',
        ),
        migrations.RemoveField(
            model_name='products',
            name='Category',
        ),
        migrations.DeleteModel(
            name='Brand',
        ),
        migrations.DeleteModel(
            name='Category',
        ),
        migrations.DeleteModel(
            name='Products',
        ),
    ]
