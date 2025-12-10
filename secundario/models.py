from django.contrib.auth.models import User  
from django.db import models
from django.utils import timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


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




class Nomina(models.Model):
    TIPO_PERIODO_CHOICES = [
        ('semanal', 'Semanal'),
       
    ]

    id_nomina = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    id_trabajo = models.ForeignKey(Labor, on_delete=models.CASCADE)
    id_sueldo = models.ForeignKey(Sueldo, on_delete=models.CASCADE)
    periodo_inicio = models.DateField(verbose_name="Fecha de Inicio del Período")
    periodo_fin = models.DateField(verbose_name="Fecha de Fin del Período")
    tipo_periodo = models.CharField(max_length=10, choices=TIPO_PERIODO_CHOICES, default='semanal')
    sueldo_bs_base = models.DecimalField(max_digits=15, decimal_places=2)
    cestaticket_bs = models.DecimalField(max_digits=15, decimal_places=2)
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
    pago_inasistencias_bs = models.DecimalField(max_digits=15, decimal_places=2, default=0.00) 
    pago_prestamo_bs = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Deducción Préstamo (Bs)")
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



class PrestacionSocialAcumulada(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='prestaciones_acumuladas')
    fecha_calculo = models.DateField(default=timezone.now)
    monto_acumulado = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    intereses_acumulados = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    dias_acumulados = models.IntegerField(default=0) 
   
    salario_integral_referencia = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"PS de {self.empleado.nombre} - {self.fecha_calculo.year}"

    class Meta:
        verbose_name = "Prestación Social Acumulada"
        verbose_name_plural = "Prestaciones Sociales Acumuladas"
        ordering = ['-fecha_calculo']


class Liquidacion(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='liquidaciones')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_fin_relacion = models.DateField(verbose_name="Fecha de Fin de Relación Laboral")
    motivo_terminacion = models.CharField(
        max_length=50,
        choices=[
            ('renuncia', 'Renuncia'),
            ('despido_justificado', 'Despido Justificado'),
            ('despido_injustificado', 'Despido Injustificado'),
            ('vacaciones', 'Vacaciones')
        ],
        verbose_name="Motivo de Terminación"
    )
    salario_normal_final = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Último Salario Normal")
    salario_integral_final = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Último Salario Integral")

    monto_prestaciones_garantia = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Monto Garantía de Prestaciones Sociales")
    monto_intereses_prestaciones = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Monto Intereses de Prestaciones")
    monto_prestaciones_retroactivo = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Monto Prestaciones (Cálculo Retroactivo)")
    monto_prestaciones_a_pagar = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Total Prestaciones a Pagar")
    anticipos_prestaciones = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Anticipos de Prestaciones Descontados")

    dias_vacaciones_otorgados = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Días de Vacaciones Otorgados (si aplica)"
    )

    fecha_regreso_trabajo = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Regreso al Trabajo"
    )
    dias_vacaciones_pendientes = models.IntegerField(default=0, verbose_name="Días Vacaciones Pendientes")
    monto_vacaciones_pendientes = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Monto Vacaciones Pendientes")
    dias_bono_vacacional_pendiente = models.IntegerField(default=0, verbose_name="Días Bono Vacacional Pendientes")
    monto_bono_vacacional_pendiente = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Monto Bono Vacacional Pendiente")

    dias_utilidades_pendientes = models.IntegerField(default=0, verbose_name="Días Utilidades Pendientes")
    monto_utilidades_pendientes = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Monto Utilidades Pendientes")

    monto_indemnizacion_despido = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Indemnización por Despido Injustificado")
    monto_preaviso = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Monto de Preaviso")

    total_liquidacion = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Total de Liquidación")

    def __str__(self):
        return f"Liquidación de {self.empleado.nombre} {self.empleado.apellido} - {self.fecha_fin_relacion}"

    class Meta:
        verbose_name = "Liquidación"
        verbose_name_plural = "Liquidaciones"
        ordering = ['-fecha_fin_relacion']



class Prestamo(models.Model):
    id_prestamo = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, verbose_name="Empleado")
    monto_total_bs = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto Total del Préstamo (Bs)")
    monto_pendiente_bs = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Monto Pendiente (Bs)")
    cuotas_restantes = models.IntegerField(default=0, verbose_name="Cuotas Restantes")
    monto_cuota_bs = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto por Cuota (Bs)")
    fecha_solicitud = models.DateField(auto_now_add=True, verbose_name="Fecha de Solicitud")
    aprobado = models.BooleanField(default=False, verbose_name="Aprobado")
    fecha_aprobacion = models.DateField(null=True, blank=True, verbose_name="Fecha de Aprobación")
    activo = models.BooleanField(default=True, verbose_name="Activo") # Para saber si el préstamo aún tiene pagos pendientes

    def save(self, *args, **kwargs):
        if not self.pk: 
            self.monto_pendiente_bs = self.monto_total_bs
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Préstamo a {self.id_empleado.nombre} {self.id_empleado.apellido} - {self.monto_total_bs} Bs (Pendiente: {self.monto_pendiente_bs} Bs)"

    class Meta:
        verbose_name = "Préstamo"
        verbose_name_plural = "Préstamos"
        ordering = ['-fecha_solicitud']

class ConceptoNomina(models.Model):
    TIPO = (('ASIGNACION', 'Asignación'), ('DEDUCCION', 'Deducción'))
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=12, choices=TIPO)
    es_por_dias = models.BooleanField(default=False, help_text="Ej: Salario base")
    es_cuota_fija = models.BooleanField(default=False, help_text="Ej: Cestaticket")
    valor_fijo = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    formula = models.TextField(blank=True, help_text="Ej: salario * 0.04 (IVSS)")

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class NominaNueva(models.Model):
    ESTADO = (('PN', 'Prenómina'), ('CC', 'Nómina Cerrada'))
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    sueldo = models.ForeignKey(Sueldo, on_delete=models.PROTECT)
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    estado = models.CharField(max_length=2, choices=ESTADO, default='PN')
    fecha_generacion = models.DateField(auto_now_add=True)

    def dias_trabajados(self):
        return (self.periodo_fin - self.periodo_inicio).days + 1

    def salario_diario(self):
        return self.sueldo.sueldo_bs / Decimal('30')

    def total_asignaciones(self):
        return sum(i.monto for i in self.items.filter(concepto__tipo='ASIGNACION'))

    def total_deducciones(self):
        return sum(i.monto for i in self.items.filter(concepto__tipo='DEDUCCION'))

    def neto(self):
        return self.total_asignaciones() - self.total_deducciones()

    def __str__(self):
        return f"{self.get_estado_display()} - {self.empleado} ({self.periodo_inicio})"


class ItemNomina(models.Model):
    nomina = models.ForeignKey(NominaNueva, related_name='items', on_delete=models.CASCADE)
    concepto = models.ForeignKey(ConceptoNomina, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unidad = models.CharField(max_length=20, default='DÍAS')
    monto = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.monto = self.calcular()
        super().save(*args, **kwargs)

    def calcular(self):
        salario = self.nomina.sueldo.sueldo_bs
        dias = self.nomina.dias_trabajados()

        if self.concepto.es_cuota_fija and self.concepto.valor_fijo:
            return self.concepto.valor_fijo

        if self.concepto.es_por_dias:
            valor_diario = salario / Decimal('30')
            return round(valor_diario * self.cantidad, 2)

        if self.concepto.formula:
            local = {'salario': salario, 'dias': dias, 'cantidad': self.cantidad}
            try:
                return round(eval(self.concepto.formula, {"__builtins__": {}}, local), 2)
            except:
                return Decimal('0.00')
        return Decimal('0.00')

    def __str__(self):
        return f"{self.concepto} → {self.monto}"
