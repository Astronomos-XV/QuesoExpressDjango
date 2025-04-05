from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required,user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .models import Empleado,  Tasa, Nomina, Sueldo, TipoDeJornada, Departamento, Profesion, Labor, TipoDeJornada
from .forms import EmpleadoForm, SueldoForm, SuperuserForm, DepartamentoForm, ProfesionForm, LaborForm, TipoDeJornadaForm, NominaForm, BuscarNominaForm   # Asumiré que tienes un forms.py
from django.contrib import messages
from datetime import datetime
import requests

def es_superusuario(user):
    return user.is_superuser  

@user_passes_test(es_superusuario, login_url='pagina_no_autorizada')  
def vista_empleado(request):
    return render(request, 'empleadopagina.html')  




def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    
                    if user.is_superuser:
                        return render(request, 'home.html')  
                    else:
                        return render(request, 'empleadopagina.html')  
                else:
                    messages.error(request, "Tu cuenta está inactiva.")
            else:
                messages.error(request, "Usuario o contraseña incorrectos.")
        else:
            messages.error(request, "Error en el formulario.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})


@login_required
def listar_empleados(request):
    empleados = Empleado.objects.all()
    return render(request, 'empleados.html', {'empleados': empleados})


@login_required
def crear_empleado(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_empleados')
    else:
        form = EmpleadoForm()
    return render(request, 'formulario.html', {'form': form})


@login_required
def editar_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id_empleado=empleado_id)
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            return redirect('listar_empleados')
    else:
        form = EmpleadoForm(instance=empleado)
    return render(request, 'formulario.html', {'form': form})


@login_required
def eliminar_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id_empleado=empleado_id)
    empleado.delete()
    return redirect('listar_empleados')


@login_required

def home(request):
     nominas = Nomina.objects.all()
     return render(request, 'home.html', {'nominas': nominas})


@login_required
def sueldo_list(request):
    sueldos = Sueldo.objects.all().select_related('id_empleado', 'id_tasa', 'id_jornada')
    return render(request, 'sueldo_lista.html', {'sueldos': sueldos})


def actualizar_tasa():
    url = "https://ve.dolarapi.com/v1/dolares/oficial"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        promedio = data.get("promedio")
        fecha_actualizacion = data.get("fechaActualizacion")

        if promedio and fecha_actualizacion:
            fecha = datetime.strptime(fecha_actualizacion[:10], "%Y-%m-%d").date()

            
            tasa_existente = Tasa.objects.filter(fecha=fecha).first()

            if tasa_existente:
                tasa_existente.valor_tasa = promedio
                tasa_existente.save()
            else:
                Tasa.objects.create(fecha=fecha, valor_tasa=promedio, activa=True)

def actualizar_y_listar_tasas(request):
    actualizar_tasa()
    tasas = Tasa.objects.all()
    return render(request, 'tasa.html', {'tasas': tasas})


@login_required
def nomina_create(request):
    if request.method == 'POST':
        
        id_empleado = request.POST.get('id_empleado')
        id_sueldo = request.POST.get('id_sueldo')
        periodo = request.POST.get('periodo')
        sueldo_bs_base = request.POST.get('sueldo_bs_base')
        cestaticket_bs = request.POST.get('cestaticket_bs')
        horas_extras = request.POST.get('horas_extras', 0)
        horas_ordinarias = request.POST.get('horas_ordinarias')
        pago_horas_extras_bs = request.POST.get('pago_horas_extras_bs')
        horas_festivas = request.POST.get('horas_festivas', 0)
        pago_horas_festivas_bs = request.POST.get('pago_horas_festivas_bs')
        dias_vacaciones = request.POST.get('dias_vacaciones', 0)
        dias_enfermedad = request.POST.get('dias_enfermedad', 0)
        total_asignaciones_bs = request.POST.get('total_asignaciones_bs')
        ivss_bs = request.POST.get('ivss_bs')
        rpe_bs = request.POST.get('rpe_bs')
        faov_bs = request.POST.get('faov_bs')
        total_deducciones_bs = request.POST.get('total_deducciones_bs')
        sueldo_neto_bs = request.POST.get('sueldo_neto_bs')
        fecha_emision = request.POST.get('fecha_emision')

        nomina = Nomina(
            id_empleado_id=id_empleado,
            id_sueldo_id=id_sueldo,
            periodo=periodo,
            sueldo_bs_base=sueldo_bs_base,
            cestaticket_bs=cestaticket_bs,
            horas_extras=horas_extras,
            horas_ordinarias=horas_ordinarias,
            pago_horas_extras_bs=pago_horas_extras_bs,
            horas_festivas=horas_festivas,
            pago_horas_festivas_bs=pago_horas_festivas_bs,
            dias_vacaciones=dias_vacaciones,
            dias_enfermedad=dias_enfermedad,
            total_asignaciones_bs=total_asignaciones_bs,
            ivss_bs=ivss_bs,
            rpe_bs=rpe_bs,
            faov_bs=faov_bs,
            total_deducciones_bs=total_deducciones_bs,
            sueldo_neto_bs=sueldo_neto_bs,
            fecha_emision=fecha_emision
        )
        nomina.save()
        return redirect('home')
    empleados = Empleado.objects.all()
    sueldos = Sueldo.objects.all() 
    return render(request, 'crear_nomina.html', {'empleados': empleados, 'sueldos': sueldos}) 


@login_required
def sueldo_create(request):
    if request.method == 'POST':
        form = SueldoForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                return redirect('sueldo_lista')
            except Exception as e:
                print(f"Error al guardar: {e}")  
    else:
        form = SueldoForm()
    
    
    if not Empleado.objects.exists() or not TipoDeJornada.objects.exists() or not Tasa.objects.filter(activa=True).exists():
        messages.warning(request, "Faltan datos necesarios (Empleados, Jornadas o Tasas activas)")
    
    return render(request, 'sueldo_creacion.html', {
        'form': form,
        'empleados': Empleado.objects.all(),
        'jornadas': TipoDeJornada.objects.all(),
        'tasas': Tasa.objects.filter(activa=True)
    })



def cerrar_sesion(request):
    logout(request)
    return redirect('login')


def crear_superuser(request):
    if request.method == 'POST':
        form = SuperuserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_superuser = form.cleaned_data['is_superuser']
            user.is_staff = form.cleaned_data['is_superuser']
            user.save()
            return redirect('login')
    else:
        form = SuperuserForm()
    return render(request, 'registrarusuario.html', {'form': form})



@login_required
def sueldo_lista(request):
    sueldos = Sueldo.objects.all()
    return render(request, 'sueldo_lista.html', {'sueldos': sueldos})

@login_required
def sueldo_lista(request):
    sueldos = Sueldo.objects.all()
    return render(request, 'sueldo_lista.html', {'sueldos': sueldos})

@login_required
def sueldo_editar(request, id_sueldo):
    sueldo = get_object_or_404(Sueldo, id_sueldo=id_sueldo)
    
    if request.method == 'POST':
        form = SueldoForm(request.POST, instance=sueldo)
        if form.is_valid():
            form.save()
            return redirect('sueldo_lista')
    else:
        form = SueldoForm(instance=sueldo)
    
    return render(request, 'sueldo_form.html', {'form': form})

@login_required
def sueldo_eliminar(request, id_sueldo):
    sueldo = get_object_or_404(Sueldo, id_sueldo=id_sueldo)
    
    if request.method == 'POST':
        sueldo.delete()
        return redirect('sueldo_lista')
    
    return render(request, 'sueldo_confirmar_eliminar.html', {'sueldo': sueldo})


def gestion_datos(request):

    departamentos = Departamento.objects.all()
    profesiones = Profesion.objects.all()
    labores = Labor.objects.all()
    jornadas = TipoDeJornada.objects.all()
    
    form_type = request.GET.get('form', None)
    form = None
    obj = None
    
    if request.method == 'POST':
 
        post_data = request.POST.copy()
        

        if 'departamento' in post_data:
            pk = post_data.get('id_depa', None)
            if pk and pk != '': 
                obj = get_object_or_404(Departamento, pk=pk)
                form = DepartamentoForm(post_data, instance=obj)
            else: 

                post_data.pop('id_depa', None)
                form = DepartamentoForm(post_data)
            
            if form.is_valid():
                form.save()
                return redirect('gestion_datos')
                
        elif 'profesion' in post_data:
            pk = post_data.get('id_pro', None)
            if pk and pk != '':
                obj = get_object_or_404(Profesion, pk=pk)
                form = ProfesionForm(post_data, instance=obj)
            else:
                post_data.pop('id_pro', None)
                form = ProfesionForm(post_data)
            
            if form.is_valid():
                form.save()
                return redirect('gestion_datos')
                
        elif 'labor' in post_data:
            pk = post_data.get('id_trabajo', None)
            if pk and pk != '':
                obj = get_object_or_404(Labor, pk=pk)
                form = LaborForm(post_data, instance=obj)
            else:
                post_data.pop('id_trabajo', None)
                form = LaborForm(post_data)
            
            if form.is_valid():
                form.save()
                return redirect('gestion_datos')
                

        elif 'jornada' in post_data:
            pk = post_data.get('id_jornada', None)
            if pk and pk != '':
                obj = get_object_or_404(TipoDeJornada, pk=pk)
                form = TipoDeJornadaForm(post_data, instance=obj)
            else:
                post_data.pop('id_trabajo', None)
                form = TipoDeJornadaForm(post_data)
            
            if form.is_valid():
                form.save()
                return redirect('gestion_datos')
            
    else:
        
        edit_id = request.GET.get('edit', None)
        delete_id = request.GET.get('delete', None)
        model_type = request.GET.get('type', None)
        
        if edit_id and model_type:
            if model_type == 'departamento':
                obj = get_object_or_404(Departamento, pk=edit_id)
                form = DepartamentoForm(instance=obj)
            elif model_type == 'profesion':
                obj = get_object_or_404(Profesion, pk=edit_id)
                form = ProfesionForm(instance=obj)
            elif model_type == 'labor':
                obj = get_object_or_404(Labor, pk=edit_id)
                form = LaborForm(instance=obj)
            elif model_type == 'jornada':
                obj = get_object_or_404(TipoDeJornada, pk=edit_id)
                form = TipoDeJornadaForm(instance=obj)
        elif delete_id and model_type:
            if model_type == 'departamento':
                obj = get_object_or_404(Departamento, pk=delete_id)
                obj.delete()
            elif model_type == 'profesion':
                obj = get_object_or_404(Profesion, pk=delete_id)
                obj.delete()
            elif model_type == 'labor':
                obj = get_object_or_404(Labor, pk=delete_id)
                obj.delete()
            elif model_type == 'jornada':
                obj = get_object_or_404(TipoDeJornada, pk=delete_id)
                obj.delete()
            return redirect('gestion_datos')
        

        if form is None:
            if form_type == 'departamento':
                form = DepartamentoForm()
            elif form_type == 'profesion':
                form = ProfesionForm()
            elif form_type == 'labor':
                form = LaborForm()
            elif form_type == 'jornada':
                form = TipoDeJornadaForm()
    
    context = {
        'departamentos': departamentos,
        'profesiones': profesiones,
        'labores': labores,
        'jornadas': jornadas,
        'form': form,
        'form_type': form_type,
        'obj': obj,
    }
    return render(request, 'gestion_datos.html', context)


def editar_nomina(request, id_nomina):
    nomina = get_object_or_404(Nomina, pk=id_nomina)
    if request.method == 'POST':
        form = NominaForm(request.POST, instance=nomina)
        if form.is_valid():
            form.save()
            return render(request, 'home.html')
    else:
        form = NominaForm(instance=nomina)
    return render(request, 'editar_nomina.html', {'form': form})

def eliminar_nomina(request, id_nomina):
    nomina = get_object_or_404(Nomina, pk=id_nomina)
    if request.method == 'POST':
        nomina.delete()
        return render(request, 'home.html')
    return render(request, 'eliminar_nomina.html', {'nomina': nomina})


def buscar_nomina(request):
    nominas = []
    cedula = ""
    
    if request.method == 'POST':
        form = BuscarNominaForm(request.POST)
        if form.is_valid():
            cedula = form.cleaned_data['cedula']
            empleados = Empleado.objects.filter(cedula__icontains=cedula)
            nominas = Nomina.objects.filter(id_empleado__in=empleados)
    else:
        form = BuscarNominaForm()
    
    return render(request, 'buscar_nomina.html', {
        'form': form,
        'nominas': nominas,
        'cedula_buscada': cedula
    })