
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required,user_passes_test
from functools import wraps
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User, Group
from django.db import transaction 
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Empleado,  Tasa, Nomina, Sueldo, TipoDeJornada, Departamento, Profesion, Labor, TipoDeJornada, Asistencia, Asistenciaconfirmada, Usuarios, PrestacionSocialAcumulada,  Liquidacion, Prestamo,ConceptoNomina,ParametrosNomina, SueldoLabor, CambioLabor, BonoExtra, ParametrosNomina, DetalleConceptoNomina, CodigoActivacionSuperuser
from .forms import EmpleadoForm, SueldoForm, SuperuserForm, DepartamentoForm, ProfesionForm, LaborForm, TipoDeJornadaForm, NominaForm, BuscarNominaForm, AsistenciaForm, NominaGrupalForm, SueldoGrupalForm, LiquidacionGrupalForm, LiquidacionForm,PrestamoForm, ParametrosNominaForm, SueldoLaborForm, NominaDepartamentalForm
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib import messages
import datetime as dt_mod  
from datetime import timedelta
from datetime import datetime, timedelta, date, time
from django.views.generic import ListView
from django.utils import timezone
from django.db.models import Q,Sum,Count
import requests
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date
import datetime
from dateutil.relativedelta import relativedelta
from django.core.serializers import serialize
import json,base64,urllib.parse,io
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import calendar

VENEZUELAN_HOLIDAYS = [
    (1, 1),    
    (1, 6),    
    (2, 12),   
    (3, 19),   
    (4, 19),   
    (5, 1),    
    (6, 24),   
    (7, 5),    
    (7, 24),   
    (10, 12),  
    (12, 24),  
    (12, 25),  
    (12, 31),  
]
"""
def check_user_able_to_see_page(*groups):
    return user_passes_test(
        lambda user: user.groups.filter(name__in=groups).exists()
    ) """

def is_holiday(date_obj):
    """
    Verifica si una fecha es un día festivo nacional en Venezuela.
    """
    if date_obj.weekday() == calendar.SUNDAY: 
        return True
    
   
    if (date_obj.month, date_obj.day) in VENEZUELAN_HOLIDAYS:
        return True
    
    

    return False

"""
Logica relacionada con la autenticación de usuarios, incluyendo inicio de sesion, cierre de sesion y creación de superusuarios.
"""
"""

def es_contador(user):
    
    imprimir = user.groups.filter(name__iexact='contador').exists()
    
    if not imprimir: 
        redirect('error_grupo')
        

    return imprimir


def es_admin(user):
    
    imprimir = user.groups.filter(name__iexact='administrador').exists()
    
    if not imprimir: 
        redirect('error_grupo')

    return imprimir
"""


def es_contador(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión.")
            return redirect('login')  
        
        if not request.user.groups.filter(name__iexact='contador').exists():
            messages.error(request, "Acceso denegado: No posees acceso")
            return redirect('error_grupo')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def es_root(view_func):
    @wraps(view_func)


    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión.")
            return redirect('login')  
        
        if not request.user.groups.filter(name__iexact='root').exists():
            messages.error(request, "Acceso denegado: No perteneces al grupo de maestros")
            return redirect('error_grupo')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def es_admin(view_func):
    @wraps(view_func)



    

    def wrapper(request, *args, **kwargs):
        admin = request.user.groups.filter(name__iexact='administrador').exists()
        root = request.user.groups.filter(name__iexact='root').exists()
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión.")
            return redirect('login')  
        
        if not (admin or root):
            messages.error(request, "Acceso denegado: No tienes acceso a esta area")
            return redirect('error_grupo')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def es_admin_o_contador(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        contador = request.user.groups.filter(name__iexact='contador').exists()
        administrador = request.user.groups.filter(name__iexact='administrador').exists()
        root = request.user.groups.filter(name__iexact='root').exists()
        login = request.user.is_authenticated
        if not login:
            messages.error(request, "Debes iniciar sesión.")
            print(f"Login es {login}")
            return redirect('login')
        
        if not (contador or administrador or root):
            messages.error(request, "Acceso denegado")
            print(f"Tienes que ser {administrador} o {contador} ")
            return redirect('error_grupo')
        


        
        return view_func(request, *args, **kwargs)
    return wrapper


def error_grupo(request):
    """
    Pantalla de error para grupo sin permiso
    """
    return render(request, 'sinacceso.html')   


def vista_empleado(request):
    """
    Vista para la página de empleados, accesible solo por superusuarios.
    """
    return render(request, 'registrar_asistencia_diaria.html')  


def cerrar_sesion(request):
    """
    Cierra la sesión del usuario actual y redirige a la página de inicio de sesión.
    """
    logout(request)
    return redirect('login')


def login_view(request):
    """
    Maneja el inicio de sesión de usuarios, autenticando credenciales y redirigiendo
    según el tipo de usuario (administrador o empleado).
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)


            administrador=user.groups.filter(name__iexact='administrador').exists() 

            root=user.groups.filter(name__iexact='root').exists()

            contador=user.groups.filter(name__iexact='contador').exists()

            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    if contador or administrador or root:
                        print(f" root {root}")
                        print(f"Admin {administrador}")
                        print(f"Contador {contador}")
                        return render(request, 'home.html')  
                    else:
                        return render(request, 'empleadopaginapre.html')  
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
#@user_passes_test(es_admin, login_url='home')
@es_root
def crear_superuser(request):
    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip()
        username = request.POST.get("username")
        password = request.POST.get("password")

        if CodigoActivacionSuperuser.validar_codigo(codigo):
            try:
                # Antes superusuario
                user = User.objects.create_superuser(username=username, password=password)
                
                grupo_admin = Group.objects.get(name__iexact='root')
                #user.is_staff = True
                #para agregar usuarios de tipo admin
                user.groups.add(grupo_admin)
                
                messages.success(request, f"¡Superusuario {username} creado y añadido al grupo Administrador con éxito!")
                return redirect("home")
            
            except Group.DoesNotExist:
                
                user.delete() 
                messages.error(request, "Error interno: No se pudo encontrar el grupo 'Administrador'.")
                return render(request, "registrarusuario.html") 
            
        else:
            messages.error(request, "Código incorrecto")
    
    return render(request, "registrarusuario.html")


@login_required
#@user_passes_test(es_admin, login_url='home')

@es_root
@transaction.atomic
def crear_usuario_normal(request):
    if request.method == "POST":
        cedula = request.POST.get("cedula").strip()
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            empleado = Empleado.objects.get(cedula=cedula)

        except Empleado.DoesNotExist:
            messages.error(request, "No existe empleado con esa cédula")
            return render(request, "crear_usuario_normal.html")

        if Usuarios.objects.filter(empleado=empleado).exists():
            
            messages.error(request, "Este empleado ya tiene usuario")
            return render(request, "crear_usuario_normal.html")

        user = User.objects.create_user(username=username, password=password)
        user.is_staff = False
        user.save()

        Usuarios.objects.create(user=user, empleado=empleado)
        grupo_empleado = Group.objects.get(name__iexact='empleado')
        user.groups.add(grupo_empleado)

        messages.success(request, f"Usuario '{username}' creado correctamente")
        return redirect("home")

    return render(request, "crear_usuario_normal.html")


"""
Todo lo relacionado a empleado(Listar, Crear, Eliminar y Actualizar)
"""
@login_required

@es_admin
def listar_empleados(request):
    """
    Muestra un listado paginado de todos los empleados.
    """
    empleados_list = Empleado.objects.all().order_by('apellido', 'nombre') 

    paginator = Paginator(empleados_list, 5)  

    page_number = request.GET.get('page')
    try:
        empleados = paginator.page(page_number)
    except PageNotAnInteger:
        empleados = paginator.page(1)
    except EmptyPage:
        empleados = paginator.page(paginator.num_pages)

    return render(request, 'empleados.html', {'empleados': empleados})

@login_required
#@user_passes_test(es_admin, login_url='home')
@es_admin
def crear_empleado(request):
    """
    Permite crear un nuevo registro de empleado.
    """
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_empleados')
    else:
        form = EmpleadoForm()
    return render(request, 'formulario.html', {'form': form})


@login_required
#@user_passes_test(es_admin, login_url='home')
@es_admin

def editar_empleado(request, empleado_id):
    """
    Permite editar un registro existente de empleado y registra el cambio de Labor si ocurre.
    """
    empleado = get_object_or_404(Empleado, id_empleado=empleado_id)
    
    labor_anterior = empleado.id_trabajo 
    
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        
        if form.is_valid():
            
            empleado_actualizado = form.save()

            print(empleado_actualizado)
            
            if empleado_actualizado.id_trabajo != labor_anterior:
                
                CambioLabor.objects.create(
                    id_empleado=empleado_actualizado,
                    labor_anterior=labor_anterior,
                    labor_nueva=empleado_actualizado.id_trabajo,
                    motivo=f"Cambio de Labor registrado automáticamente: De '{labor_anterior.nombre_trabajo}' a '{empleado_actualizado.id_trabajo.nombre_trabajo}'."
                )
                messages.info(request, f"Se registró el cambio de Labor para {empleado.nombre}: {labor_anterior.nombre_trabajo} -> {empleado_actualizado.id_trabajo.nombre_trabajo}.")

                print(empleado_actualizado)
                
            messages.success(request, f"Empleado {empleado.nombre} {empleado.apellido} actualizado exitosamente.")
            return redirect('listar_empleados')
        
        else:
            messages.error(request, "Error al guardar el formulario. Por favor, revise los datos ingresados.")
            
    else:
        form = EmpleadoForm(instance=empleado)
        
    return render(request, 'formulario.html', {'form': form, 'empleado': empleado})


@login_required
@es_admin
def eliminar_empleado(request, empleado_id):
    """
    Elimina un registro de empleado.
    """
    empleado = get_object_or_404(Empleado, id_empleado=empleado_id)
    empleado.delete()
    return redirect('listar_empleados')


"""
Vista principal del sistema, mostrando un listado de nóminas, accesible solo para superusuarios(administradores)
"""
@login_required



@es_admin_o_contador
def home(request):
    """
    Muestra un listado paginado de nóminas, con opciones de filtrado por cédula y nombre/apellido del empleado.
    """
    
    # Busquedad de Cedula
    cedula = request.GET.get('cedula')
    nombre = request.GET.get('nombre')
    page = request.GET.get('page', 1)

    
    nominas_list = Nomina.objects.all().select_related('id_empleado').order_by(
        '-fecha_creacion',  
        'id_nomina'
    )

    
    if cedula:
        nominas_list = nominas_list.filter(id_empleado__cedula__icontains=cedula)
        
    if nombre:
        nominas_list = nominas_list.filter(
            Q(id_empleado__nombre__icontains=nombre) |
            Q(id_empleado__apellido__icontains=nombre)
        )
# Paginador
    items_por_pagina = 4 
    paginator = Paginator(nominas_list, items_por_pagina)

    try:
        nominas_paginadas = paginator.page(page)
    except PageNotAnInteger:
        nominas_paginadas = paginator.page(1)
    except EmptyPage:
        nominas_paginadas = paginator.page(paginator.num_pages)
    
    context = {
        'nominas': nominas_paginadas,
        'filtros': {
            'cedula': cedula or '',
            'nombre': nombre or '',
        }
    }

    # 7. Renderizar el template
    return render(request, 'home.html', context)




"""
Gestión de sueldos: listado, creación individual y grupal, edición y eliminación de registros de sueldos.
También incluye la lógica para actualizar la tasa de cambio.
"""
@login_required
@es_admin_o_contador
def sueldo_list(request):
    """
    Muestra un listado de todos los sueldos registrados.
    """
    sueldos = Sueldo.objects.all().select_related('id_empleado', 'id_tasa')
    return render(request, 'sueldo_lista.html', {'sueldos': sueldos})

def actualizar_tasa():
    """
    Consulta una API externa para obtener la tasa de cambio del dólar y la actualiza
    o crea en el modelo Tasa.
    """
    url = "https://ve.dolarapi.com/v1/dolares/oficial"
    try:
        response = requests.get(url)
        print(f"Estado de la respuesta de la API: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Respuesta JSON COMPLETA de la API: {data}")
                promedio = data.get("promedio")
                fecha_actualizacion = data.get("fechaActualizacion")

                if promedio is not None and fecha_actualizacion is not None:
                    fecha = datetime.datetime.strptime(fecha_actualizacion[:10], "%Y-%m-%d").date()
                    
                    tasa_existente = Tasa.objects.filter(fecha=fecha).first()

                    if tasa_existente:
                        tasa_existente.valor_tasa = promedio
                        tasa_existente.save()
                        return True, "Tasa actualizada correctamente"
                    else:
                        Tasa.objects.create(fecha=fecha, valor_tasa=promedio, activa=True)
                        return True, "Tasa creada correctamente"
                else:
                    return False, "Datos incompletos (promedio o fecha_actualizacion) en la respuesta de la API"
            except requests.exceptions.JSONDecodeError:
                print(f"Error: La respuesta de la API no es un JSON válido: {response.text}")
                return False, "La API devolvió una respuesta no JSON"
        
        elif response.status_code != 200:
            return False, f"Error al consultar la API: Código {response.status_code}"
        
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión a la API: {str(e)}") 
        return False, f"Error de conexión: {str(e)}"

@login_required
def actualizar_y_listar_tasas(request):
    """
    Ejecuta la actualización de la tasa de cambio y luego lista todas las tasas registradas.
    """
    success, message = actualizar_tasa() 
    tasas = Tasa.objects.all()
    
    return render(request, 'tasa.html', {
        'tasas': tasas,
        'message': message,
        'success': success
    })

@login_required
@es_admin_o_contador
def sueldo_create(request):
    if request.method == 'POST':
        form = SueldoForm(request.POST)
        if form.is_valid():
            print("--- Formulario VÁLIDO ---")
            nuevo_sueldo = form.save(commit=False)
            labor_seleccionada = nuevo_sueldo.id_labor
            tasa = nuevo_sueldo.id_tasa
            print(f"Labor: {labor_seleccionada}, Tasa: {tasa}")
            
            sueldo_labor_obj = SueldoLabor.objects.filter(id_labor=labor_seleccionada).first()
            
            if sueldo_labor_obj:
                print("--- SueldoLabor ENCONTRADO ---")
                sueldo_base_usd = sueldo_labor_obj.sueldo_base_semanal_usd
                
                if tasa:
                    print(f"--- Tasa ENCONTRADA. Sueldo base: {sueldo_base_usd} ---")
                 
                    nuevo_sueldo.save()
                    print("--- REGISTRO GUARDADO ---")
                    return redirect('sueldo_lista')
                else:
                    print("--- ERROR: Tasa no encontrada ---")
            else:
                print("--- ERROR: SueldoLabor no encontrado ---")

            return render(request, 'sueldo_creacion.html', {'form': form})
        else:
            print("--- ERROR: Formulario INVÁLIDO ---")
            print(form.errors) 
            return render(request, 'sueldo_creacion.html', {'form': form})

@login_required
@es_admin_o_contador
def generar_sueldo_grupal(request):
    """
    Genera o actualiza sueldos de forma grupal para empleados filtrados por labor y jornada.
    """
    if request.method == 'POST':
        print("--- Entrando a generar_sueldo_grupal (POST) ---")
        form = SueldoGrupalForm(request.POST)
        if form.is_valid():
            selected_labor = form.cleaned_data['labor']
            selected_jornada = form.cleaned_data['jornada']
            selected_tasa = form.cleaned_data['tasa']

            empleados_en_labor = Empleado.objects.filter(
                id_trabajo=selected_labor,
                id_jornada=selected_jornada 
            )
            
            sueldos_generados = []
            errores_generacion = []

            if not empleados_en_labor.exists():
                messages.warning(request, f"No se encontraron empleados para la labor '{selected_labor.nombre_trabajo}' y jornada '{selected_jornada.nombre_jornada}'.")
                return render(request, 'generar_sueldo_grupal.html', {'form': form})

            for empleado in empleados_en_labor:
                try:
                    existing_sueldo = Sueldo.objects.filter(
                        id_empleado=empleado,
                        id_labor=selected_labor, 
                        id_tasa=selected_tasa
                    ).first()

                    if existing_sueldo:
                        existing_sueldo.save() 
                        sueldos_generados.append(f"Sueldo actualizado para {empleado.nombre} {empleado.apellido}")
                        messages.info(request, f"Sueldo actualizado para {empleado.nombre} {empleado.apellido} (ya existía).")
                    else:
                        sueldo = Sueldo(
                            id_empleado=empleado,
                            id_labor=selected_labor, 
                            id_tasa=selected_tasa
                        )
                        sueldo.save() 
                        sueldos_generados.append(f"Sueldo generado para {empleado.nombre} {empleado.apellido}.")
                        messages.success(request, f"Sueldo generado para {empleado.nombre} {empleado.apellido}.")

                except Exception as e:
                    error_msg = f"Error al generar/actualizar sueldo para {empleado.nombre} {empleado.apellido}: {e}"
                    messages.error(request, error_msg)
                    errores_generacion.append(error_msg)


            return render(request, 'sueldo_grupal_resultado.html', { 
                 'sueldos_generados': sueldos_generados, 
                 'errores_generacion': errores_generacion 
            }) 
            
        else:
            messages.error(request, 'Error en el formulario de generación grupal. Por favor, revise los datos.')
            return render(request, 'generar_sueldo_grupal.html', {'form': form})
            
    else:
        form = SueldoGrupalForm()
        return render(request, 'generar_sueldo_grupal.html', {'form': form})

@login_required
@es_admin_o_contador
def sueldo_lista(request):
    """
    Muestra un listado de todos los sueldos registrados (duplicado de sueldo_list, se puede refactorizar).
    """
    sueldos = Sueldo.objects.all()
    return render(request, 'sueldo_lista.html', {'sueldos': sueldos})

@login_required
@es_admin
def sueldo_editar(request, id_sueldo):
    """
    Permite editar un registro de sueldo existente.
    """
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
@es_admin
def sueldo_eliminar(request, id_sueldo):
    """
    Elimina un registro de sueldo.
    """
    sueldo = get_object_or_404(Sueldo, id_sueldo=id_sueldo)
    
    if request.method == 'POST':
        sueldo.delete()
        return redirect('sueldo_lista')
    
    return render(request, 'sueldo_confirmar_eliminar.html', {'sueldo': sueldo})

"""
Gestiona exclusivamente todo lo relacionado a departamentos profesiones labores y jornadas Un Crud unificado para los 4
"""
@login_required
@es_admin
def gestion_datos(request):
    """
    Gestiona la creación, edición y eliminación de Departamentos, Profesiones, Labores y Tipos de Jornada
    a través de un único formulario y vista.
    """
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

"""
Busquedad de nomina por numero de cedula del empleado(Se autocompleta por la cedula del empleado registrado)
"""
@login_required
@es_admin_o_contador
def ver_concepto_nomina(request, pk):
    """
    Muestra los detalles de asignaciones y deducciones para una nómina específica.
    """
    nomina = get_object_or_404(Nomina, pk=pk)
    concepto = get_object_or_404(ConceptoNomina, id_nomina=nomina)
    detalles_personalizados = DetalleConceptoNomina.objects.filter(id_nomina=nomina)
    
    context = {
        'nomina': nomina,
        'concepto': concepto,
        'detalles_personalizados': detalles_personalizados,
        'titulo': f'Detalles de Nómina para {nomina.id_empleado.nombre} {nomina.id_empleado.apellido}'
    }
    return render(request, 'ver_concepto_nomina.html', context)

@login_required
def buscar_nomina(request):
    """
    Permite buscar nóminas por número de cédula de empleado.
    Si el usuario logeado es un empleado, muestra automáticamente sus nóminas.
    La tabla de nóminas ahora está paginada.
    """
    nominas_list = []
    cedula_buscada = ""
    form = None #


    if hasattr(request.user, 'usuarios') and request.user.usuarios.empleado:
        empleado = request.user.usuarios.empleado
        cedula_buscada = empleado.cedula
        nominas_list = Nomina.objects.filter(id_empleado=empleado).order_by('-fecha_emision')

    else:
        if request.method == 'POST':
            form = BuscarNominaForm(request.POST)
            if form.is_valid():
                cedula_buscada = form.cleaned_data['cedula']
                empleados = Empleado.objects.filter(cedula__icontains=cedula_buscada)
                nominas_list = Nomina.objects.filter(id_empleado__in=empleados).order_by('-fecha_emision')
          
            
        else:
            form = BuscarNominaForm()
 


    items_per_page = 2

    paginator = Paginator(nominas_list, items_per_page)
    page = request.GET.get('page')

    try:
        nominas = paginator.page(page)
    except PageNotAnInteger:
       
        nominas = paginator.page(1)
    except EmptyPage:
        
        nominas = paginator.page(paginator.num_pages)
   
            
    return render(request, 'buscar_nomina.html', {
        'nominas': nominas, 
        'cedula_buscada': cedula_buscada,
        'form': form, 
    })

"""
Exportacion de la nomina a pdf
"""
@login_required
@es_admin_o_contador
def exportar_nomina_pdf(request, id_nomina):
    nomina = None
    concepto = None 
    conceptos_nomina = [] 
    
    try:
        
        nomina = get_object_or_404(Nomina.objects.select_related('id_empleado'), pk=id_nomina) 
        
        
        concepto = ConceptoNomina.objects.get(id_nomina=nomina)
        
        conceptos_nomina = [concepto] 
        
    except ConceptoNomina.DoesNotExist:
        messages.error(request, f"Error: La Nómina N° {id_nomina} existe, pero no tiene Conceptos de Nómina asociados.")
        return redirect('buscar_nomina')
    except Exception as e:
        print(f"Error al cargar la información para el PDF: {e}")
        messages.error(request, f"Error grave al cargar los datos de la nómina. Verifique si el campo 'id_empleado' existe en su modelo Nomina.")
        return redirect('buscar_nomina')

    context = {
        'nomina': nomina,
        'conceptos_nomina': conceptos_nomina,
        'fecha_generacion': timezone.now().date(),
        'titulo': f'Recibo de Nómina N°{nomina.id_nomina}',
    }
    
    template = get_template('exportar_nomina_pdf.html') 
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    filename = f"Recibo_Nomina_{nomina.id_nomina}_{nomina.id_empleado.apellido}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    pisa_status = pisa.CreatePDF(
        html, 
        dest=response,
    )

    if pisa_status.err:
        return HttpResponse('<h1>Error al generar el PDF</h1><p>Revise la plantilla HTML.</p>')
        
    return response

"""
CRUD para inasistencias
elimina, actualiza, crea y lee datos para inasistencias
"""
@login_required
@es_admin_o_contador
def inasistencia_list(request):
    """
    Muestra un listado paginado de todas las inasistencias registradas.
    """
    inasistencias_list = Asistencia.objects.filter(asistio=False).order_by('-fecha_asistencia')
    
    paginator = Paginator(inasistencias_list, 4)  

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inasistencia_list.html', {'page_obj': page_obj})

@login_required
@es_admin
def inasistencia_create(request):
    """
    Permite registrar una nueva inasistencia para un empleado.
    """
    if request.method == 'POST':
        form = AsistenciaForm(request.POST)
        if form.is_valid():
            inasistencia = form.save(commit=False)
            inasistencia.asistio = False
            inasistencia.save()
            messages.success(request, 'Inasistencia registrada exitosamente.')
            return redirect('inasistencia_list')
    else:
        form = AsistenciaForm()
    return render(request, 'inasistencia_form.html', {'form': form, 'action': 'Crear'})

@login_required
@es_admin
def inasistencia_edit(request, id_asistencia):
    """
    Permite editar un registro de inasistencia existente.
    """
    inasistencia = get_object_or_404(Asistencia, pk=id_asistencia)
    if request.method == 'POST':
        form = AsistenciaForm(request.POST, instance=inasistencia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inasistencia actualizada exitosamente.')
            return redirect('inasistencia_list')
    else:
        form = AsistenciaForm(instance=inasistencia)
    return render(request, 'inasistencia_form.html', {'form': form, 'action': 'Editar'})

@login_required
@es_admin
def inasistencia_delete(request, id_asistencia):
    """
    Elimina un registro de inasistencia.
    """
    inasistencia = get_object_or_404(Asistencia, pk=id_asistencia)
    if request.method == 'POST':
        inasistencia.delete()
        messages.success(request, 'Inasistencia eliminada exitosamente.')
        return redirect('inasistencia_list')
    return render(request, 'inasistencia_confirm_delete.html', {'inasistencia': inasistencia})

"""
registrar_asistencia_diaria se encarga de registra la asistencia diaria por empleado 
"""


@login_required
def registrar_asistencia_diaria(request):
    empleado_encontrado = None
    asistencia_hoy = None
    cedula_buscada = ""
    hoy = timezone.localdate()

    #logout = cerrar_sesion(request)

    current_time_dt = timezone.localtime() 

    HORA_LIMITE_ENTRADA = datetime.time(8, 30, 0) 

    if hasattr(request.user, 'usuarios') and request.user.usuarios.empleado:
        empleado_encontrado = request.user.usuarios.empleado
        cedula_buscada = empleado_encontrado.cedula

        asistencia_hoy = Asistenciaconfirmada.objects.filter(
            id_empleado=empleado_encontrado,
            fecha_asistencia=hoy
        ).first()

    
        if (not asistencia_hoy or not asistencia_hoy.hora_entrada) and current_time_dt.time() > HORA_LIMITE_ENTRADA:
            inasistencia_existente = Asistencia.objects.filter(
                id_empleado=empleado_encontrado,
                fecha_asistencia=hoy
            ).first()

            if not inasistencia_existente:
                Asistencia.objects.create(
                    id_empleado=empleado_encontrado,
                    fecha_asistencia=hoy,
                    asistio=False,
                    tipo_inasistencia='injustificada',
                    observaciones=f'Inasistencia automática por no registro de entrada antes de las {HORA_LIMITE_ENTRADA.strftime("%H:%M")}.'
                )
                messages.warning(request, f"Se ha registrado una inasistencia injustificada para {empleado_encontrado.nombre} {empleado_encontrado.apellido} para hoy.")

        if request.method == 'POST':
            
            if 'registrar_entrada' in request.POST:
                asistencia_obj, created = Asistenciaconfirmada.objects.get_or_create(
                
                    id_empleado=empleado_encontrado,
                    fecha_asistencia=hoy,
                    
                    defaults={'asistio': True, 'hora_entrada': current_time_dt} 
                    
                       
                    
                )

                
                
                if not created:
                    if not asistencia_obj.hora_entrada:
                        asistencia_obj.hora_entrada = current_time_dt 
                        asistencia_obj.asistio = True
                        asistencia_obj.save()
                        
                        messages.success(request, f"Entrada registrada para {empleado_encontrado.nombre} {empleado_encontrado.apellido} a las {current_time_dt.strftime('%H:%M')}.")
                        return cerrar_sesion(request)
                    else:
                        messages.info(request, f"La entrada para {empleado_encontrado.nombre} {empleado_encontrado.apellido} ya fue registrada hoy a las {asistencia_obj.hora_entrada.strftime('%H:%M')}.")
                        return cerrar_sesion(request)
                else:
                    messages.success(request, f"Entrada registrada para {empleado_encontrado.nombre} {empleado_encontrado.apellido} a las {current_time_dt.strftime('%H:%M')}.")
                    return cerrar_sesion(request)
            elif 'registrar_salida' in request.POST:
                if asistencia_hoy and not asistencia_hoy.hora_salida:
                    asistencia_hoy.hora_salida = current_time_dt 
                    asistencia_hoy.save()
                    messages.success(request, f"Salida registrada para {empleado_encontrado.nombre} {empleado_encontrado.apellido} a las {current_time_dt.strftime('%H:%M')}.")
                    return cerrar_sesion(request)
                elif asistencia_hoy and asistencia_hoy.hora_salida:
                    messages.info(request, f"La salida para {empleado_encontrado.nombre} {empleado_encontrado.apellido} ya fue registrada hoy a las {asistencia_hoy.hora_salida.strftime('%H:%M')}.")
                else:
                    messages.error(request, "No se ha registrado la entrada para poder registrar la salida.")

            asistencia_hoy = Asistenciaconfirmada.objects.filter(
                id_empleado=empleado_encontrado,
                fecha_asistencia=hoy
            ).first()
    else:
        messages.error(request, "No se encontró un empleado asociado a su cuenta.")
        return redirect('login')

    context = {
        'empleado_encontrado': empleado_encontrado,
        'asistencia_hoy': asistencia_hoy,
        'cedula_buscada': cedula_buscada,
        'hora_actual': current_time_dt, 
    }
    return render(request, 'registrar_asistencia_diaria.html', context)


@login_required
@es_admin
def inasistencia_create(request):
    """
    Permite registrar una nueva inasistencia para un empleado.
    """
    if request.method == 'POST':
        form = AsistenciaForm(request.POST)
        if form.is_valid():
            inasistencia = form.save(commit=False)
            inasistencia.asistio = False
            inasistencia.save()
            messages.success(request, 'Inasistencia registrada exitosamente.')
            return redirect('inasistencia_list')
    else:
        form = AsistenciaForm()
    return render(request, 'inasistencia_form.html', {'form': form, 'action': 'Crear'})
@login_required
@es_admin_o_contador
def asistencia_confirmada_list(request):
    """
    Muestra un listado paginado de asistencias confirmadas, con opciones de filtrado.
    """
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    cedula = request.GET.get('cedula')
    nombre = request.GET.get('nombre')
    page = request.GET.get('page', 1)

    asistencias = Asistenciaconfirmada.objects.select_related('id_empleado').order_by(
        '-fecha_asistencia',
        'id_empleado__apellido',
        'id_empleado__nombre'
    )

    if fecha_desde:
        asistencias = asistencias.filter(fecha_asistencia__gte=fecha_desde)
    if fecha_hasta:
        asistencias = asistencias.filter(fecha_asistencia__lte=fecha_hasta)
    if cedula:
        asistencias = asistencias.filter(id_empleado__cedula__icontains=cedula)
    if nombre:
        asistencias = asistencias.filter(
            Q(id_empleado__nombre__icontains=nombre) |
            Q(id_empleado__apellido__icontains=nombre)
        )

    items_por_pagina = 3 
    paginator = Paginator(asistencias, items_por_pagina)

    try:
        asistencias_paginadas = paginator.page(page)
    except PageNotAnInteger:
        asistencias_paginadas = paginator.page(1)
    except EmptyPage:
        asistencias_paginadas = paginator.page(paginator.num_pages)
   
    hoy = timezone.localdate()
    primer_dia_mes = hoy.replace(day=1)

    context = {
        'asistencias_confirmadas': asistencias_paginadas, 
        'hoy': hoy,
        'primer_dia_mes': primer_dia_mes,
        'filtros': {
            'fecha_desde': fecha_desde or str(primer_dia_mes),
            'fecha_hasta': fecha_hasta or str(hoy),
            'cedula': cedula or '',
            'nombre': nombre or '',
        }
    }
    return render(request, 'asistencia_lista.html', context)


@login_required
@es_admin_o_contador
@transaction.atomic
def generar_nomina_por_departamento(request):
    form = NominaDepartamentalForm() 

    if request.method == 'POST':
        form = NominaDepartamentalForm(request.POST)
        if form.is_valid():
            departamentos = form.cleaned_data['departamentos']       
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = fecha_inicio + timedelta(days=6)

            try:
                ultima_tasa = Tasa.objects.latest('fecha')
            except Tasa.DoesNotExist:
                messages.error(request, "No hay tasa BCV registrada.")
                return render(request, 'generar_nominas_por_departamento.html', {'form': form})

            parametros = ParametrosNomina.objects.all()
            param_dict = {p.nombre.strip().lower(): p for p in parametros}

            required = ['ivss', 'rpe', 'faov', 'cestaticket socialista', 
                        'hora extra', 'hora festiva', 'ince']
            for req in required:
                if req not in param_dict:
                    messages.error(request, f"Falta el parámetro obligatorio: {req}")
                    return render(request, 'generar_nomina_departamental.html', {'form': form})

            IVSS = param_dict['ivss']
            RPE = param_dict['rpe']
            FAOV = param_dict['faov']
            CESTATICKET = param_dict['cestaticket socialista']
            HORA_EXTRA = param_dict['hora extra']
            HORA_FESTIVA = param_dict['hora festiva']
            INCE = param_dict['ince']

   
            ultimo_dia_mes = (fecha_fin.day >= 26) or (fecha_fin + timedelta(days=5)).month != fecha_fin.month
            es_fin_de_mes = ultimo_dia_mes

            frecuencia_ince = getattr(INCE, 'Periodicidad de Aplicación', '').strip().lower()
            es_dia_pago_ince = (
                (frecuencia_ince == 'quincenal' and 14 <= fecha_fin.day <= 16) or
                (frecuencia_ince != 'quincenal' and es_fin_de_mes)
            )

            empleados = Empleado.objects.filter(
                id_depa__in=departamentos,
                activo=True 
            ).select_related('id_jornada', 'id_depa').order_by( 'apellido', 'nombre')

            nominas_generadas = []
            errores = []

            
            for empleado in empleados:
                try:
                    sueldo = Sueldo.objects.filter(id_empleado=empleado).latest('fecha_creacion')
                except Sueldo.DoesNotExist:
                    errores.append(f"{empleado} (Dpto: {empleado.id_depa}) sin sueldo asignado")
                    continue

                sueldo_semanal_bs = sueldo.sueldo_bs
                sueldo_diario_bs = sueldo_semanal_bs / Decimal('7')
                jornada_diaria = empleado.id_jornada.horas_diarias
                valor_hora_normal = sueldo_diario_bs / jornada_diaria

                horas_ordinarias = horas_extras = horas_festivas = Decimal('0')
                pago_extras = pago_festivas = pago_bonos = deduccion_inasistencias = deduccion_prestamo = Decimal('0')

                confirmadas = Asistenciaconfirmada.objects.filter(
                    id_empleado=empleado,
                    fecha_asistencia__range=[fecha_inicio, fecha_fin]
                )

                for reg in confirmadas:
                    if reg.hora_entrada and reg.hora_salida:
                        entrada = dt_mod.datetime.combine(reg.fecha_asistencia, reg.hora_entrada)
                        salida = dt_mod.datetime.combine(reg.fecha_asistencia, reg.hora_salida)
                        if salida < entrada:
                            salida += timedelta(days=1)
                        horas_dia = Decimal((salida - entrada).total_seconds() / 3600).quantize(Decimal('0.01'))

                        if reg.fecha_asistencia.weekday() >= 5: 
                            horas_festivas += horas_dia
                        else:
                            exceso = max(horas_dia - jornada_diaria, Decimal('0'))
                            horas_extras += exceso
                            horas_ordinarias += horas_dia - exceso

                if horas_ordinarias == 0:
                    dias_asistidos = Asistencia.objects.filter(
                        id_empleado=empleado,
                        fecha_asistencia__range=[fecha_inicio, fecha_fin],
                        asistio=True
                    ).count()
                    horas_ordinarias = Decimal(dias_asistidos) * jornada_diaria

           
                pago_extras = horas_extras * valor_hora_normal * HORA_EXTRA.porcentaje
                pago_festivas = horas_festivas * valor_hora_normal * HORA_FESTIVA.porcentaje

                bonos = BonoExtra.objects.filter(
                    id_empleado=empleado,
                    fecha_aplicacion__range=[fecha_inicio, fecha_fin],
                    pagado_en_nomina=False
                )
                pago_bonos = bonos.aggregate(total=Sum('monto_bs'))['total'] or Decimal('0')
                bonos.update(pagado_en_nomina=True)

         
                faltas = Asistencia.objects.filter(
                    id_empleado=empleado,
                    fecha_asistencia__range=[fecha_inicio, fecha_fin],
                    tipo_inasistencia='injustificada'
                ).count()
                deduccion_inasistencias = Decimal(faltas) * sueldo_diario_bs

                
                deduccion_prestamo = Decimal('0')
                try:
                    prestamo = Prestamo.objects.get(id_empleado=empleado, activo=True)
                    if prestamo.cuotas_restantes > 0 and prestamo.monto_pendiente_bs >= prestamo.monto_cuota_bs:
                        deduccion_prestamo = prestamo.monto_cuota_bs
                        prestamo.monto_pendiente_bs -= deduccion_prestamo
                        prestamo.cuotas_restantes -= 1
                        if prestamo.cuotas_restantes <= 0:
                            prestamo.activo = False
                        prestamo.save()
                except Prestamo.DoesNotExist:
                    pass

                base_seg_social = sueldo_semanal_bs + pago_extras + pago_festivas + pago_bonos
                ivss_bs = base_seg_social * IVSS.porcentaje
                rpe_bs = base_seg_social * RPE.porcentaje
                faov_bs = base_seg_social * FAOV.porcentaje
                inces_bs = (base_seg_social * INCE.porcentaje) if es_dia_pago_ince else Decimal('0')
                cestaticket_bs = CESTATICKET.valor_en_bs() if es_fin_de_mes else Decimal('0')

                total_asignaciones = sueldo_semanal_bs + pago_extras + pago_festivas + pago_bonos + cestaticket_bs
                total_deducciones = deduccion_inasistencias + deduccion_prestamo + ivss_bs + rpe_bs + faov_bs
                neto_pagar = total_asignaciones - total_deducciones

                # creaion de nomina y conceptos
                nomina = Nomina.objects.create(
                    id_empleado=empleado,
                    id_sueldo=sueldo,
                    id_trabajo=empleado.id_trabajo,  # o el cargo actual del empleado
                    periodo_inicio=fecha_inicio,
                    periodo_fin=fecha_fin,
                    tipo_periodo='SEMANAL',
                    total_asignaciones_bs=round(total_asignaciones, 2),
                    total_deducciones_bs=round(total_deducciones, 2),
                    sueldo_neto_bs=round(neto_pagar, 2),
                )

                ConceptoNomina.objects.create(
                    id_nomina=nomina,
                    sueldo_bs_base=round(sueldo_semanal_bs, 2),
                    cestaticket_bs=round(cestaticket_bs, 2),
                    horas_ordinarias=round(horas_ordinarias, 2),
                    horas_extras=round(horas_extras, 2),
                    pago_horas_extras_bs=round(pago_extras, 2),
                    horas_festivas=round(horas_festivas, 2),
                    pago_horas_festivas_bs=round(pago_festivas, 2),
                    pago_bonos_bs=round(pago_bonos, 2),
                    dias_enfermedad=faltas,
                    pago_inasistencias_bs=round(deduccion_inasistencias, 2),
                    pago_prestamo_bs=round(deduccion_prestamo, 2),
                    ivss_bs=round(ivss_bs, 2),
                    inces_bs=round(inces_bs, 2),
                    rpe_bs=round(rpe_bs, 2),
                    faov_bs=round(faov_bs, 2),
                    total_asignaciones_bs=round(total_asignaciones, 2),
                    total_deducciones_bs=round(total_deducciones, 2),
                )

                # acumulacion de prestaciones al final del mes
                if es_fin_de_mes:
                    alicuota_utilidades = Decimal('0.25')
                    alicuota_bono_vacacional = Decimal('0.0417')  # 15 dias / 360
                    salario_integral_diario = sueldo_diario_bs * (1 + alicuota_utilidades + alicuota_bono_vacacional)

                    PrestacionSocialAcumulada.objects.update_or_create(
                        empleado=empleado,
                        fecha_calculo__year=fecha_fin.year,
                        fecha_calculo__month=fecha_fin.month,
                        defaults={
                            'monto_acumulado': salario_integral_diario * 30,
                            'salario_integral_referencia': salario_integral_diario * 30,
                            'dias_acumulados': 30
                        }
                    )

                nominas_generadas.append(nomina)

            # lo mismo que en nominas grupales se genera el resultado de las nominas
            messages.success(request, f"Se generaron {len(nominas_generadas)} nóminas correctamente.")
            return render(request, 'home.html', {
                'nominas_generadas': nominas_generadas,
                'departamentos': departamentos,
                'periodo_inicio': fecha_inicio,
                'periodo_fin': fecha_fin,
                'errores_generacion': errores
            })

    return render(request, 'generar_nominas_por_departamento.html', {'form': form})


@login_required
@es_admin_o_contador
@transaction.atomic

def generar_nomina_grupal(request):
    form = NominaGrupalForm()

    if request.method == 'POST':
        form = NominaGrupalForm(request.POST)
        if form.is_valid():
            labor_seleccionada = form.cleaned_data['labor']
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = fecha_inicio + timedelta(days=6)

            try:
                ultima_tasa = Tasa.objects.latest('fecha')
            except Tasa.DoesNotExist:
                messages.error(request, "No hay tasa BCV registrada.")
                return render(request, 'generar_nomina_grupal.html', {'form': form})

            parametros = ParametrosNomina.objects.all()
            param_dict = {p.nombre.lower(): p for p in parametros}

            required = ['ivss', 'rpe', 'faov', 'cestaticket socialista', 'hora extra', 'hora festiva', 'ince']
            for req in required:
                if req not in param_dict:
                    messages.error(request, f"Falta el parámetro obligatorio: {req}")
                    return render(request, 'generar_nomina_grupal.html', {'form': form})

            IVSS = param_dict['ivss']
            RPE = param_dict['rpe']
            FAOV = param_dict['faov']
            CESTATICKET = param_dict['cestaticket socialista']
            HORA_EXTRA = param_dict['hora extra']
            HORA_FESTIVA = param_dict['hora festiva']
            INCE= param_dict['ince']


          

            ultimo_dia_mes = (fecha_fin.day >= 26) or (fecha_fin + timedelta(days=5)).month != fecha_fin.month
            es_fin_de_mes = ultimo_dia_mes

            frecuencia_ince = getattr(INCE, 'Periodicidad de Aplicación', '').strip().lower()

            if frecuencia_ince == 'quincenal':
                es_dia_pago_ince = (14 <= fecha_fin.day <= 16)
                
            else:
                es_dia_pago_ince = es_fin_de_mes


            print(es_dia_pago_ince)

            empleados = Empleado.objects.filter(id_trabajo=labor_seleccionada)
            nominas_generadas = []
            errores = []

            for empleado in empleados:
                try:
                    sueldo = Sueldo.objects.filter(id_empleado=empleado).latest('fecha_creacion')
                except Sueldo.DoesNotExist:
                    errores.append(f"{empleado} sin sueldo asignado")
                    continue

                sueldo_semanal_bs = sueldo.sueldo_bs
                sueldo_diario_bs = sueldo_semanal_bs / Decimal('7')
                jornada_diaria = empleado.id_jornada.horas_diarias
                valor_hora_normal = sueldo_diario_bs / jornada_diaria

                horas_ordinarias = horas_extras = horas_festivas = Decimal('0')
                pago_extras = pago_festivas = pago_bonos = deduccion_inasistencias = deduccion_prestamo = Decimal('0')

                confirmadas = Asistenciaconfirmada.objects.filter(
                    id_empleado=empleado,
                    fecha_asistencia__range=[fecha_inicio, fecha_fin]
                )

                for reg in confirmadas:
                    if reg.hora_entrada and reg.hora_salida:
                        entrada = dt_mod.datetime.combine(reg.fecha_asistencia, reg.hora_entrada)
                        salida = dt_mod.datetime.combine(reg.fecha_asistencia, reg.hora_salida)
                        if salida < entrada:
                            salida += timedelta(days=1)
                        horas_dia = Decimal((salida - entrada).total_seconds() / 3600).quantize(Decimal('0.01'))

                        if reg.fecha_asistencia.weekday() >= 5:
                            horas_festivas += horas_dia
                        else:
                            exceso = max(horas_dia - jornada_diaria, Decimal('0'))
                            horas_extras += exceso
                            horas_ordinarias += horas_dia - exceso

                if horas_ordinarias == 0:
                    dias_asistidos = Asistencia.objects.filter(
                        id_empleado=empleado,
                        fecha_asistencia__range=[fecha_inicio, fecha_fin],
                        asistio=True
                    ).count()
                    horas_ordinarias = Decimal(dias_asistidos) * jornada_diaria

                pago_extras = horas_extras * valor_hora_normal * HORA_EXTRA.porcentaje
                pago_festivas = horas_festivas * valor_hora_normal * HORA_FESTIVA.porcentaje

                bonos = BonoExtra.objects.filter(
                    id_empleado=empleado,
                    fecha_aplicacion__range=[fecha_inicio, fecha_fin],
                    pagado_en_nomina=False
                )
                pago_bonos = bonos.aggregate(total=Sum('monto_bs'))['total'] or Decimal('0')
                bonos.update(pagado_en_nomina=True)

                faltas = Asistencia.objects.filter(
                    id_empleado=empleado,
                    fecha_asistencia__range=[fecha_inicio, fecha_fin],
                    tipo_inasistencia='injustificada'
                ).count()
                deduccion_inasistencias = Decimal(faltas) * sueldo_diario_bs

                try:
                    prestamo = Prestamo.objects.get(id_empleado=empleado, activo=True)
                    if prestamo.cuotas_restantes > 0 and prestamo.monto_pendiente_bs >= prestamo.monto_cuota_bs:
                        deduccion_prestamo = prestamo.monto_cuota_bs
                        prestamo.monto_pendiente_bs -= deduccion_prestamo
                        prestamo.cuotas_restantes -= 1
                        if prestamo.cuotas_restantes <= 0:
                            prestamo.activo = False
                        prestamo.save()
                except Prestamo.DoesNotExist:
                    pass

                base_seg_social = sueldo_semanal_bs + pago_extras + pago_festivas + pago_bonos
                ivss_bs = base_seg_social * IVSS.porcentaje
                rpe_bs = base_seg_social * RPE.porcentaje
                faov_bs = base_seg_social * FAOV.porcentaje
                inces_bs = (base_seg_social * INCE.porcentaje ) if es_dia_pago_ince else Decimal('0')


                cestaticket_bs = CESTATICKET.valor_en_bs() if es_fin_de_mes else Decimal('0')

                total_asignaciones = sueldo_semanal_bs + pago_extras + pago_festivas + pago_bonos + cestaticket_bs
                total_deducciones = deduccion_inasistencias + deduccion_prestamo + ivss_bs + rpe_bs + faov_bs
                neto_pagar = total_asignaciones - total_deducciones

                nomina = Nomina.objects.create(
                    id_empleado=empleado,
                    id_sueldo=sueldo,
                    id_trabajo=labor_seleccionada,
                    periodo_inicio=fecha_inicio,
                    periodo_fin=fecha_fin,
                    tipo_periodo='SEMANAL',
                    total_asignaciones_bs=round(total_asignaciones, 2),
                    total_deducciones_bs=round(total_deducciones, 2),
                    sueldo_neto_bs=round(neto_pagar, 2),
                )

                ConceptoNomina.objects.create(
                    id_nomina=nomina,
                    sueldo_bs_base=round(sueldo_semanal_bs, 2),
                    cestaticket_bs=round(cestaticket_bs, 2),
                    horas_ordinarias=round(horas_ordinarias, 2),
                    horas_extras=round(horas_extras, 2),
                    pago_horas_extras_bs=round(pago_extras, 2),
                    horas_festivas=round(horas_festivas, 2),
                    pago_horas_festivas_bs=round(pago_festivas, 2),
                    pago_bonos_bs=round(pago_bonos, 2),
                    dias_enfermedad=faltas,
                    pago_inasistencias_bs=round(deduccion_inasistencias, 2),
                    pago_prestamo_bs=round(deduccion_prestamo, 2),
                    ivss_bs=round(ivss_bs, 2),
                    inces_bs=round(inces_bs, 2),
                    rpe_bs=round(rpe_bs, 2),
                    faov_bs=round(faov_bs, 2),
                    total_asignaciones_bs=round(total_asignaciones, 2),
                    total_deducciones_bs=round(total_deducciones, 2),
                )

                nominas_generadas.append(nomina)

                if es_fin_de_mes:
                    alicuota_utilidades = Decimal('0.25')
                    alicuota_bono_vacacional = Decimal('0.0417')
                    salario_integral_diario = sueldo_diario_bs * (1 + alicuota_utilidades + alicuota_bono_vacacional)

                    PrestacionSocialAcumulada.objects.update_or_create(
                        empleado=empleado,
                        fecha_calculo__year=fecha_fin.year,
                        fecha_calculo__month=fecha_fin.month,
                        defaults={
                            'monto_acumulado': salario_integral_diario * 30,
                            'salario_integral_referencia': salario_integral_diario * 30,
                            'dias_acumulados': 30
                        }
                    )

            messages.success(request, f"Se generaron {len(nominas_generadas)} nóminas correctamente.")
            return render(request, 'nomina_grupal_generada.html', {
                'nominas_generadas': nominas_generadas,
                'errores_generacion': errores
            })

    return render(request, 'generar_nomina_grupal.html', {'form': form})



@login_required
def editar_nomina(request, id_nomina):
    """
    Permite editar un registro de nómina existente.
    """
    nomina = get_object_or_404(Nomina, pk=id_nomina)
    if request.method == 'POST':
        form = NominaForm(request.POST, instance=nomina)
        if form.is_valid():
            form.save()
            return render(request, 'home.html')
    else:
        form = NominaForm(instance=nomina)
    return render(request, 'editar_nomina.html', {'form': form})
 
@login_required
def eliminar_nomina(request, id_nomina):
    """
    Elimina un registro de nómina.
    """
    nomina = get_object_or_404(Nomina, pk=id_nomina)
    if request.method == 'POST':
        nomina.delete()
        return render(request, 'nomina_eliminada_satisfactoriamente.html')
    return render(request, 'eliminar_nomina.html', {'nomina': nomina})



def eliminar_todas_nominas(request):
    if request.method == 'GET': 
  
        Nomina.objects.all().delete()
    return redirect('home') 



def es_habil(fecha):
    """
    Función auxiliar para determinar si una fecha es un día hábil.
    Excluye sábados y domingos. Puede extenderse para incluir feriados nacionales.
    """
    if fecha.weekday() >= 5: 
        return False

    return True

def get_dias_habiles_entre(fecha_inicio, fecha_fin):
    """
    Función auxiliar para obtener el número de días hábiles entre dos fechas.
    (Actualmente no se usa directamente en liquidación, pero es útil)
    """
    dias = 0
    current_date = fecha_inicio
    while current_date <= fecha_fin:
        if es_habil(current_date):
            dias += 1
        current_date += timedelta(days=1)
    return dias

def calcular_salario_normal(empleado, fecha_referencia):
    """
    Función para obtener el salario normal de un empleado en una fecha de referencia.
    
    aplicado según la definición del Art. 104 de la LOTTT. 
    """
    try:
        sueldo = Sueldo.objects.filter(id_empleado=empleado, fecha_creacion__lte=fecha_referencia).latest('fecha_creacion')
        return sueldo.sueldo_bs
    except Sueldo.DoesNotExist:
        return Decimal('0.00')

def calcular_salario_integral(empleado, fecha_referencia, dias_base_utilidades_empresa=Decimal('30')):
    """
    Función para calcular el salario integral de un empleado.


    """
    salario_normal = calcular_salario_normal(empleado, fecha_referencia)

    antiguedad_anios = relativedelta(fecha_referencia, empleado.fecha_contratacion).years
    
    dias_bono_vacacional_base = Decimal('15')
    dias_bono_vacacional_adicional = min(Decimal(antiguedad_anios), Decimal('15')) 
    total_dias_bono_vacacional = dias_bono_vacacional_base + dias_bono_vacacional_adicional
    alicuota_bono_vacacional = (salario_normal * total_dias_bono_vacacional) / Decimal('360')

    alicuota_utilidades = (salario_normal * dias_base_utilidades_empresa) / Decimal('360')

    salario_integral = salario_normal + alicuota_bono_vacacional + alicuota_utilidades
    return salario_integral.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


"""
    Función principal para calcular todos los componentes de la liquidación de un empleado.
   .
"""


def calcular_salario_integral(empleado, fecha_fin_relacion):

    return calcular_salario_normal(empleado, fecha_fin_relacion) * Decimal('1.3') 

""" Version Reciente"""


def calcular_liquidacion_detalle(empleado, fecha_fin_relacion, motivo_terminacion, dias_utilidades_empresa=Decimal('30'), dias_vacaciones_otorgados=None):

    fecha_ingreso = empleado.fecha_contratacion
    antiguedad_relativa = relativedelta(fecha_fin_relacion, fecha_ingreso)
    antiguedad_anios = antiguedad_relativa.years
    antiguedad_meses = antiguedad_relativa.months
    antiguedad_dias = antiguedad_relativa.days


    fecha_regreso_trabajo_calc = None
    vacation_error_message = None
    
   
    if motivo_terminacion == 'vacaciones':
        if dias_vacaciones_otorgados is not None and dias_vacaciones_otorgados > 0:
            
            fecha_temp = fecha_fin_relacion
            dias_restantes = dias_vacaciones_otorgados
            
            while dias_restantes > 0:
                fecha_temp += timedelta(days=1)
                if fecha_temp.weekday() < 5:  
                    dias_restantes -= 1
            
            fecha_regreso_trabajo_calc = fecha_temp
        else:
            vacation_error_message = "Debe especificar una cantidad válida de días de vacaciones para el motivo 'Vacaciones'."

    salario_normal_final = calcular_salario_normal(empleado, fecha_fin_relacion)
    salario_integral_final = calcular_salario_integral(empleado, fecha_fin_relacion)
    #salario_integral_final = Decimal('0.00')
    print(empleado)
    print(fecha_fin_relacion)
    print(dias_utilidades_empresa)

    """ 1. Prestaciones Sociales (Art. 142 LOTTT) """
    monto_prestaciones_garantia = Decimal('0.00')
    monto_intereses_prestaciones = Decimal('0.00')
    
    try:
        ultima_ps_acumulada = PrestacionSocialAcumulada.objects.filter(empleado=empleado).latest('fecha_calculo')
        monto_prestaciones_garantia = ultima_ps_acumulada.monto_acumulado
        monto_intereses_prestaciones = ultima_ps_acumulada.intereses_acumulados
    except PrestacionSocialAcumulada.DoesNotExist:
        pass

    monto_prestaciones_retroactivo = Decimal('0.00')
    if antiguedad_anios >= 1 or (antiguedad_anios == 0 and antiguedad_meses >= 6):
        dias_retroactivo_base = Decimal(antiguedad_anios) * Decimal('30')
        if antiguedad_meses >= 6: 
            dias_retroactivo_base += Decimal('30')
        monto_prestaciones_retroactivo = (salario_integral_final / Decimal('30')) * dias_retroactivo_base
    
    monto_prestaciones_a_pagar = max(monto_prestaciones_garantia + monto_intereses_prestaciones, monto_prestaciones_retroactivo)
    anticipos_prestaciones = Decimal('0.00') 

    """ 2. Vacaciones No Disfrutadas y Bono Vacacional (Art. 192, 193 LOTTT) """
    dias_vacaciones_pendientes_calc = Decimal('0.00')
    monto_vacaciones_pendientes = Decimal('0.00')
    dias_bono_vacacional_pendiente_calc = Decimal('0.00')
    monto_bono_vacacional_pendiente = Decimal('0.00')

    if motivo_terminacion != 'vacaciones':  
        if antiguedad_anios >= 1:
            dias_vacaciones_por_ano = Decimal('15') + min(Decimal(antiguedad_anios) - 1, Decimal('15'))
            dias_bono_vacacional_por_ano = Decimal('15') + min(Decimal(antiguedad_anios) - 1, Decimal('15'))
            
            fecha_ultimo_aniversario = empleado.fecha_contratacion + relativedelta(years=antiguedad_anios)
            dias_trabajados_ultimo_periodo = (fecha_fin_relacion - fecha_ultimo_aniversario).days

            if dias_trabajados_ultimo_periodo > 0:
                meses_trabajados_ultimo_periodo_dec = Decimal(dias_trabajados_ultimo_periodo) / Decimal('30')
                
                dias_vacaciones_pendientes_calc = (dias_vacaciones_por_ano / Decimal('12')) * meses_trabajados_ultimo_periodo_dec
                dias_bono_vacacional_pendiente_calc = (dias_bono_vacacional_por_ano / Decimal('12')) * meses_trabajados_ultimo_periodo_dec
                
        monto_vacaciones_pendientes = (salario_normal_final / Decimal('30')) * dias_vacaciones_pendientes_calc.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        monto_bono_vacacional_pendiente = (salario_normal_final / Decimal('30')) * dias_bono_vacacional_pendiente_calc.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    """ 3. Utilidades Pendientes (Art. 131 LOTTT) """
    dias_utilidades_pendientes_calc = Decimal('0.00')
    monto_utilidades_pendientes = Decimal('0.00')
    
    mes_inicio_fiscal = 1 
    
    if fecha_fin_relacion.month >= mes_inicio_fiscal:
        fecha_inicio_ejercicio_fiscal = date(fecha_fin_relacion.year, mes_inicio_fiscal, 1)
    else:
        fecha_inicio_ejercicio_fiscal = date(fecha_fin_relacion.year - 1, mes_inicio_fiscal, 1)

    meses_trabajados_ejercicio = (fecha_fin_relacion.year - fecha_inicio_ejercicio_fiscal.year) * 12 + (fecha_fin_relacion.month - fecha_inicio_ejercicio_fiscal.month)
    
    if fecha_fin_relacion.day < 30 and fecha_fin_relacion.month != fecha_inicio_ejercicio_fiscal.month:
        meses_trabajados_ejercicio -= 1
    
    meses_trabajados_ejercicio = max(0, meses_trabajados_ejercicio)

    if meses_trabajados_ejercicio > 0:
        dias_utilidades_base_empresa_local = dias_utilidades_empresa 
        
        dias_utilidades_pendientes_calc = (dias_utilidades_base_empresa_local / Decimal('12')) * Decimal(meses_trabajados_ejercicio)
        
        monto_calculado_utilidades = (salario_integral_final / Decimal('30')) * dias_utilidades_pendientes_calc.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        minimo_legal_utilidades = (salario_normal_final / Decimal('30')) * Decimal('30') 
        maximo_legal_utilidades = (salario_normal_final / Decimal('30')) * Decimal('120')

        monto_preaviso = Decimal('0.00')
        TASA_DEDUCCION_INCES = Decimal('0.005')

        monto_utilidades_pendientes = max(minimo_legal_utilidades, min(monto_calculado_utilidades, maximo_legal_utilidades))

        monto_deduccion_inces = Decimal('0.00')
        if monto_utilidades_pendientes > 0:
             monto_deduccion_inces = monto_utilidades_pendientes * TASA_DEDUCCION_INCES
        monto_deduccion_inces

    """ 4. Indemnización por Despido Injustificado (Art. 92 LOTTT) """
    monto_indemnizacion_despido = Decimal('0.00')
    if motivo_terminacion == 'despido_injustificado':
        anios_para_indemnizacion = Decimal(antiguedad_anios)
        if antiguedad_meses >= 6: 
            anios_para_indemnizacion += Decimal('1')
        
        anios_para_indemnizacion = min(anios_para_indemnizacion, Decimal('11'))
        
        monto_indemnizacion_despido = salario_integral_final * anios_para_indemnizacion

    """ 5. Preaviso (Art. 81 LOTTT) """
    monto_preaviso = Decimal('0.00')
    if motivo_terminacion in ['despido_injustificado', 'renuncia_sin_preaviso']: 
        dias_preaviso = Decimal('0.00')
        
        if antiguedad_anios >= 10:
            dias_preaviso = Decimal('90') 
        elif antiguedad_anios >= 5:
            dias_preaviso = Decimal('60') 
        elif antiguedad_anios >= 1:
            dias_preaviso = Decimal('30') 
        elif antiguedad_meses >= 6:
            dias_preaviso = Decimal('15') 
        elif antiguedad_meses >= 1: 
            dias_preaviso = Decimal('7')

        monto_preaviso = (salario_normal_final / Decimal('30')) * dias_preaviso

    """ Total Liquidación """
    total_liquidacion = (
        monto_prestaciones_a_pagar - anticipos_prestaciones +
        monto_vacaciones_pendientes + monto_bono_vacacional_pendiente +
        monto_utilidades_pendientes +
        monto_indemnizacion_despido + monto_preaviso
        
    )

    return {
        'empleado': empleado,
        'fecha_fin_relacion': fecha_fin_relacion,
        'motivo_terminacion': motivo_terminacion,
        'salario_normal_final': salario_normal_final,
        'salario_integral_final': salario_integral_final,
        'monto_prestaciones_garantia': monto_prestaciones_garantia.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'monto_intereses_prestaciones': monto_intereses_prestaciones.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'monto_prestaciones_retroactivo': monto_prestaciones_retroactivo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'monto_prestaciones_a_pagar': monto_prestaciones_a_pagar.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'anticipos_prestaciones': anticipos_prestaciones.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'dias_vacaciones_pendientes': dias_vacaciones_pendientes_calc.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'monto_vacaciones_pendientes': monto_vacaciones_pendientes.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'dias_bono_vacacional_pendiente': dias_bono_vacacional_pendiente_calc.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'monto_bono_vacacional_pendiente': monto_bono_vacacional_pendiente.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'dias_utilidades_pendientes': dias_utilidades_pendientes_calc.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'monto_utilidades_pendientes': monto_utilidades_pendientes.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'monto_indemnizacion_despido': monto_indemnizacion_despido.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'monto_preaviso': monto_preaviso.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'total_liquidacion': total_liquidacion.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),

        'dias_vacaciones_otorgados': dias_vacaciones_otorgados if motivo_terminacion == 'vacaciones' else None,
        'fecha_regreso_trabajo': fecha_regreso_trabajo_calc,
        'vacation_error': vacation_error_message,
    }


def crear_liquidacion_individual(request):
    """
    Vista para crear una liquidación individual de un empleado.

    """
    if request.method == 'POST':
        form = LiquidacionForm(request.POST)
        if form.is_valid():
            empleado = form.cleaned_data['empleado']
            fecha_fin_relacion = form.cleaned_data['fecha_fin_relacion']
            motivo_terminacion = form.cleaned_data['motivo_terminacion']
            
            dias_vacaciones_otorgados = None
            if motivo_terminacion == 'vacaciones':
                dias_vacaciones_otorgados = form.cleaned_data.get('dias_vacaciones_otorgados')
                if not dias_vacaciones_otorgados or dias_vacaciones_otorgados <= 0:
                    messages.error(request, "Debe especificar una cantidad válida de días de vacaciones.")
                    return render(request, 'crear_liquidacion_individual.html', {'form': form})

            dias_utilidades_empresa = Decimal('90')  

            calculo_data = calcular_liquidacion_detalle(
                empleado, 
                fecha_fin_relacion, 
                motivo_terminacion, 
                dias_utilidades_empresa,
                dias_vacaciones_otorgados
            )

            if motivo_terminacion == 'vacaciones' and calculo_data.get('vacation_error'):
                messages.error(request, calculo_data['vacation_error'])
                return render(request, 'crear_liquidacion_individual.html', {'form': form})

            liquidacion = Liquidacion.objects.create(
                empleado=empleado,
                fecha_fin_relacion=fecha_fin_relacion,
                motivo_terminacion=motivo_terminacion,
                salario_normal_final=calculo_data['salario_normal_final'],
                salario_integral_final=calculo_data['salario_integral_final'],
                monto_prestaciones_garantia=calculo_data['monto_prestaciones_garantia'],
                monto_intereses_prestaciones=calculo_data['monto_intereses_prestaciones'],
                monto_prestaciones_retroactivo=calculo_data['monto_prestaciones_retroactivo'],
                monto_prestaciones_a_pagar=calculo_data['monto_prestaciones_a_pagar'],
                anticipos_prestaciones=calculo_data['anticipos_prestaciones'],
                dias_vacaciones_pendientes=calculo_data['dias_vacaciones_pendientes'],
                monto_vacaciones_pendientes=calculo_data['monto_vacaciones_pendientes'],
                dias_bono_vacacional_pendiente=calculo_data['dias_bono_vacacional_pendiente'],
                monto_bono_vacacional_pendiente=calculo_data['monto_bono_vacacional_pendiente'],
                dias_utilidades_pendientes=calculo_data['dias_utilidades_pendientes'],
                monto_utilidades_pendientes=calculo_data['monto_utilidades_pendientes'],
                monto_indemnizacion_despido=calculo_data['monto_indemnizacion_despido'],
                monto_preaviso=calculo_data['monto_preaviso'],
                total_liquidacion=calculo_data['total_liquidacion'],
                dias_vacaciones_otorgados=calculo_data.get('dias_vacaciones_otorgados'),
                fecha_regreso_trabajo=calculo_data.get('fecha_regreso_trabajo')
            )
            
            messages.success(request, f"Liquidación para {empleado.nombre} {empleado.apellido} creada exitosamente.")
            if motivo_terminacion == 'vacaciones':
                messages.info(request, f"El empleado debe regresar al trabajo el {calculo_data['fecha_regreso_trabajo'].strftime('%d/%m/%Y')}")
            
            return redirect('lista_liquidaciones')
        else:
            messages.error(request, "Error en el formulario. Por favor, corrija los errores.")
    else:
        form = LiquidacionForm()
    
    return render(request, 'crear_liquidacion_individual.html', {'form': form})

@login_required
def crear_liquidacion_grupal(request):
    """
    Vista para crear liquidaciones de forma grupal, filtrando por departamento o labor.
    Calcula y guarda liquidaciones para múltiples empleados a la vez.
    """
    liquidaciones_generadas = []
    if request.method == 'POST':
        form = LiquidacionGrupalForm(request.POST)
        if form.is_valid():
            departamento = form.cleaned_data['departamento']
            labor = form.cleaned_data['labor']
            fecha_fin_relacion = form.cleaned_data['fecha_fin_relacion']
            motivo_terminacion = request.POST.get('motivo_terminacion_grupal', 'otros') 

            empleados_a_liquidar = Empleado.objects.all()
            if departamento:
                empleados_a_liquidar = empleados_a_liquidar.filter(id_depa=departamento)
            if labor:
                empleados_a_liquidar = empleados_a_liquidar.filter(id_trabajo=labor)

            if not empleados_a_liquidar.exists():
                messages.warning(request, "No se encontraron empleados con los filtros seleccionados.")
            else:
                dias_utilidades_empresa = Decimal('90') 

                for empleado in empleados_a_liquidar:
                    calculo_data = calcular_liquidacion_detalle(empleado, fecha_fin_relacion, motivo_terminacion, dias_utilidades_empresa)
                    
                    liquidacion = Liquidacion.objects.create(
                        empleado=empleado,
                        fecha_fin_relacion=fecha_fin_relacion,
                        motivo_terminacion=motivo_terminacion,
                        salario_normal_final=calculo_data['salario_normal_final'],
                        salario_integral_final=calculo_data['salario_integral_final'],
                        monto_prestaciones_garantia=calculo_data['monto_prestaciones_garantia'],
                        monto_intereses_prestaciones=calculo_data['monto_intereses_prestaciones'],
                        monto_prestaciones_retroactivo=calculo_data['monto_prestaciones_retroactivo'],
                        monto_prestaciones_a_pagar=calculo_data['monto_prestaciones_a_pagar'],
                        anticipos_prestaciones=calculo_data['anticipos_prestaciones'],
                        dias_vacaciones_pendientes=calculo_data['dias_vacaciones_pendientes'],
                        monto_vacaciones_pendientes=calculo_data['monto_vacaciones_pendientes'],
                        dias_bono_vacacional_pendiente=calculo_data['dias_bono_vacacional_pendiente'],
                        monto_bono_vacacional_pendiente=calculo_data['monto_bono_vacacional_pendiente'],
                        dias_utilidades_pendientes=calculo_data['dias_utilidades_pendientes'],
                        monto_utilidades_pendientes=calculo_data['monto_utilidades_pendientes'],
                        monto_indemnizacion_despido=calculo_data['monto_indemnizacion_despido'],
                        monto_preaviso=calculo_data['monto_preaviso'],
                        total_liquidacion=calculo_data['total_liquidacion']
                    )
                    liquidaciones_generadas.append(liquidacion)
                messages.success(request, f"Se generaron {len(liquidaciones_generadas)} liquidaciones grupales.")
                return redirect('lista_liquidaciones')
        else:
            messages.error(request, "Error en el formulario. Por favor, corrija los errores.")
    else:
        form = LiquidacionGrupalForm()
    
    motivos_terminacion = Liquidacion._meta.get_field('motivo_terminacion').choices
    return render(request, 'crear_liquidacion_grupal.html', {'form': form, 'motivos_terminacion': motivos_terminacion})


#crear_liquidacion_grupal.html


@login_required
def lista_liquidaciones(request):
    """
    Vista para listar todas las liquidaciones existentes.
    Implementa paginación para manejar grandes volúmenes de datos.
    """
    liquidaciones = Liquidacion.objects.all().order_by('-fecha_creacion')
    paginator = Paginator(liquidaciones, 10)
    page = request.GET.get('page')
    try:
        liquidaciones_paginadas = paginator.page(page)
    except PageNotAnInteger:
        liquidaciones_paginadas = paginator.page(1)
    except EmptyPage:
        liquidaciones_paginadas = paginator.page(paginator.num_pages)
    
    return render(request, 'lista_liquidaciones.html', {'liquidaciones': liquidaciones_paginadas})

@login_required
def ver_liquidacion_pdf(request, pk):
    """
    Vista para generar un PDF de una liquidación específica.
    Recupera los datos de la liquidación y los renderiza en un template HTML que luego se convierte a PDF.
    """
   
    liquidacion = get_object_or_404(Liquidacion.objects.select_related('empleado'), pk=pk)
    
    template_path = 'liquidacion_pdf_template.html'
    context = {'liquidacion': liquidacion}

    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')

    response['Content-Disposition'] = f'attachment; filename="liquidacion_{liquidacion.empleado.cedula}_{liquidacion.fecha_fin_relacion}.pdf"'
    
    pisa_status = pisa.CreatePDF(
        html, dest=response
    )
    if pisa_status.err:
        return HttpResponse('Tuvimos algunos errores <pre>' + html + '</pre>')
    return response

@login_required
def eliminar_todas_liquidaciones(request):
    """
    Vista para eliminar todas las liquidaciones registradas en el sistema.
    Requiere una petición POST para su ejecución y muestra mensajes de éxito o error.
    """
    try:
        count, _ = Liquidacion.objects.all().delete()
        messages.success(request, f"Se eliminaron {count} liquidaciones exitosamente.")
    except Exception as e:
        messages.error(request, f"Ocurrió un error al intentar eliminar las liquidaciones: {e}")
    
    return redirect('lista_liquidaciones')

from django.http import JsonResponse
import json

@login_required
def inasistencias_histograma(request):
    """
    Genera los datos para un histograma de inasistencias por empleado.
    Cuenta el número de inasistencias (asistio=False) para cada empleado
    y los ordena de mayor a menor.
    """
    
    inasistencias_por_empleado = Asistencia.objects.filter(asistio=False, tipo_inasistencia='injustificada') \
                                                    .values('id_empleado__nombre', 'id_empleado__apellido') \
                                                    .annotate(total_faltas=Count('id_empleado')) \
                                                    .order_by('-total_faltas')
    
    
    labels = [] 
    data = []   

    for entry in inasistencias_por_empleado:
        empleado_nombre_completo = f"{entry['id_empleado__nombre']} {entry['id_empleado__apellido']}"
        labels.append(empleado_nombre_completo)
        data.append(entry['total_faltas'])

       
    print("\n--- DEPURACIÓN DE DATOS PARA HISTOGRAMA (DJANGO) ---")
    print(f"Queryset de inasistencias_por_empleado: {list(inasistencias_por_empleado)}")
    print(f"Labels que se pasarán al template: {labels}")
    print(f"Data que se pasará al template: {data}")
    print("-------------------------------------------\n")
  

    context = {
        'labels': labels,
        'data': data,
    }
    return render(request, 'inasistencias_histograma.html', context)




plt.switch_backend('Agg') 

@login_required
def inasistencias_histograma_imagen(request):
    """
    Genera un histograma de inasistencias por empleado y lo devuelve como una imagen.
    """
    inasistencias_por_empleado = Asistencia.objects.filter(asistio=False,    tipo_inasistencia='injustificada') \
                                                    .values('id_empleado__nombre', 'id_empleado__apellido') \
                                                    .annotate(total_faltas=Count('id_empleado')) \
                                                    .order_by('-total_faltas')
    
    labels = []  
    data = []    

    for entry in inasistencias_por_empleado:
        empleado_nombre_completo = f"{entry['id_empleado__nombre']} {entry['id_empleado__apellido']}"
        labels.append(empleado_nombre_completo)
        data.append(entry['total_faltas'])

    
    if not labels:
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No hay datos de inasistencias', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14, color='gray')
        ax.axis('off') 
    else:
       
        fig, ax = plt.subplots(figsize=(10, 6)) 
        
    
        ax.bar(labels, data, color='#007c91', width=0.15)

    
        ax.set_title('Inasistencias del Personal')
        ax.set_xlabel('Empleado')
        ax.set_ylabel('Número de Faltas')

    
        plt.xticks(rotation=45, ha='right')

    
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        
    
        plt.tight_layout()

    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close(fig) 


    return HttpResponse(buffer.getvalue(), content_type='image/png')


def create_missing_attendance_records():

    today = timezone.localdate()
    if is_holiday(today):
        return 0 

    employees = Empleado.objects.all()
    absences_created_count = 0

    for employee in employees:
        attendance_confirmed_today = Asistenciaconfirmada.objects.filter(
            id_empleado=employee,
            fecha_asistencia=today
        ).exists()

        if not attendance_confirmed_today:
            unjustified_absence_exists = Asistencia.objects.filter(
                id_empleado=employee,
                fecha_asistencia=today,
                asistio=False,
                tipo_inasistencia='injustificada'
            ).exists()

            if not unjustified_absence_exists:
                Asistencia.objects.create(
                    id_empleado=employee,
                    fecha_asistencia=today,
                    asistio=False,
                    tipo_inasistencia='injustificada',
                    observacion='Inasistencia injustificada automática por no registro de asistencia.'
                )
                absences_created_count += 1
                print(f"Inasistencia injustificada creada para {employee.nombre} {employee.apellido} en la fecha {today}.")
            else:
                print(f"Inasistencia injustificada ya existe para {employee.nombre} {employee.apellido} en la fecha {today}.")
        else:
            print(f"Asistencia confirmada para {employee.nombre} {employee.apellido} en la fecha {today}. No se crea inasistencia.")
    return absences_created_count

@login_required
@user_passes_test(es_admin, login_url='sinacceso')
def trigger_create_missing_attendances(request):


    if request.method == 'POST':
        absences_count = create_missing_attendance_records()
        if absences_count > 0:
            messages.success(request, f"Se crearon {absences_count} registros de inasistencia injustificada para el día de hoy.")
        else:
            messages.info(request, "No se crearon nuevas inasistencias injustificadas o ya existían para hoy, o es fin de semana/feriado.")
        return redirect('home') 
    else:
        return render(request, 'confirm_create_absences.html', {'titulo': 'Confirmar Generación de Inasistencias Injustificadas'})

@login_required
def crear_prestamo(request):
    if request.method == 'POST':
        form = PrestamoForm(request.POST)
        if form.is_valid():
            prestamo = form.save(commit=False)
            
            monto_total_bs = form.cleaned_data.get('monto_total_bs')
            numero_cuotas_deseado = form.cleaned_data.get('numero_cuotas_deseado')

            if monto_total_bs is not None and numero_cuotas_deseado is not None and numero_cuotas_deseado > 0:
                
                prestamo.monto_cuota_bs = (Decimal(monto_total_bs) / Decimal(numero_cuotas_deseado)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
             
                prestamo.cuotas_restantes = numero_cuotas_deseado
            else:
                
                messages.error(request, "Error en los datos para calcular las cuotas. Por favor, revise el monto total y el número de cuotas deseadas.")
                return render(request, 'generar_prestamos.html', {'form': form, 'titulo': 'Otorgar Nuevo Préstamo'})

            if prestamo.aprobado and not prestamo.fecha_aprobacion:
                prestamo.fecha_aprobacion = date.today() 

            prestamo.save() 
            messages.success(request, f"Préstamo para {prestamo.id_empleado.nombre} {prestamo.id_empleado.apellido} creado exitosamente.")
            return redirect('listar_prestamos') 
        else:
            messages.error(request, "Error al crear el préstamo. Por favor, revise los datos.")
            print("Errores del formulario de préstamo:", form.errors)
    else:
        form = PrestamoForm()
    
    context = {
        'form': form,
        'titulo': 'Otorgar Nuevo Préstamo'
    }
    return render(request, 'generar_prestamos.html', context)


"""
@login_required
def crear_prestamo(request):
    if request.method == 'POST':
        form = PrestamoForm(request.POST)
        if form.is_valid():
            prestamo = form.save(commit=False)
            
           
            if prestamo.aprobado and not prestamo.fecha_aprobacion:
                prestamo.fecha_aprobacion = date.today() 

            prestamo.save() 
            messages.success(request, f"Préstamo para {prestamo.id_empleado.nombre} {prestamo.id_empleado.apellido} creado exitosamente.")
            return redirect('listar_prestamos') 
        else:
            messages.error(request, "Error al crear el préstamo. Por favor, revise los datos.")
            print("Errores del formulario de préstamo:", form.errors)
    else:
        form = PrestamoForm()
    
    context = {
        'form': form,
        'titulo': 'Otorgar Nuevo Préstamo'
    }
    return render(request, 'generar_prestamos.html', context)

"""


@login_required
def listar_prestamos(request):
    """
    Lista todos los préstamos con paginación.
    """
   
    prestamo_list = Prestamo.objects.all().order_by('-fecha_solicitud')

   
    paginator = Paginator(prestamo_list, 4) 

   
    page = request.GET.get('page')

    try:
      
        prestamos = paginator.page(page)
    except PageNotAnInteger:
        
        prestamos = paginator.page(1)
    except EmptyPage:
        
        prestamos = paginator.page(paginator.num_pages)
    
    context = {
        'prestamos': prestamos, 
        'titulo': 'Lista de Préstamos'
    }
    return render(request, 'listar_prestamos.html', context)
@login_required
def editar_prestamo(request, pk):
    """
    Permite editar un préstamo existente.
    """
    prestamo = get_object_or_404(Prestamo, pk=pk)
    
    if request.method == 'POST':
        form = PrestamoForm(request.POST, instance=prestamo)
        if form.is_valid():
            edited_prestamo = form.save(commit=False)
            
            
            if edited_prestamo.aprobado and not edited_prestamo.fecha_aprobacion:
                edited_prestamo.fecha_aprobacion = date.today()
            elif not edited_prestamo.aprobado:
                edited_prestamo.fecha_aprobacion = None 
            
            
            if edited_prestamo.monto_pendiente_bs > edited_prestamo.monto_total_bs:
                edited_prestamo.monto_pendiente_bs = edited_prestamo.monto_total_bs
            
            
            if edited_prestamo.monto_pendiente_bs <= Decimal('0.00'):
                edited_prestamo.activo = False
                edited_prestamo.monto_pendiente_bs = Decimal('0.00')
                edited_prestamo.cuotas_restantes = 0
            else:
                edited_prestamo.activo = True 

            edited_prestamo.save()
            messages.success(request, f"Préstamo para {edited_prestamo.id_empleado.nombre} {edited_prestamo.id_empleado.apellido} actualizado exitosamente.")
            return redirect('listar_prestamos')
        else:
            messages.error(request, "Error al actualizar el préstamo. Por favor, revise los datos.")
            print("Errores del formulario de edición de préstamo:", form.errors)
    else:
        form = PrestamoForm(instance=prestamo)
    
    context = {
        'form': form,
        'titulo': f'Editar Préstamo para {prestamo.id_empleado.nombre} {prestamo.id_empleado.apellido}',
        'prestamo': prestamo, 
    }
    return render(request, 'editar_prestamo.html', context)



@login_required
def eliminar_prestamo(request, pk):
    """
    Permite eliminar un préstamo específico.
    """
    prestamo = get_object_or_404(Prestamo, pk=pk)
    
    if request.method == 'POST':
        empleado_nombre = f"{prestamo.id_empleado.nombre} {prestamo.id_empleado.apellido}"
        prestamo.delete()
        messages.success(request, f"Préstamo de {empleado_nombre} eliminado exitosamente.")
        return redirect('listar_prestamos')
    
    
    context = {
        'prestamo': prestamo,
        'titulo': f'Confirmar Eliminación de Préstamo para {prestamo.id_empleado.nombre} {prestamo.id_empleado.apellido}'
    }
    return render(request, 'confirmar_eliminar_prestamo.html', context)


@login_required
def eliminar_todos_los_prestamos(request):
    """
    Elimina todos los préstamos del sistema. Requiere confirmación POST.
    """
    if request.method == 'POST':
        count, _ = Prestamo.objects.all().delete()
        messages.success(request, f"{count} préstamos han sido eliminados del sistema.")
        return redirect('listar_prestamos')
    
    context = {
        'titulo': 'Confirmar Eliminación de TODOS los Préstamos',
        'cantidad_prestamos': Prestamo.objects.count(),
    }
    return render(request, 'confirmar_eliminar_todos_prestamos.html', context)


@login_required
def crear_concepto_nomina(request):
    """
    Permite a los administradores crear un nuevo concepto/regla de nómina (ParametrosNomina).
    """
    print("--- Entrando a crear_concepto_nomina ---")
    
    
    if request.method == 'POST':
        form = ParametrosNominaForm(request.POST)
        
        if form.is_valid():
            print("Formulario de ParametrosNominaForm es VÁLIDO. Guardando nuevo concepto.")
            
            nuevo_concepto = form.save() 
            
            messages.success(request, f"Concepto de Nómina '{nuevo_concepto.nombre}' creado exitosamente.")
            
            return redirect('home') 
        else:
            messages.error(request, 'Error al crear el concepto. Por favor, revise el formulario.')
    else:
        form = ParametrosNominaForm()

    context = {
        'form': form,
        'titulo': 'Añadir Nuevo Concepto/Regla de Nómina',
        'subtitulo': 'Defina una nueva regla de asignación o deducción para la nómina.',
        # 'parametros' 
    }
    
    return render(request, 'form_concepto_nomina.html', context)

@login_required
def editar_parametros_nomina(request):
    """
    Permite a los administradores editar los parámetros 
    globales de nómina (IVSS, RPE, FAOV).
    """
    try:
        parametros = ParametrosNomina.objects.first()
        if not parametros:
            parametros = ParametrosNomina.objects.create(tasa_ivss=0, tasa_rpe=0, tasa_faov=0)
            messages.info(request, "Se creó la instancia inicial de Parámetros de Nómina.")
            
    except Exception as e:
        messages.error(request, f"Error al cargar los parámetros: {e}")
        return redirect('home')

    if request.method == 'POST':
        form = ParametrosNominaForm(request.POST, instance=parametros)
        if form.is_valid():
            parametro_guardado = form.save(commit=False)
            parametro_guardado.fecha_ultima_actualizacion = timezone.now()
            parametro_guardado.save()
            
            messages.success(request, 'Parámetros de Nómina actualizados exitosamente.')
            return redirect('home') 
    else:
        form = ParametrosNominaForm(instance=parametros)

    context = {
        'form': form,
        'titulo': 'Editar Parámetros Globales de Nómina',
        'subtitulo': 'Establezca las tasas de deducción (IVSS, RPE, FAOV) en porcentaje (0-100).',
        'parametros': parametros, 
    }
    return render(request, 'editar_parametros_nomina.html', context)



def sueldo_labor_list_create(request):
    """
    Muestra la lista de SueldoLabor (Sueldo base USD por cargo) y 
    permite crear nuevos registros.
    """
    sueldos_labor = SueldoLabor.objects.all().order_by('id_labor__nombre_trabajo')
    
    if request.method == 'POST':
        form = SueldoLaborForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sueldo base en USD por Labor creado exitosamente.')
            return redirect('sueldo_labor_list_create') 
        else:
            messages.error(request, 'Error al crear el sueldo por Labor. Revise los campos.')
    else:
        form = SueldoLaborForm() 

    context = {
        'sueldos_labor': sueldos_labor,
        'form': form,
        'titulo': 'Gestión de Sueldos Base (USD) por Cargo',
    }
    return render(request, 'sueldo_labor_list_create.html', context)


@login_required
def sueldo_labor_list_create(request):
    """
    Muestra la lista de SueldoLabor (Sueldo base USD por cargo) y 
    permite crear nuevos registros.
    """

    sueldos_labor = SueldoLabor.objects.all().order_by('id_labor')
    paginator = Paginator(sueldos_labor, 2)  

    page_number = request.GET.get('page')
    try:
        sueldos_labor = paginator.page(page_number)
    except PageNotAnInteger:
        sueldos_labor = paginator.page(1)
    except EmptyPage:
        sueldos_labor = paginator.page(paginator.num_pages)

    
    if request.method == 'POST':
        form = SueldoLaborForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sueldo base en USD por Labor creado exitosamente.')
            return redirect('sueldo_labor_list_create') 
        else:
            messages.error(request, 'Error al crear el sueldo por Labor. Revise los campos.')
    else:
        form = SueldoLaborForm() 

    context = {
        'sueldos_labor': sueldos_labor,
        'form': form,
        'titulo': 'Gestión de Sueldos Base (USD) por Cargo',
    }




    
    return render(request, 'sueldo_labor_list_create.html', context)

@login_required
def sueldo_labor_edit(request, pk):
    """
    Permite editar un registro SueldoLabor existente.
    """
    sueldo_labor = get_object_or_404(SueldoLabor, pk=pk)
    
    if request.method == 'POST':
        form = SueldoLaborForm(request.POST, instance=sueldo_labor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Sueldo para {sueldo_labor.id_labor.nombre_trabajo} actualizado.')
            return redirect('sueldo_labor_list_create') 
    else:
        form = SueldoLaborForm(instance=sueldo_labor)
        form.fields['id_labor'].widget.attrs['readonly'] = 'readonly'
        form.fields['id_labor'].widget.attrs['disabled'] = 'disabled' 

    context = {
        'sueldo_labor': sueldo_labor,
        'form': form,
        'titulo': f'Editar Sueldo Base para: {sueldo_labor.id_labor.nombre_trabajo}',
    }
    return render(request, 'sueldo_labor_edit.html', context)


@login_required
def gestionar_conceptos_nomina(request):
    """
    Muestra la lista de todos los conceptos de nómina.
    """
    conceptos = ParametrosNomina.objects.all().order_by('nombre') 
    
    context = {
        'conceptos': conceptos,
        'titulo': 'Gestión de Conceptos/Reglas de Nómina',
        'subtitulo': 'Lista de asignaciones y deducciones para el cálculo de nómina.',
    }
    return render(request, 'gestionar_conceptos_nomina.html', context)


@login_required
def editar_concepto_nomina(request, pk):
    """
    Permite editar un concepto de nómina específico por su ID (pk).
    """
    concepto = get_object_or_404(ParametrosNomina, pk=pk)

    if request.method == 'POST':
        form = ParametrosNominaForm(request.POST, instance=concepto)
        if form.is_valid():
            form.save()
            messages.success(request, f"Concepto '{concepto.nombre}' actualizado exitosamente.")
            return redirect('gestionar_conceptos_nomina')
        else:
            messages.error(request, 'Error al actualizar. Por favor, revise el formulario.')
    else:
        form = ParametrosNominaForm(instance=concepto)

    context = {
        'form': form,
        'titulo': f"Editar Concepto: {concepto.nombre}",
        'subtitulo': 'Modifique los valores o la periodicidad de este concepto.',
    }
    return render(request, 'form_concepto_nomina.html', context)


@login_required
def eliminar_concepto_nomina(request, pk):
    """
    Elimina un concepto de nómina por su ID (pk) tras una confirmación POST.
    """
    concepto = get_object_or_404(ParametrosNomina, pk=pk)
    
    if request.method == 'POST':
        nombre_eliminado = concepto.nombre
        concepto.delete()
        messages.success(request, f"Concepto '{nombre_eliminado}' eliminado exitosamente.")
        return redirect('gestionar_conceptos_nomina')
    
    context = {
        'concepto': concepto,
        'titulo': 'Confirmar Eliminación',
        'subtitulo': f'¿Está seguro que desea eliminar el concepto "{concepto.nombre}"? Esta acción es irreversible.',
    }
    return render(request, 'confirmar_eliminacion_concepto.html', context)