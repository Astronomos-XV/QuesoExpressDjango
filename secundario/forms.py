# forms.py  
from django import forms 
from django.contrib.auth.models import User  
from .models import Empleado, Departamento, Profesion, Labor, TipoDeJornada,Nomina, Sueldo, Tasa
from django.utils import timezone 

class EmpleadoForm(forms.ModelForm):  
    class Meta:  
        model = Empleado  
        fields = ['cedula','nombre', 'apellido', 'telefono', 'correo', 'fecha_contratacion', 'id_depa', 'id_pro', 'id_trabajo', 'id_jornada']  

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

class SuperuserForm(forms.ModelForm):
    
    is_superuser = forms.BooleanField(
        required=False,
        label='¿Es superusuario?'
    )
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):  
        user = super().save(commit=False)  
        user.set_password(self.cleaned_data['password'])  
        user.is_superuser = True
        user.is_staff = True
        if commit:  
            user.save()  
        return user  


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
        
        # Personaliza el campo id_empleado para mostrar nombre y apellido
        self.fields['id_empleado'].queryset = Empleado.objects.all().order_by('nombre')
        self.fields['id_empleado'].label_from_instance = lambda obj: f"{obj.nombre} {obj.apellido} ({obj.cedula})"
        
        # Agrega atributos data-horas a las opciones de jornada
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
            'id_empleado',
            'periodo',
            'sueldo_bs_base',
            'cestaticket_bs',
            'horas_extras',
            'pago_horas_extras_bs',
            'horas_festivas',
            'pago_horas_festivas_bs',
            'total_asignaciones_bs',
            'total_deducciones_bs',
            'sueldo_neto_bs',
            'fecha_emision'
        ]
        widgets = {
            'periodo': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'placeholder': 'DD/MM/AAAA'

           }),
            'fecha_emision': forms.DateInput(attrs={
                'type': 'date',
                'max': timezone.now().strftime('%Y-%m-%d')
            }),
            'sueldo_bs_base': forms.NumberInput(attrs={'step': '0.01'}),
            'cestaticket_bs': forms.NumberInput(attrs={'step': '0.01'}),
            'pago_horas_extras_bs': forms.NumberInput(attrs={'step': '0.01'}),
            'pago_horas_festivas_bs': forms.NumberInput(attrs={'step': '0.01'}),
            'total_asignaciones_bs': forms.NumberInput(attrs={'step': '0.01'}),
            'total_deducciones_bs': forms.NumberInput(attrs={'step': '0.01'}),
            'sueldo_neto_bs': forms.NumberInput(attrs={'step': '0.01'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
     
        self.fields['id_empleado'].queryset = Empleado.objects.all().order_by('nombre')
        self.fields['id_empleado'].label_from_instance = lambda obj: f"{obj.nombre} {obj.apellido} ({obj.cedula})"
        
    
        for field in ['horas_extras', 'horas_festivas']:
            self.fields[field].widget.attrs['min'] = '0'
        
        for field in self.fields:
            if 'bs' in field:
                self.fields[field].widget.attrs['min'] = '0.00'

class BuscarNominaForm(forms.Form):
    cedula = forms.CharField(
        label='Buscar nómina por cédula',
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: V-12345678',
            'class': 'form-control'
        })
    )