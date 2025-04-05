from django.contrib.auth.models import User  
from django.db import models 

class Usuarios(models.Model):  
    user = models.OneToOneField(User, on_delete=models.CASCADE)  
    puesto = models.CharField(max_length=100)

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
    cedula = models.CharField(max_length=15, unique=True, null=False, blank=False)
    nombre = models.CharField(max_length=100)  
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15, blank=True, null=True)  
    correo = models.EmailField(blank=True, null=True)  
    fecha_contratacion = models.DateField()  
    id_depa = models.ForeignKey(Departamento, on_delete=models.CASCADE)  
    id_pro = models.ForeignKey(Profesion, on_delete=models.CASCADE)  
    id_trabajo = models.ForeignKey(Labor, on_delete=models.CASCADE)  
    id_jornada = models.ForeignKey(TipoDeJornada, on_delete=models.CASCADE)  



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
    id_nomina = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    id_sueldo = models.ForeignKey(Sueldo, on_delete=models.CASCADE)
    periodo = models.DateField()
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
    total_deducciones_bs = models.DecimalField(max_digits=15, decimal_places=2)
    sueldo_neto_bs = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_emision = models.DateField()
    
    def __str__(self):
        return f"Nómina {self.id_nomina} - {self.id_empleado.nombre} {self.periodo}" 
