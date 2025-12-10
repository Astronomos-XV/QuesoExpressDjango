# forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib import redirects
from .models import Empleado, Departamento, Profesion, Labor, TipoDeJornada, Nomina, Sueldo, Tasa, Asistencia, Usuarios, Liquidacion,Prestamo, NominaNueva, ItemNomina, ConceptoNomina
from django.utils import timezone
from datetime import date
from django.core.validators import RegexValidator
from django.shortcuts import render, redirect, get_object_or_404


cedula_validator = RegexValidator(
    r'^\d+$',
    'La cédula debe contener solo números.'
)
telefono_validator = RegexValidator(
    r'^\d+$',
    'El teléfono debe contener solo números.'
)

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = ['cedula','nombre', 'apellido', 'telefono', 'correo', 'fecha_contratacion', 'id_depa', 'id_pro', 'id_trabajo', 'id_jornada']

    cedula = forms.CharField(
        max_length=10,
        validators=[
            cedula_validator,
        ],
        help_text="Solo números (ej. 12345678)"
    )
    telefono = forms.CharField(
        max_length=11,
        required=True,
        validators=[
            telefono_validator,

        ],
        help_text="Solo números (ej. 4121234567)"
    )


    fecha_contratacion = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'min': '2010-01-01',
            'max': f'{timezone.now().year}-12-31'
        }),
        help_text="Ingrese la fecha de contratación. (Rango: 2010 - Año actual)"
    )

    id_depa = forms.ModelChoiceField(queryset=Departamento.objects.all(), label="Departamento")
    id_pro = forms.ModelChoiceField(queryset=Profesion.objects.all(), label="Profesión")
    id_trabajo = forms.ModelChoiceField(queryset=Labor.objects.all(), label="Labor")
    id_jornada = forms.ModelChoiceField(queryset=TipoDeJornada.objects.all(), label="Tipo de Jornada")

class SueldoForm(forms.ModelForm):
    class Meta:
        model = Sueldo
        fields = ['id_empleado', 'id_jornada', 'id_tasa']
        labels = {
            'id_empleado': 'Empleado',
            'id_jornada': 'Tipo de Jornada',
            'id_tasa': 'Tasa Activa'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        self.fields['id_tasa'].queryset = Tasa.objects.filter(activa=True)


        self.fields['id_empleado'].queryset = Empleado.objects.all().order_by('nombre')
        self.fields['id_empleado'].label_from_instance = lambda obj: f"{obj.nombre} {obj.apellido} ({obj.cedula})"


        jornadas = TipoDeJornada.objects.all()
        self.fields['id_jornada'].queryset = jornadas
        for jornada in jornadas:
            self.fields['id_jornada'].widget.attrs.update({
                f'data-{jornada.id_jornada}-horas': jornada.horas_semanales
            })

class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        fields = ['nombre_depa', 'ubicacion']

class ProfesionForm(forms.ModelForm):
    class Meta:
        model = Profesion
        fields = ['nombre_pro']

class LaborForm(forms.ModelForm):
    class Meta:
        model = Labor
        fields = ['nombre_trabajo', 'descripcion']

class TipoDeJornadaForm(forms.ModelForm):
    class Meta:
        model = TipoDeJornada
        fields = ['nombre_jornada', 'horas_semanales', 'sueldo_semanal_usd']

class NominaForm(forms.ModelForm):
    class Meta:
        model = Nomina
        fields = [
            'id_empleado', 'id_sueldo', 'id_trabajo', 'periodo_inicio', 'periodo_fin',
            'tipo_periodo', 'sueldo_bs_base', 'cestaticket_bs',  'horas_extras',
            'horas_ordinarias', 'pago_horas_extras_bs', 'horas_festivas',
            'pago_horas_festivas_bs', 'dias_vacaciones', 'dias_enfermedad',
            'total_asignaciones_bs', 'ivss_bs', 'rpe_bs', 'faov_bs',
            'total_deducciones_bs', 'sueldo_neto_bs'
        ]



class BuscarNominaForm(forms.Form):
    cedula = forms.CharField(
        label='Buscar nómina por cédula',
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: V-12345678',
            'class': 'form-control'
        })
    )




class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = ['id_empleado', 'fecha_asistencia', 'tipo_inasistencia', 'observaciones']
        widgets = {
            'fecha_asistencia': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['asistio'] = False
        self.fields['id_empleado'].queryset = Empleado.objects.all()


"""
Formulario para crear nuevos usuarios si es un superusuario o es un usuario normal

"""

class SuperuserForm(forms.ModelForm):
    SUPERUSER_CODE = "62425"

    superuser_code = forms.CharField(
        required=False,
        label='Código de Superusuario (opcional)',
        help_text='Ingrese el código especial para crear un superusuario, déjelo vacío para un usuario normal.'
    )
    password = forms.CharField(widget=forms.PasswordInput)

    
    cedula = forms.CharField(
        max_length=10,
        required=False, 
        label='Cédula del Empleado (para usuarios normales)',
        help_text='Ingrese la cédula del empleado para el usuario normal.'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'cedula']

    def clean_superuser_code(self):
        code = self.cleaned_data.get('superuser_code')
        if code and code != self.SUPERUSER_CODE:
            raise forms.ValidationError('Código de superusuario incorrecto')
        return code

    def clean(self):
        cleaned_data = super().clean()
        superuser_code = cleaned_data.get('superuser_code')
        cedula = cleaned_data.get('cedula')

        is_creating_superuser = (superuser_code == self.SUPERUSER_CODE)

        if not is_creating_superuser:
            if not cedula:
                self.add_error('cedula', 'La cédula es obligatoria para crear un usuario normal.')
            else:
                try:
                    cedula_validator(cedula)
                    empleado = Empleado.objects.get(cedula=cedula)
                    if Usuarios.objects.filter(empleado=empleado).exists():
                        self.add_error('cedula', 'Esta cédula ya está asociada a otro usuario.')
                    cleaned_data['empleado_obj'] = empleado 
                except Empleado.DoesNotExist:
                    self.add_error('cedula', 'No existe un empleado con la cédula proporcionada.')
                except forms.ValidationError as e:
                    self.add_error('cedula', e.message)
        else:
            if cedula:
                self.add_error('cedula', 'La cédula debe dejarse vacía al crear un superusuario.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])

        is_creating_superuser = (self.cleaned_data.get('superuser_code') == self.SUPERUSER_CODE)

        if is_creating_superuser:
            user.is_superuser = True
            user.is_staff = True
        else:
            user.is_superuser = False
            user.is_staff = False

        if commit:
            user.save()

            if not is_creating_superuser:
                empleado = self.cleaned_data.get('empleado_obj') 
                if empleado:
                    Usuarios.objects.create(user=user, empleado=empleado, puesto='Usuario Empleado')

        return user


class NominaGrupalForm(forms.Form):
    labor = forms.ModelChoiceField(queryset=Labor.objects.all(), label="Tipo de Labor")
    tipo_periodo = forms.ChoiceField(choices=Nomina.TIPO_PERIODO_CHOICES, label="Tipo de Período")
    fecha_inicio = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Fecha de Inicio")
    fecha_fin = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Fecha de Fin")

class SueldoGrupalForm(forms.Form):
    labor = forms.ModelChoiceField(queryset=Labor.objects.all(), label="Tipo de Labor")
    jornada = forms.ModelChoiceField(queryset=TipoDeJornada.objects.all(), label="Tipo de Jornada")
    tasa = forms.ModelChoiceField(queryset=Tasa.objects.filter(activa=True), label="Tasa Activa")


class LiquidacionForm(forms.ModelForm):
 
    empleado = forms.ModelChoiceField(queryset=Empleado.objects.all(), label="Empleado a Liquidar")

    class Meta:
        model = Liquidacion
        fields = ['empleado', 'fecha_fin_relacion', 'motivo_terminacion', 'dias_vacaciones_otorgados']
        widgets = {
            'fecha_fin_relacion': forms.DateInput(attrs={'type': 'date'}),
           
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['dias_vacaciones_otorgados'].required = False
        self.fields['dias_vacaciones_otorgados'].help_text = "Solo si el motivo de terminación es 'Vacaciones'."


      

class LiquidacionGrupalForm(forms.Form):
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        label="Filtrar por Departamento"
    )
    labor = forms.ModelChoiceField(
        queryset=Labor.objects.all(),
        required=False,
        label="Filtrar por Labor"
    )
    fecha_fin_relacion = forms.DateField(
        label="Fecha de Fin de Relación Laboral (para el grupo)",
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=date.today
    )
  

    def clean(self):
        cleaned_data = super().clean()
        departamento = cleaned_data.get('departamento')
        labor = cleaned_data.get('labor')
        
        if not departamento and not labor: 
            raise forms.ValidationError("Debe seleccionar un departamento, una labor o empleados específicos para la liquidación grupal.")
        return cleaned_data
    


"""




class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        
        fields = ['id_empleado', 'monto_total_bs', 'monto_cuota_bs', 'cuotas_restantes', 'aprobado']
        
        widgets = {
            'monto_total_bs': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'monto_cuota_bs': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'cuotas_restantes': forms.NumberInput(attrs={'min': '0'}),
        }
        labels = {
            'id_empleado': 'Empleado',
            'monto_total_bs': 'Monto Total del Préstamo (Bs)',
            'monto_cuota_bs': 'Monto por Cuota (Bs)',
            'cuotas_restantes': 'Número de Cuotas',
            'aprobado': '¿Préstamo Aprobado?', 
        }

    def clean(self):
        cleaned_data = super().clean()
        monto_total_bs = cleaned_data.get('monto_total_bs')
        monto_cuota_bs = cleaned_data.get('monto_cuota_bs')
        cuotas_restantes = cleaned_data.get('cuotas_restantes')

      
        if monto_total_bs is not None and monto_cuota_bs is not None and cuotas_restantes is not None:
            if cuotas_restantes > 0 and monto_cuota_bs > 0:
            
                if monto_total_bs < (monto_cuota_bs * cuotas_restantes):
                    self.add_error('monto_cuota_bs', "El monto de la cuota o el número de cuotas no coincide con el monto total del préstamo.")
            elif cuotas_restantes == 0 and monto_total_bs > 0:
                 self.add_error('cuotas_restantes', "Si hay un monto total, debe haber cuotas restantes.")
            elif monto_total_bs == 0 and (monto_cuota_bs > 0 or cuotas_restantes > 0):
                self.add_error('monto_total_bs', "Si el monto total es cero, las cuotas también deben ser cero.")

        return cleaned_data



"""


class PrestamoForm(forms.ModelForm):
    numero_cuotas_deseado = forms.IntegerField(
        label='Número de Cuotas Deseadas',
        min_value=1,
        initial=12,  
        widget=forms.NumberInput(attrs={'min': '1'})
    )

    class Meta:
        model = Prestamo
        fields = ['id_empleado', 'monto_total_bs', 'aprobado']
        
        widgets = {
            'monto_total_bs': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
        labels = {
            'id_empleado': 'Empleado',
            'monto_total_bs': 'Monto Total del Préstamo (Bs)',
            'aprobado': '¿Préstamo Aprobado?', 
        }

    def clean(self):
        cleaned_data = super().clean()
        monto_total_bs = cleaned_data.get('monto_total_bs')
        numero_cuotas_deseado = cleaned_data.get('numero_cuotas_deseado')

        if monto_total_bs is not None and numero_cuotas_deseado is not None:
            if monto_total_bs < 0:
                self.add_error('monto_total_bs', "El monto total del préstamo no puede ser negativo.")
            if numero_cuotas_deseado <= 0:
                self.add_error('numero_cuotas_deseado', "El número de cuotas debe ser mayor que cero.")
            
            
        return cleaned_data

class NominaNuevaForm(forms.ModelForm):
    class Meta:
        model = NominaNueva
        fields = ['empleado', 'sueldo', 'periodo_inicio', 'periodo_fin', 'estado']
        widgets = {
            'periodo_inicio': forms.DateInput(attrs={'type': 'date'}),
            'periodo_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sueldo'].queryset = Sueldo.objects.none()
        if 'empleado' in self.data:
            try:
                empleado_id = int(self.data.get('empleado'))
                self.fields['sueldo'].queryset = Sueldo.objects.filter(id_empleado=empleado_id)
            except:
                pass
        elif self.instance.pk and self.instance.empleado:
            self.fields['sueldo'].queryset = Sueldo.objects.filter(id_empleado=self.instance.empleado)


