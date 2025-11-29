# forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Empleado, Departamento, Profesion, Labor, TipoDeJornada, Nomina, Sueldo, Tasa, Asistencia, Usuarios, Liquidacion,Prestamo, ParametrosNomina, SueldoLabor, CodigoActivacionSuperuser
from django.utils import timezone
from datetime import date
from django.core.validators import RegexValidator
from django.contrib import admin
from django.contrib.auth.hashers import make_password

class SuperuserForm(forms.ModelForm):


    superuser_code = forms.CharField(
        required=False,
        widget=forms.PasswordInput(), # Recomendado para códigos sensibles
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
        """
        Método adaptado: Evalúa si el código ingresado es válido
        usando la función de validación que compara con el hash guardado.
        """
        code = self.cleaned_data.get('superuser_code')
        
        if code:
            if not CodigoActivacionSuperuser.validar_codigo(code):
                raise forms.ValidationError('Código de superusuario incorrecto.')
                
        # 2. Si es vacío, es válido (el usuario será normal).
        return code

    def clean(self):
        cleaned_data = super().clean()
        superuser_code = cleaned_data.get('superuser_code')
        cedula = cleaned_data.get('cedula')

        # Determinar si se está intentando crear un superusuario
        # Ahora se considera True si el código NO está vacío (ya que clean_superuser_code garantiza que si existe, es válido)
        is_creating_superuser = bool(superuser_code) 

        # --- Lógica de Validación de Cédula (NO SUPERUSUARIO) ---
        if not is_creating_superuser:
            if not cedula:
                self.add_error('cedula', 'La cédula es obligatoria para crear un usuario normal.')
            else:
                try:
                    # Asumiendo que cedula_validator se importa y funciona
                    # cedula_validator(cedula) 
                    
                    empleado = Empleado.objects.get(cedula=cedula)
                    if Usuarios.objects.filter(empleado=empleado).exists():
                        self.add_error('cedula', 'Esta cédula ya está asociada a otro usuario.')
                        
                    # Guardamos el objeto empleado para usarlo en save()
                    cleaned_data['empleado_obj'] = empleado 
                except Empleado.DoesNotExist:
                    self.add_error('cedula', 'No existe un empleado con la cédula proporcionada.')
                # except forms.ValidationError as e:
                #     self.add_error('cedula', e.message) # Descomentar si usas cedula_validator

        # --- Lógica de Validación de Cédula (SUPERUSUARIO) ---
        else:
            if cedula:
                self.add_error('cedula', 'La cédula debe dejarse vacía al crear un superusuario.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])

        # Determinamos si es superusuario basándonos en si el campo fue llenado (y validado)
        is_creating_superuser = bool(self.cleaned_data.get('superuser_code'))

        if is_creating_superuser:
            user.is_superuser = True
            user.is_staff = True
            # Limpiamos la cédula para el superusuario (si tu modelo la guarda)
            user.cedula = None 
        else:
            user.is_superuser = False
            user.is_staff = False
            # La cédula ya está asignada en el modelo User si es un campo ahí,
            # o se maneja con el objeto Empleado en el paso siguiente.

        if commit:
            user.save()

            if not is_creating_superuser:
                # CREACIÓN DEL OBJETO USUARIOS RELACIONADO CON EMPLEADO
                empleado = self.cleaned_data.get('empleado_obj') 
                if empleado:
                    # Asumiendo que 'Usuarios' es tu modelo de perfil extendido
                    Usuarios.objects.create(user=user, empleado=empleado, puesto='Usuario Empleado')

        return user
    
class FormularioCodigoActivacion(forms.ModelForm):
    codigo_nuevo = forms.CharField(
        label="Código de activación",
        widget=forms.PasswordInput(render_value=True),
        min_length=6,
        required=False,
        help_text="Este código permite crear superusuarios. Guárdalo en un lugar seguro."
    )
    confirmar = forms.CharField(
        label="Repetir código",
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    class Meta:
        model = CodigoActivacionSuperuser
        fields = []

    def clean(self):
        c1 = self.cleaned_data.get('codigo_nuevo')
        c2 = self.cleaned_data.get('confirmar')
        if c1 != c2:
            raise forms.ValidationError("Los códigos no coinciden")
        if c1 and len(c1) < 6:
            raise forms.ValidationError("El código debe tener mínimo 6 caracteres")
        return self.cleaned_data

    def save(self, commit=True):
        instancia = super().save(commit=False)
        if self.cleaned_data.get('codigo_nuevo'):
            instancia.codigo_hash = make_password(self.cleaned_data['codigo_nuevo'])
            instancia.activado = True
        if commit:
            instancia.save()
        return instancia

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
        fields = [
            'id_empleado', 
            'id_labor', 
            'id_tasa', 
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['id_tasa'].queryset = Tasa.objects.filter(activa=True)

        self.fields['id_empleado'].queryset = Empleado.objects.all().order_by('nombre')
        self.fields['id_empleado'].label_from_instance = lambda obj: f"{obj.nombre} {obj.apellido} ({obj.cedula})"

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
        fields = [
            'nombre_jornada', 
            'horas_diarias'  ]

class NominaForm(forms.ModelForm):
    class Meta:
        model = Nomina
        fields = [
            'id_empleado', 
            'id_sueldo', 
            'id_trabajo', 
            'periodo_inicio', 
            'periodo_fin',
            'tipo_periodo',
            
            'total_asignaciones_bs', 
            'total_deducciones_bs', 
            'sueldo_neto_bs'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance.pk: 
            self.fields['total_asignaciones_bs'].widget.attrs['readonly'] = 'readonly'
            self.fields['total_deducciones_bs'].widget.attrs['readonly'] = 'readonly'
            self.fields['sueldo_neto_bs'].widget.attrs['readonly'] = 'readonly'


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

    def clean(self):
        cleaned_data = super().clean()
        
        empleado = cleaned_data.get('id_empleado')
        fecha_asistencia = cleaned_data.get('fecha_asistencia')
        
        if empleado and fecha_asistencia:
            
            try:
                fecha_contratacion = empleado.fecha_contratacion
            except AttributeError:
                raise forms.ValidationError(
                    "Error interno: El modelo Empleado no tiene el campo 'fecha_contratacion'."
                )

            if fecha_asistencia < fecha_contratacion:
                
                raise forms.ValidationError(
                    f"La fecha de inasistencia ({fecha_asistencia.strftime('%d/%m/%Y')}) "
                    f"no puede ser anterior a la fecha de contratación del empleado "
                    f"({fecha_contratacion.strftime('%d/%m/%Y')})."
                )
                
        return cleaned_data
"""
Formulario para crear nuevos usuarios si es un superusuario o es un usuario normal

"""
""""""

from django import forms
from django.contrib.auth.models import User
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.exceptions import ValidationError
from .models import Empleado, Usuarios

class SuperuserForm(forms.ModelForm):
    superuser_code = forms.CharField(
        required=False,
        label="Código de activación",
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'placeholder': 'Opcional - solo para administradores'
        }),
        help_text="Código especial para crear superusuario. Déjelo vacío para usuario normal."
    )

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        min_length=8,
        help_text="Mínimo 8 caracteres"
    )

    cedula = forms.CharField(
        max_length=10,
        required=False,
        label="Cédula del empleado",
        help_text="Obligatoria para usuarios normales. Déjela vacía si crea un superusuario."
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'cedula']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'opcional@empresa.com'}),
        }

    def clean_superuser_code(self):
        code = self.cleaned_data.get('superuser_code', '').strip()
        if not code:
            return None  # No intenta crear superusuario

        signer = TimestampSigner()

        try:
            # El código debe ser válido y no haber expirado (48 horas máximo)
            signer.unsign(code, max_age=172800)  # 48 horas = 2 días
            return code
        except SignatureExpired:
            raise ValidationError("El código ha expirado. Solicite uno nuevo.")
        except BadSignature:
            raise ValidationError("Código inválido.")
        except Exception:
            raise ValidationError("Error al verificar el código.")

    def clean(self):
        cleaned_data = super().clean()
        superuser_code = cleaned_data.get('superuser_code')
        cedula = cleaned_data.get('cedula', '').strip()

        # Determina si se está intentando crear un superusuario
        is_creating_superuser = bool(superuser_code)

        if is_creating_superuser:
            if cedula:
                self.add_error('cedula', 'La cédula debe estar vacía al crear un superusuario.')
        else:
            # Es usuario normal → cédula obligatoria
            if not cedula:
                self.add_error('cedula', 'La cédula es obligatoria para usuarios normales.')
            else:
                try:
                    cedula_validator(cedula)
                    empleado = Empleado.objects.get(cedula=cedula)
                    if Usuarios.objects.filter(empleado=empleado).exists():
                        self.add_error('cedula', 'Este empleado ya tiene un usuario asociado.')
                    else:
                        cleaned_data['empleado_obj'] = empleado
                except Empleado.DoesNotExist:
                    self.add_error('cedula', 'No existe un empleado con esta cédula.')
                except ValidationError as e:
                    self.add_error('cedula', str(e))

        # Guardamos el flag para usarlo en save()
        cleaned_data['is_creating_superuser'] = is_creating_superuser
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])

        if self.cleaned_data['is_creating_superuser']:
            user.is_superuser = True
            user.is_staff = True
        else:
            user.is_superuser = False
            user.is_staff = False  # o True si quieres que acceda al admin

        if commit:
            user.save()

            # Solo crear relación con empleado si es usuario normal
            if not self.cleaned_data['is_creating_superuser']:
                empleado = self.cleaned_data.get('empleado_obj')
                if empleado:
                    Usuarios.objects.create(
                        user=user,
                        empleado=empleado,
                        puesto='Usuario Empleado'
                    )

        return user

class NominaGrupalForm(forms.Form):
    labor = forms.ModelChoiceField(
        queryset=Labor.objects.all(),
        label='Seleccionar Labor para Generar Nómina'
    )
    fecha_inicio = forms.DateField(
        label='Fecha de Inicio del Período',
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='Indique la fecha de inicio del período de 7 días (semanal).'
    )

class SueldoGrupalForm(forms.Form):
    labor = forms.ModelChoiceField(
        queryset=Labor.objects.all(), 
        label="Labor a la que aplica el sueldo"
    )
    
    jornada = forms.ModelChoiceField(
        queryset=TipoDeJornada.objects.all(), 
        label="Tipo de Jornada (Filtro de Empleado)"
    )
    
    tasa = forms.ModelChoiceField(
        queryset=Tasa.objects.filter(activa=True), 
        label="Tasa de Cambio (USD a Bs)"
    )

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


class ParametrosNominaForm(forms.ModelForm):
    """
    Formulario para crear o actualizar un Concepto/Regla de Nómina.
    """
    class Meta:
        model = ParametrosNomina
        fields = ['nombre', 'tipo', 'periodicidad', 'monto_fijo','monto_fijo_usd', 'porcentaje', 'es_concepto_fijo']
        
        widgets = {
            'monto_fijo': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'porcentaje': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '2'}), 
        }

        labels = {
            'nombre': 'Nombre del Concepto/Regla',
            'tipo': 'Tipo (Asignación o Deducción)',
            'periodicidad': 'Frecuencia de Aplicación',
            'monto_fijo_usd': 'Monto/Valor (Bs)',
            'monto_usd': 'Monto/Valor (USD)',
            'porcentaje': 'Porcentaje/Tasa (Ej: 0.05)',
            'es_concepto_fijo': 'Es una Tasa o Factor Fijo Global',
        }
    

    def clean_porcentaje(self):
        value = self.cleaned_data.get('porcentaje')
        if value is not None and (value < 0 or value > 2):
            raise forms.ValidationError("El porcentaje debe ser un valor entre 0 y 1 (ej. 0.04 para 4%).")
        return value
    


class SueldoLaborForm(forms.ModelForm):
    """
    Formulario para crear o actualizar el sueldo base semanal USD de un cargo (Labor).
    """
    class Meta:
        model = SueldoLabor
        fields = ['id_labor', 'sueldo_base_semanal_usd'] 
        
        widgets = {
            'sueldo_base_semanal_usd': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
        labels = {
            'id_labor': 'Cargo o Labor',
            'sueldo_base_semanal_usd': 'Sueldo Base Semanal (USD)',
        }
    
    def clean_id_labor(self):
        id_labor = self.cleaned_data.get('id_labor')
        if not self.instance.pk:
            if SueldoLabor.objects.filter(id_labor=id_labor).exists():
                raise forms.ValidationError("Ya existe un sueldo base en USD asignado para este Cargo/Labor.")
        return id_labor


