# Generated by Django 5.1.5 on 2025-07-17 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('secundario', '0004_prestacionsocialacumulada'),
    ]

    operations = [
        migrations.AddField(
            model_name='nomina',
            name='pago_prestaciones_bs',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=15),
        ),
    ]
