from django.contrib.auth.models import User  
from django.db import models
from django.utils import timezone

class Usuarios(models.Model):  
    user = models.OneToOneField(User, on_delete=models.CASCADE)  
    puesto = models.CharField(max_length=100)
    empleado = models.OneToOneField('Empleado', on_delete=models.CASCADE, null=True, blank=True, related_name='user_account')
    def __str__(self):  
        return self.user.username 

class Departamento(models.Model):  
    id_depa = models.AutoField(primary_key=True)  
    nombre_depa = models.CharField(max_length=100)  
    ubicacion = models.CharField(max_length=100)  
    def __str__(self):  
        return self.nombre_depa

class Profesion(models.Model):  
    id_pro = models.AutoField(primary_key=True)  
    nombre_pro = models.CharField(max_length=100)
    def __str__(self):  
        return self.nombre_pro

class TipoDeJornada(models.Model):  
    id_jornada = models.AutoField(primary_key=True)  
    nombre_jornada = models.CharField(max_length=100)  
    horas_semanales = models.IntegerField()
    sueldo_semanal_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 

    def __str__(self):  
        return self.nombre_jornada


class Labor(models.Model):  
    id_trabajo = models.AutoField(primary_key=True)  
    nombre_trabajo = models.CharField(max_length=100)  
    descripcion = models.TextField()
    def __str__(self):  
        return self.nombre_trabajo  

class Empleado(models.Model):  
    id_empleado = models.AutoField(primary_key=True)  
    cedula = models.CharField(max_length=10, unique=True, null=False, blank=False,)
    nombre = models.CharField(max_length=100)  
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=11, blank=True, null=True,)  
    correo = models.EmailField(blank=True, null=True)  
    fecha_contratacion = models.DateField()  
    id_depa = models.ForeignKey(Departamento, on_delete=models.CASCADE)  
    id_pro = models.ForeignKey(Profesion, on_delete=models.CASCADE)  
    id_trabajo = models.ForeignKey(Labor, on_delete=models.CASCADE)  
    id_jornada = models.ForeignKey(TipoDeJornada, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} {self.apellido}" 


class Tasa(models.Model):
    id_tasa = models.AutoField(primary_key=True)
    fecha = models.DateField()
    valor_tasa = models.DecimalField(max_digits=15, decimal_places=2)
    activa = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Tasa {self.fecha} - {self.valor_tasa}"


class Sueldo(models.Model):
    id_sueldo = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, verbose_name="Empleado")
    id_jornada = models.ForeignKey(TipoDeJornada, on_delete=models.CASCADE, verbose_name="Jornada")
    id_tasa = models.ForeignKey(Tasa, on_delete=models.CASCADE, verbose_name="Tasa")
    sueldo_bs = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    fecha_creacion = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.id_jornada and self.id_tasa:
            self.sueldo_bs = self.id_jornada.sueldo_semanal_usd * self.id_tasa.valor_tasa
        super().save(*args, **kwargs)

class PrestacionSocialAcumulada(models.Model):
    """
    Modelo para registrar el historial de depósitos y cálculos de intereses de prestaciones sociales.
    """
    TIPO_MOVIMIENTO_CHOICES = [
        ('DEPOSITO', 'Depósito Trimestral'),
        ('INTERESES', 'Intereses Anuales'),
        ('LIQUIDACION', 'Liquidación'),
    ]

    id_prestacion_social = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, verbose_name="Empleado")
    fecha_movimiento = models.DateField(default=timezone.now, verbose_name="Fecha Movimiento")
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO_CHOICES,
                                      verbose_name="Tipo de Movimiento")
    monto_bs = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto (Bs)")
    saldo_anterior_bs = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Saldo Anterior (Bs)")
    saldo_actual_bs = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Saldo Actual (Bs)")
    periodo_inicio = models.DateField(null=True, blank=True, verbose_name="Período Inicio (para Depósito)")
    periodo_fin = models.DateField(null=True, blank=True, verbose_name="Período Fin (para Depósito)")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Prestación Social Acumulada"
        verbose_name_plural = "Prestaciones Sociales Acumuladas"
        ordering = ['-fecha_movimiento', 'id_empleado']

    def __str__(self):
        return f"{self.id_empleado.nombre} {self.id_empleado.apellido} - {self.tipo_movimiento} ({self.fecha_movimiento}): {self.monto_bs:.2f} Bs"




class Nomina(models.Model):
    TIPO_PERIODO_CHOICES = [
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
    ]

    id_nomina = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    id_trabajo = models.ForeignKey(Labor, on_delete=models.CASCADE)
    id_sueldo = models.ForeignKey(Sueldo, on_delete=models.CASCADE)
    periodo_inicio = models.DateField(verbose_name="Fecha de Inicio del Período")
    periodo_fin = models.DateField(verbose_name="Fecha de Fin del Período")
    tipo_periodo = models.CharField(max_length=10, choices=TIPO_PERIODO_CHOICES, default='quincenal')
    sueldo_bs_base = models.DecimalField(max_digits=15, decimal_places=2)
    cestaticket_bs = models.DecimalField(max_digits=15, decimal_places=2)
    pago_prestaciones_bs = models.DecimalField(max_digits=15, decimal_places=2, default=0.00) 
    horas_extras = models.IntegerField(default=0)
    horas_ordinarias = models.DecimalField(max_digits=5, decimal_places=2)
    pago_horas_extras_bs = models.DecimalField(max_digits=15, decimal_places=2)
    horas_festivas = models.IntegerField(default=0)
    pago_horas_festivas_bs = models.DecimalField(max_digits=15, decimal_places=2)
    dias_vacaciones = models.IntegerField(default=0)
    dias_enfermedad = models.IntegerField(default=0)
    total_asignaciones_bs = models.DecimalField(max_digits=15, decimal_places=2)
    ivss_bs = models.DecimalField(max_digits=15, decimal_places=2)
    rpe_bs = models.DecimalField(max_digits=15, decimal_places=2)
    faov_bs = models.DecimalField(max_digits=15, decimal_places=2)
    total_deducciones_bs = models.DecimalField(max_digits=15, decimal_places=2)
    sueldo_neto_bs = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_emision = models.DateField(auto_now_add=True) 

    def __str__(self):
        return f"Nómina {self.id_nomina} - {self.id_empleado.nombre} {self.periodo_inicio} a {self.periodo_fin}" 


class Asistencia(models.Model):
    TIPO_INASISTENCIA_CHOICES = [
        ('justificada', 'Justificada'),
        ('injustificada', 'Injustificada'),
        ('enfermedad', 'Enfermedad'),
        ('vacaciones', 'Vacaciones'),
        ('permiso', 'Permiso'),
    ]
    
    id_asistencia = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, verbose_name="Empleado")
    fecha_asistencia = models.DateField(verbose_name="Fecha de Asistencia")
    asistio = models.BooleanField(default=False, verbose_name="Asistió")
    tipo_inasistencia = models.CharField(
        max_length=20, 
        choices=TIPO_INASISTENCIA_CHOICES, 
        blank=True, 
        null=True,
        verbose_name="Tipo de inasistencia"
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    
    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        unique_together = ('id_empleado', 'fecha_asistencia')
    
    def __str__(self):
        return f"{self.id_empleado.nombre} - {self.fecha_asistencia} - {'Sí' if self.asistio else 'No'}"
    

class Asistenciaconfirmada(models.Model):
    id_asistencia = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    asistio = models.BooleanField(default=False) 
    fecha_asistencia = models.DateField(default=timezone.localdate) 
    hora_entrada = models.TimeField(null=True, blank=True) 
    hora_salida = models.TimeField(null=True, blank=True)
    def __str__(self):
        return f"Asistencia de {self.id_empleado.nombre} el {self.fecha_asistencia}" 

    class Meta:
        unique_together = ('id_empleado', 'fecha_asistencia', 'asistio')