from django.contrib.auth.models import User  
from django.db import models
from django.utils import timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password



class CodigoActivacionSuperuser(models.Model):
    """
    UN SOLO registro en toda la base de datos.
    Aquí se guarda el código permanente para crear superusuarios.
    """
    codigo_hash = models.CharField(max_length=255, blank=True, verbose_name="superuser_code")
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activado = models.BooleanField(default=False, help_text="Marcado cuando ya se configuró el código")

    class Meta:
        verbose_name = "Código de Activación de Superusuarios"        
        verbose_name_plural = "Código de Activación de Superusuarios"  

    def __str__(self):
        return "Código de Activación de Superusuarios"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def validar_codigo(cls, codigo: str) -> bool:
        try:
            obj = cls.objects.get(pk=1)
            return check_password(codigo, obj.codigo_hash) if obj.codigo_hash else False
        except cls.DoesNotExist:
            return False




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
    
    horas_diarias = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('8.00'), 
                                       verbose_name="Horas Diarias de Trabajo") 

    @property
    def horas_semanales(self):
        return self.horas_diarias * 5
    
    def __str__(self):  
        return f"{self.nombre_jornada} ({self.horas_semanales} hrs/sem)"


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
    id_labor = models.ForeignKey('Labor', on_delete=models.CASCADE, verbose_name="Labor") 
    id_tasa = models.ForeignKey('Tasa', on_delete=models.CASCADE, verbose_name="Tasa")
    sueldo_usd_referencia = models.DecimalField(max_digits=10, decimal_places=2, editable=False) 
    sueldo_bs = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    fecha_creacion = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        try:
            sueldo_base = self.id_labor.sueldolabor.sueldo_base_semanal_usd
        except SueldoLabor.DoesNotExist:
            raise ValueError(f"La Labor '{self.id_labor.nombre_trabajo}' no tiene un Sueldo Base (SueldoLabor) asignado.")
            
        if self.id_tasa:
            self.sueldo_usd_referencia = sueldo_base
            self.sueldo_bs = sueldo_base * self.id_tasa.valor_tasa
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Sueldo Liquidado (Histórico)"
        verbose_name_plural = "Sueldos Liquidados (Históricos)"

class DetalleConceptoNomina(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    
    id_nomina = models.ForeignKey('Nomina', on_delete=models.CASCADE, related_name='detalles_personalizados', verbose_name="Nómina")
    
    id_regla = models.ForeignKey('ParametrosNomina', on_delete=models.CASCADE, null=True, blank=True)
    
    nombre_concepto = models.CharField(max_length=150, verbose_name="Nombre del Concepto")
    tipo_concepto = models.CharField(max_length=10, verbose_name="Tipo (Asignación/Deducción)") 
    monto_calculado_bs = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto Calculado (Bs)")

    class Meta:
        verbose_name = "Detalle de Concepto Personalizado"
        verbose_name_plural = "Detalles de Conceptos Personalizados"
        unique_together = ('id_nomina', 'id_regla') 
        
    def __str__(self):
        return f"Detalle {self.nombre_concepto} para Nómina #{self.id_nomina.id_nomina}"

class ConceptoNomina(models.Model):
    id_nomina = models.OneToOneField('Nomina', on_delete=models.CASCADE, primary_key=True, verbose_name="Nómina")
    pago_bonos_bs = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Pago de Bonos Extra (Bs)")
    sueldo_bs_base = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Sueldo Base (Bs)")
    pago_recargo_nocturno_bs = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'), 
        verbose_name="Pago Recargo Nocturno (Bs)"
    )
    cestaticket_bs = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Cestaticket (Bs)")
    horas_ordinarias = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name="Horas Ordinarias")
    horas_extras = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name="Total Horas Extras")
    pago_horas_extras_bs = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Pago Horas Extras (Bs)")
    horas_festivas = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name="Total Horas Festivas")
    pago_horas_festivas_bs = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Pago Horas Festivas (Bs)")
    dias_vacaciones = models.IntegerField(default=0, verbose_name="Días de Vacaciones Pagados")
    dias_enfermedad = models.IntegerField(default=0, verbose_name="Días de Inasistencia (Deducidos)") 
    inces_bs = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Deducción INCES (Bs)")
    ivss_bs = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Deducción IVSS (Bs)")
    rpe_bs = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Deducción RPE (Bs)")
    faov_bs = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Deducción FAOV (Bs)")
    pago_inasistencias_bs = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Deducción Inasistencias (Bs)")
    pago_prestamo_bs = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Deducción Préstamo (Bs)")

    total_asignaciones_bs = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Total Asignaciones")
    total_deducciones_bs = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Total Deducciones")

    class Meta:
        verbose_name = "Concepto de Nómina"
        verbose_name_plural = "Conceptos de Nómina"
        
    def __str__(self):
        return f"Conceptos de Nómina #{self.id_nomina.id_nomina}"




class Nomina(models.Model):
    id_nomina = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, verbose_name="Empleado")
    id_sueldo = models.ForeignKey(Sueldo, on_delete=models.CASCADE, verbose_name="Sueldo")
    id_trabajo = models.ForeignKey(Labor, on_delete=models.CASCADE, verbose_name="Labor")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    periodo_inicio = models.DateField(verbose_name="Período de Inicio")
    periodo_fin = models.DateField(verbose_name="Período de Fin")
    tipo_periodo = models.CharField(max_length=50, verbose_name="Tipo de Período")

    total_asignaciones_bs = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Total Asignaciones (Bs)")
    total_deducciones_bs = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Total Deducciones (Bs)")
    sueldo_neto_bs = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Sueldo Neto (Bs)")
    


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
    
    def clean(self):
        """
        Valida que la fecha de asistencia no sea anterior a la fecha de contratación.
        """
        if self.id_empleado and self.fecha_asistencia:
            
            fecha_contratacion = self.id_empleado.fecha_contratacion 
            
            if self.fecha_asistencia < fecha_contratacion:
                raise ValidationError({
                    'fecha_asistencia': (
                        f"La fecha de inasistencia ({self.fecha_asistencia.strftime('%d/%m/%Y')}) "
                        f"no puede ser anterior a la fecha de contratación del empleado "
                        f"({fecha_contratacion.strftime('%d/%m/%Y')})."
                    )
                })

    def save(self, *args, **kwargs):
     
        self.full_clean() 
        super().save(*args, **kwargs)
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
    activo = models.BooleanField(default=True, verbose_name="Activo") 
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

TIPO_CONCEPTO_CHOICES = [
    ('ASIGNACION', 'Asignación'),
    ('DEDUCCION', 'Deducción'),
]

PERIODICIDAD_CHOICES = [
    ('SEMANAL', 'Semanal'),
    ('QUINCENAL', 'Quincenal'),
    ('MENSUAL', 'Mensual'),
    ('TRIMESTRAL', 'Trimestral'),
    ('ANUAL', 'Anual'),
    ('UNICA', 'Única (por evento)'),
]

class ParametrosNomina(models.Model):
    id_parametro = models.AutoField(primary_key=True) 
    
    nombre = models.CharField(max_length=150, unique=True, verbose_name="Nombre del Concepto/Regla")
    
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CONCEPTO_CHOICES,
        default='ASIGNACION',
        verbose_name="Tipo de Concepto"
    )
    
    periodicidad = models.CharField(
        max_length=10,
        choices=PERIODICIDAD_CHOICES,
        default='MENSUAL',
        verbose_name="Periodicidad de Aplicación"
    )
    
    monto_fijo = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'), 
        blank=True, null=True, verbose_name="Monto Fijo (Bs) / Valor UT"
    )

    monto_fijo_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, blank=True, null=True,
    help_text="Monto en USD (ej: cestaticket 40 USD)")
    
    porcentaje = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.0000'), 
        blank=True, null=True, verbose_name="Porcentaje (Ej: Tasa IVSS)"
    )
    
    es_concepto_fijo = models.BooleanField(
        default=False, 
        verbose_name="Es Tasa/Factor Fijo Global (IVSS, UT, Cesta)"
    )
    
    fecha_ultima_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")




    class Meta:
        verbose_name = "Concepto/Regla de Nómina"
        verbose_name_plural = "Conceptos/Reglas de Nómina"
    


    def valor_en_bs(self):
        """
        Devuelve el monto en bolívares según prioridad:
        1. Si tiene monto_fijo_usd → convierte con la última tasa BCV
        2. Si no → usa monto_fijo directamente
        """
        if self.monto_fijo_usd and self.monto_fijo_usd > 0:
            try:
                ultima_tasa = Tasa.objects.latest('fecha')
                return self.monto_fijo_usd * ultima_tasa.valor_tasa
            except Tasa.DoesNotExist:
                return Decimal('0.00')
        return self.monto_fijo
        
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class SueldoLabor(models.Model):
    id_labor = models.OneToOneField('Labor', on_delete=models.CASCADE, primary_key=True, verbose_name="Labor (Cargo)")
    
    sueldo_base_semanal_usd = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Sueldo Base Semanal (USD)"
    ) 
    
    fecha_establecimiento = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Sueldo Base para {self.id_labor.nombre_trabajo}: ${self.sueldo_base_semanal_usd}"

    class Meta:
        verbose_name = "Sueldo por Labor"
        verbose_name_plural = "Sueldos por Labor"


class CambioLabor(models.Model):
    id_cambio = models.AutoField(primary_key=True)
    
    id_empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, related_name='cambios_labor')
    
    labor_anterior = models.ForeignKey('Labor', on_delete=models.SET_NULL, null=True, related_name='labor_previa')
    
    labor_nueva = models.ForeignKey('Labor', on_delete=models.SET_NULL, null=True, related_name='labor_actual')
    
    fecha_cambio = models.DateTimeField(default=timezone.now, verbose_name="Fecha y Hora del Cambio")
    motivo = models.CharField(max_length=255, blank=True, null=True, verbose_name="Motivo o Razón del Cambio")
    
    class Meta:
        verbose_name = "Registro de Cambio de Labor"
        verbose_name_plural = "Historial de Cambios de Labor"
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"{self.id_empleado.nombre} cambió de {self.labor_anterior.nombre_trabajo if self.labor_anterior else 'N/A'} a {self.labor_nueva.nombre_trabajo} el {self.fecha_cambio.date()}"
    

class BonoExtra(models.Model):
    id_bono = models.AutoField(primary_key=True)
    
    id_empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, related_name='bonos_recibidos')
    
    concepto = models.CharField(max_length=150, verbose_name="Concepto del Bono")
    
    monto_bs = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto (Bs)")
    
    fecha_aplicacion = models.DateField(verbose_name="Fecha de Aplicación")
    
    pagado_en_nomina = models.BooleanField(default=False, verbose_name="Pagado en Nómina")
    
    fecha_registro = models.DateTimeField(default=timezone.now)

    

    class Meta:
        verbose_name = "Asignación/Bono Extra"
        verbose_name_plural = "Asignaciones/Bonos Extras"
        ordering = ['-fecha_aplicacion']

    def __str__(self):
        return f"Bono de Bs {self.monto_bs} para {self.id_empleado.nombre} ({self.concepto})"