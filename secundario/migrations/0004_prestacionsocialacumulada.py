# Generated by Django 5.1.5 on 2025-07-17 18:40

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('secundario', '0003_usuarios_empleado'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrestacionSocialAcumulada',
            fields=[
                ('id_prestacion_social', models.AutoField(primary_key=True, serialize=False)),
                ('fecha_movimiento', models.DateField(default=django.utils.timezone.now, verbose_name='Fecha Movimiento')),
                ('tipo_movimiento', models.CharField(choices=[('DEPOSITO', 'Depósito Trimestral'), ('INTERESES', 'Intereses Anuales'), ('LIQUIDACION', 'Liquidación')], max_length=20, verbose_name='Tipo de Movimiento')),
                ('monto_bs', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Monto (Bs)')),
                ('saldo_anterior_bs', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Saldo Anterior (Bs)')),
                ('saldo_actual_bs', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Saldo Actual (Bs)')),
                ('periodo_inicio', models.DateField(blank=True, null=True, verbose_name='Período Inicio (para Depósito)')),
                ('periodo_fin', models.DateField(blank=True, null=True, verbose_name='Período Fin (para Depósito)')),
                ('descripcion', models.TextField(blank=True, null=True, verbose_name='Descripción')),
                ('id_empleado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='secundario.empleado', verbose_name='Empleado')),
            ],
            options={
                'verbose_name': 'Prestación Social Acumulada',
                'verbose_name_plural': 'Prestaciones Sociales Acumuladas',
                'ordering': ['-fecha_movimiento', 'id_empleado'],
            },
        ),
    ]
