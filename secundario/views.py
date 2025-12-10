
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Empleado,  Tasa, Nomina, Sueldo, TipoDeJornada, Departamento, Profesion, Labor, TipoDeJornada, Asistencia, Asistenciaconfirmada, Usuarios, PrestacionSocialAcumulada,  Liquidacion, Prestamo, NominaNueva, ItemNomina,ConceptoNomina
from .forms import EmpleadoForm, SueldoForm, SuperuserForm, DepartamentoForm, ProfesionForm, LaborForm, TipoDeJornadaForm, NominaForm, BuscarNominaForm, AsistenciaForm, NominaGrupalForm, SueldoGrupalForm, LiquidacionGrupalForm, LiquidacionForm,PrestamoForm, NominaNuevaForm
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib import messages
from datetime import datetime, timedelta
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
from django.template.loader import render_to_string
from weasyprint import HTML
import io

VENEZUELAN_HOLIDAYS = [
    (1, 1),    # Año Nuevo
    (1, 6),    # Día de Reyes (sometimes observed)
    (2, 12),   # Día de la Juventud (movable, approximate)
    (3, 19),   # Día de San José (sometimes observed)
    (4, 19),   # Declaración de la Independencia
    (5, 1),    # Día del Trabajador
    (6, 24),   # Batalla de Carabobo
    (7, 5),    # Día de la Independencia
    (7, 24),   # Natalicio del Libertador
    (10, 12),  # Día de la Resistencia Indígena
    (12, 24),  # Víspera de Navidad (half-day or full-day)
    (12, 25),  # Navidad
    (12, 31),  # Víspera de Año Nuevo (half-day or full-day)
    
]

def is_holiday(date):
    return (date.month, date.day) in VENEZUELAN_HOLIDAYS

"""
Logica relacionada con la autenticación de usuarios, incluyendo inicio de sesión, cierre de sesión y creación de superusuarios.
"""
def es_superusuario(user):
    return user.is_superuser  

@user_passes_test(es_superusuario, login_url='pagina_no_autorizada')  
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
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    if user.is_superuser:
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
def crear_superuser(request):
    """
    Permite a un usuario autenticado crear un nuevo superusuario.
    """
    if request.method == 'POST':
        form = SuperuserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Usuario creado exitosamente!')
            return redirect('login')
    else:
        form = SuperuserForm()
    return render(request, 'registrarusuario.html', {'form': form})

"""
Todo lo relacionado a empleado(Listar, Crear, Eliminar y Actualizar)
"""
@login_required
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
def editar_empleado(request, empleado_id):
    """
    Permite editar un registro existente de empleado.
    """
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
def home(request):
    """
    Muestra la página de inicio, listando las nóminas existentes con paginación.
    """
    nominas_list = Nomina.objects.all().order_by('-fecha_emision', 'id_nomina') 
    paginator = Paginator(nominas_list, 4)  

    page_number = request.GET.get('page')
    try:
        nominas = paginator.page(page_number)
    except PageNotAnInteger:
        nominas = paginator.page(1)
    except EmptyPage:
        nominas = paginator.page(paginator.num_pages)

    return render(request, 'home.html', {'nominas': nominas})

"""
Gestión de sueldos: listado, creación individual y grupal, edición y eliminación de registros de sueldos.
También incluye la lógica para actualizar la tasa de cambio.
"""
@login_required
def sueldo_list(request):
    """
    Muestra un listado de todos los sueldos registrados.
    """
    sueldos = Sueldo.objects.all().select_related('id_empleado', 'id_tasa', 'id_jornada')
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
                    fecha = datetime.strptime(fecha_actualizacion[:10], "%Y-%m-%d").date()
                    
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
def sueldo_create(request):
    """
    Permite la creación de un nuevo registro de sueldo para un empleado.
    """
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

@login_required
def generar_sueldo_grupal(request):
    """
    Genera o actualiza sueldos de forma grupal para empleados filtrados por labor.
    """
    if request.method == 'POST':
        print("--- Entrando a generar_sueldo_grupal (POST) ---")
        form = SueldoGrupalForm(request.POST)
        if form.is_valid():
            selected_labor = form.cleaned_data['labor']
            selected_jornada = form.cleaned_data['jornada']
            selected_tasa = form.cleaned_data['tasa']

            empleados_en_labor = Empleado.objects.filter(id_trabajo=selected_labor)
            sueldos_generados = []
            errores_generacion = []

            if not empleados_en_labor.exists():
                messages.warning(request, f"No se encontraron empleados para la labor '{selected_labor.nombre_trabajo}'.")
                return render(request, 'generar_sueldo_grupal.html', {'form': form})

            for empleado in empleados_en_labor:
                try:
                    existing_sueldo = Sueldo.objects.filter(
                        id_empleado=empleado,
                        id_jornada=selected_jornada,
                        id_tasa=selected_tasa
                    ).first()

                    if existing_sueldo:
                        existing_sueldo.save() 
                        sueldos_generados.append(f"Sueldo actualizado para {empleado.nombre} {empleado.apellido}")
                        messages.info(request, f"Sueldo actualizado para {empleado.nombre} {empleado.apellido} (ya existía).")
                    else:
                        sueldo = Sueldo(
                            id_empleado=empleado,
                            id_jornada=selected_jornada,
                            id_tasa=selected_tasa
                        )
                        sueldo.save() 
                        sueldos_generados.append(f"Sueldo generado para {empleado.nombre} {empleado.apellido}")
                        messages.success(request, f"Sueldo generado para {empleado.nombre} {empleado.apellido}.")

                except Exception as e:
                    error_msg = f"Error al generar/actualizar sueldo para {empleado.nombre} {empleado.apellido}: {e}"
                    messages.error(request, error_msg)
                    errores_generacion.append(error_msg)
                    print(f"--- ERROR: {error_msg} ---")

            return render(request, 'sueldo_grupal_resultado.html', {
                'sueldos_generados': sueldos_generados,
                'errores_generacion': errores_generacion,
                'selected_labor': selected_labor
            })
        else:
            messages.error(request, 'Error en el formulario de generación grupal de sueldos. Por favor, revise los datos.')
            print("Errores del formulario SueldoGrupalForm:", form.errors)
    else:
        form = SueldoGrupalForm()

    return render(request, 'generar_sueldo_grupal.html', {'form': form})

@login_required
def sueldo_lista(request):
    """
    Muestra un listado de todos los sueldos registrados (duplicado de sueldo_list, se puede refactorizar).
    """
    sueldos = Sueldo.objects.all()
    return render(request, 'sueldo_lista.html', {'sueldos': sueldos})

@login_required
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
def exportar_nomina_pdf(request, id_nomina):
    """
    Genera y exporta una nómina específica como un archivo PDF.
    """
    nomina = Nomina.objects.get(id_nomina=id_nomina)
    template_path = 'exportar_nomina_pdf.html'
    context = {'nomina': nomina}
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="nomina_{nomina.id_nomina}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error al generar PDF')
    return response

"""
CRUD para inasistencias
elimina, actualiza, crea y lee datos para inasistencias
"""
@login_required
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
                        asistencia_obj.hora_entrada = current_time_dt #
                        asistencia_obj.asistio = True
                        asistencia_obj.save()
                        messages.success(request, f"Entrada registrada para {empleado_encontrado.nombre} {empleado_encontrado.apellido} a las {current_time_dt.strftime('%H:%M')}.")
                    else:
                        messages.info(request, f"La entrada para {empleado_encontrado.nombre} {empleado_encontrado.apellido} ya fue registrada hoy a las {asistencia_obj.hora_entrada.strftime('%H:%M')}.")
                else:
                    messages.success(request, f"Entrada registrada para {empleado_encontrado.nombre} {empleado_encontrado.apellido} a las {current_time_dt.strftime('%H:%M')}.")

            elif 'registrar_salida' in request.POST:
                if asistencia_hoy and not asistencia_hoy.hora_salida:
                    asistencia_hoy.hora_salida = current_time_dt 
                    asistencia_hoy.save()
                    messages.success(request, f"Salida registrada para {empleado_encontrado.nombre} {empleado_encontrado.apellido} a las {current_time_dt.strftime('%H:%M')}.")
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

"""
Todo lo relacionado a la creacion de nominas
"""
def nomina_create(request):
    if request.method == 'POST':
        print("--- Entrando a nomina_create (POST) ---")
        form = NominaForm(request.POST)

        print("Datos POST recibidos:", request.POST)

        if form.is_valid():
            print("Formulario de Nomina es VÁLIDO.")
            try:
                nomina = form.save(commit=False)
                if 'id_sueldo' in request.POST and request.POST['id_sueldo']:
                    nomina.id_sueldo_id = request.POST['id_sueldo']
                    print(f"Asignando id_sueldo_id: {nomina.id_sueldo_id}")
                else:
                    print("Advertencia: id_sueldo no encontrado en POST o está vacío.")
                    
                    messages.error(request, "Error: No se ha seleccionado un sueldo para la nómina.")
                    empleados = Empleado.objects.all()
                    sueldos = Sueldo.objects.all()
                    return render(request, 'crear_nomina.html', {'empleados': empleados, 'sueldos': sueldos, 'form': form})

                nomina.save()
                messages.success(request, 'Nómina creada exitosamente!')
                print("Nómina guardada con éxito:", nomina)
                return redirect('home')
            except Exception as e:
                messages.error(request, f'Error al guardar la nómina: {e}')
                print(f"--- ERROR al guardar la nómina: {e} ---")
                
                empleados = Empleado.objects.all()
                sueldos = Sueldo.objects.all()
                return render(request, 'crear_nomina.html', {'empleados': empleados, 'sueldos': sueldos, 'form': form})
        else:
            print("Formulario de Nomina NO es VÁLIDO.")
            print("Errores del formulario:", form.errors)
            messages.error(request, 'Error en el formulario. Por favor, revise los datos.')
            
            empleados = Empleado.objects.all()
            sueldos = Sueldo.objects.all()
            return render(request, 'crear_nomina.html', {'empleados': empleados, 'sueldos': sueldos, 'form': form})
    else:
        print("--- Entrando a nomina_create (GET) ---")
        form = NominaForm()
        empleados = Empleado.objects.all()
        sueldos = Sueldo.objects.all()
        return render(request, 'crear_nomina.html', {'empleados': empleados, 'sueldos': sueldos, 'form': form})


@login_required
def generar_nomina_grupal(request):
    if request.method == 'POST':
        print("--- Entrando a generar_nomina_grupal (POST) ---")
        form = NominaGrupalForm(request.POST)
        print("Datos POST recibidos para nómina grupal:", request.POST)

        if form.is_valid():
            print("Formulario de NominaGrupalForm es VÁLIDO.")
            labor_seleccionada = form.cleaned_data['labor']
            tipo_periodo = form.cleaned_data['tipo_periodo']
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']

            try:
                ultima_tasa = Tasa.objects.latest('fecha')
                valor_tasa_por_falta = ultima_tasa.valor_tasa
            except Tasa.DoesNotExist:
                messages.error(request, "No se ha definido ninguna tasa en el sistema. No se puede calcular la deducción por inasistencias o préstamos si la tasa influye en el cálculo de cuotas de préstamos.")
                return render(request, 'generar_nomina_grupal.html', {'form': form})
            except Exception as e:
                messages.error(request, f"Error al obtener la última tasa: {e}")
                return render(request, 'generar_nomina_grupal.html', {'form': form})

            empleados_por_labor = Empleado.objects.filter(id_trabajo=labor_seleccionada)
            
            nominas_generadas = []
            errores_generacion = []

            if not empleados_por_labor.exists():
                messages.warning(request, f"No se encontraron empleados para la labor '{labor_seleccionada.nombre_trabajo}'.")
                return render(request, 'generar_nomina_grupal.html', {'form': form})

            dias_en_periodo = (fecha_fin - fecha_inicio).days + 1
            
            unidad_tributaria_valor = Decimal('43.0')
            factor_calculo_cestaticket = Decimal('8.0')

            monto_diario_cestaticket = unidad_tributaria_valor * factor_calculo_cestaticket
            cestaticket_bs_calculado = monto_diario_cestaticket * Decimal(str(dias_en_periodo))


            for empleado in empleados_por_labor:
                total_faltas_empleado = Asistencia.objects.filter(
                    id_empleado=empleado,
                    asistio=False,
                    tipo_inasistencia='injustificada',
                    fecha_asistencia__range=[fecha_inicio, fecha_fin]
                ).count()
                pago_inasistencias_bs = Decimal(str(total_faltas_empleado)) * valor_tasa_por_falta

                total_deduccion_prestamo_bs = Decimal('0.00')
                prestamos_activos_empleado = Prestamo.objects.filter(
                    id_empleado=empleado,
                    activo=True,
                    monto_pendiente_bs__gt=Decimal('0.00'),
                    aprobado=True
                ).order_by('fecha_solicitud')

                for prestamo in prestamos_activos_empleado:
                    monto_a_deducir_en_esta_nomina = prestamo.monto_cuota_bs
                    
                    if monto_a_deducir_en_esta_nomina > prestamo.monto_pendiente_bs:
                        monto_a_deducir_en_esta_nomina = prestamo.monto_pendiente_bs

                    total_deduccion_prestamo_bs += monto_a_deducir_en_esta_nomina
                    
                    prestamo.monto_pendiente_bs -= monto_a_deducir_en_esta_nomina
                    if prestamo.cuotas_restantes > 0:
                        prestamo.cuotas_restantes -= 1
                    
                    if prestamo.monto_pendiente_bs <= Decimal('0.00'):
                        prestamo.activo = False
                        prestamo.monto_pendiente_bs = Decimal('0.00')
                        prestamo.cuotas_restantes = 0
                        messages.info(request, f"Préstamo #{prestamo.id_prestamo} de {empleado.nombre} {empleado.apellido} ha sido saldado.")

                    prestamo.save()
                

                total_horas_ordinarias_confirmadas = Decimal('0.00')
                total_horas_extras = Decimal('0.00')
                total_pago_horas_extras_bs = Decimal('0.00')
                total_horas_festivas = Decimal('0.00')
                total_pago_horas_festivas_bs = Decimal('0.00')

                try:
                    sueldo_empleado = Sueldo.objects.get(id_empleado=empleado)
                    print(f"Sueldo encontrado para {empleado.nombre} {empleado.apellido}: {sueldo_empleado.sueldo_bs} BS")
                    
                    sueldo_semanal_usd = sueldo_empleado.id_jornada.sueldo_semanal_usd
                    valor_tasa_sueldo = sueldo_empleado.id_tasa.valor_tasa
                    sueldo_semanal_bs = sueldo_semanal_usd * valor_tasa_sueldo

                    sueldo_bs_base_periodo = Decimal('0.00')

                    if tipo_periodo == 'semanal':
                        sueldo_bs_base_periodo = sueldo_semanal_bs
                    
                    if empleado.id_jornada.horas_semanales > 0:
                        tarifa_hora_ordinaria_bs = sueldo_semanal_bs / Decimal(str(empleado.id_jornada.horas_semanales))
                    else:
                        tarifa_hora_ordinaria_bs = Decimal('0.00')

                    tarifa_hora_extra_bs = tarifa_hora_ordinaria_bs * Decimal('1.5')
                    tarifa_hora_festiva_bs = tarifa_hora_ordinaria_bs * Decimal('2.0')

                    horas_diarias_regulares_jornada = Decimal('0.00')
                    if empleado.id_jornada.horas_semanales > 0:
                        horas_diarias_regulares_jornada = Decimal(str(empleado.id_jornada.horas_semanales)) / Decimal('5.0')
                        
                        
                    current_date = fecha_inicio
                    while current_date <= fecha_fin:
                        try:
                            asistencia_diaria = Asistencia.objects.get(
                                id_empleado=empleado,
                                fecha_asistencia=current_date,
                            )
                            if asistencia_diaria.hora_entrada and asistencia_diaria.hora_salida:
                                entrada_dt = datetime.combine(current_date, asistencia_diaria.hora_entrada)
                                salida_dt = datetime.combine(current_date, asistencia_diaria.hora_salida)
                                
                                if salida_dt < entrada_dt:
                                    salida_dt += timedelta(days=1)

                                duracion = salida_dt - entrada_dt
                                horas_trabajadas_hoy = Decimal(duracion.total_seconds() / 3600)

                                es_fin_de_semana = (current_date.weekday() == 5 or current_date.weekday() == 6)
                                es_feriado = is_holiday(current_date)
                                if es_fin_de_semana or es_feriado:
                                    total_horas_festivas += horas_trabajadas_hoy
                                    total_pago_horas_festivas_bs += (horas_trabajadas_hoy * tarifa_hora_festiva_bs)
                                else:
                                    if horas_trabajadas_hoy > horas_diarias_regulares_jornada:
                                        horas_extra_hoy = horas_trabajadas_hoy - horas_diarias_regulares_jornada
                                        total_horas_extras += horas_extra_hoy
                                        total_pago_horas_extras_bs += (horas_extra_hoy * tarifa_hora_extra_bs)
                                        total_horas_ordinarias_confirmadas += horas_diarias_regulares_jornada
                                    else:
                                        total_horas_ordinarias_confirmadas += horas_trabajadas_hoy
                        except Asistencia.DoesNotExist:
                            pass
                        except Exception as e:
                            print(f"Error processing attendance for {empleado.nombre} on {current_date}: {e}")

                        current_date += timedelta(days=1)

                    total_asignaciones_bs = (
                        sueldo_bs_base_periodo +
                        cestaticket_bs_calculado +
                        total_pago_horas_extras_bs +
                        total_pago_horas_festivas_bs
                    )

                    ivss_bs = total_asignaciones_bs * Decimal('0.04')
                    rpe_bs = total_asignaciones_bs * Decimal('0.01')
                    faov_bs = total_asignaciones_bs * Decimal('0.02')
                    
                    total_deducciones_bs = ivss_bs + rpe_bs + faov_bs + pago_inasistencias_bs + total_deduccion_prestamo_bs
                    
                    sueldo_neto_bs = total_asignaciones_bs - total_deducciones_bs

                    
                    print(f"Calculando para {empleado.nombre} {empleado.apellido}:")
                    print(f"   Sueldo Base Periodo: {sueldo_bs_base_periodo}")
                    print(f"   Tarifa Hora Ordinaria: {tarifa_hora_ordinaria_bs}")
                    print(f"   Tarifa Hora Extra: {tarifa_hora_extra_bs}")
                    print(f"   Tarifa Hora Festiva: {tarifa_hora_festiva_bs}")
                    print(f"   Cestaticket: {cestaticket_bs_calculado}")
                    print(f"   Horas Ordinarias Confirmadas: {total_horas_ordinarias_confirmadas}")
                    print(f"   Total Horas Extras: {total_horas_extras}")
                    print(f"   Pago Horas Extras: {total_pago_horas_extras_bs}")
                    print(f"   Total Horas Festivas: {total_horas_festivas}")
                    print(f"   Pago Horas Festivas: {total_pago_horas_festivas_bs}")
                    print(f"   Total Asignaciones: {total_asignaciones_bs}")
                    print(f"   Deducción por Inasistencias (Injustificadas): {pago_inasistencias_bs:.2f} Bs (Faltas: {total_faltas_empleado})")
                    print(f"   Deducción por Préstamo: {total_deduccion_prestamo_bs:.2f} Bs")
                    print(f"   Total Deducciones: {total_deducciones_bs}")
                    print(f"   Sueldo Neto: {sueldo_neto_bs}")

                    nomina = Nomina(
                        id_empleado=empleado,
                        id_sueldo=sueldo_empleado,
                        id_trabajo=labor_seleccionada,
                        periodo_inicio=fecha_inicio,
                        periodo_fin=fecha_fin,
                        tipo_periodo=tipo_periodo,
                        sueldo_bs_base=round(sueldo_bs_base_periodo, 2),
                        cestaticket_bs=round(cestaticket_bs_calculado, 2),
                        horas_extras=round(total_horas_extras, 2),
                        horas_ordinarias=round(total_horas_ordinarias_confirmadas, 2),
                        pago_horas_extras_bs=round(total_pago_horas_extras_bs, 2),
                        horas_festivas=round(total_horas_festivas, 2),
                        pago_horas_festivas_bs=round(total_pago_horas_festivas_bs, 2),
                        dias_vacaciones=0,
                        dias_enfermedad=total_faltas_empleado,
                        
                        total_asignaciones_bs=round(total_asignaciones_bs, 2),
                        ivss_bs=round(ivss_bs, 2),
                        rpe_bs=round(rpe_bs, 2),
                        faov_bs=round(faov_bs, 2),
                        pago_inasistencias_bs=round(pago_inasistencias_bs, 2),
                        pago_prestamo_bs=round(total_deduccion_prestamo_bs, 2),
                        total_deducciones_bs=round(total_deducciones_bs, 2),
                        sueldo_neto_bs=round(sueldo_neto_bs, 2),
                    )
                    nomina.save()
                    nominas_generadas.append(f"Nómina generada para {empleado.nombre} {empleado.apellido}. (Faltas: {total_faltas_empleado}, Deducción Faltas: {pago_inasistencias_bs:.2f} Bs, Deducción Préstamo: {total_deduccion_prestamo_bs:.2f} Bs)")
                    messages.success(request, f"Nómina generada para {empleado.nombre} {empleado.apellido}.")
                    print(f"Nómina guardada para {empleado.nombre} {empleado.apellido}.")

                except Sueldo.DoesNotExist:
                    error_msg = f"No se pudo generar la nómina para {empleado.nombre} {empleado.apellido}: No tiene un sueldo asignado."
                    messages.warning(request, error_msg)
                    errores_generacion.append(error_msg)
                    print(error_msg)
                except Exception as e:
                    error_msg = f"Error al generar nómina para {empleado.nombre} {empleado.apellido}: {e}"
                    messages.error(request, error_msg)
                    errores_generacion.append(error_msg)
                    print(f"--- ERROR: {error_msg} ---")
            
            return render(request, 'nomina_grupal_generada.html', {
                'nominas_generadas': nominas_generadas,
                'errores_generacion': errores_generacion
            })
        else:
            print("Formulario de NominaGrupalForm NO es VÁLIDO.")
            print("Errores del formulario NominaGrupalForm:", form.errors)
            messages.error(request, 'Error en el formulario de generación grupal. Por favor, revise los datos.')
            return render(request, 'generar_nomina_grupal.html', {'form': form})
    else:
        print("--- Entrando a generar_nomina_grupal (GET) ---")
        form = NominaGrupalForm()
    
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
"""
def calcular_liquidacion_detalle(empleado, fecha_fin_relacion, motivo_terminacion, dias_utilidades_empresa=Decimal('30')):
 
    fecha_ingreso = empleado.fecha_contratacion
    antiguedad_relativa = relativedelta(fecha_fin_relacion, fecha_ingreso)
    antiguedad_anios = antiguedad_relativa.years
    antiguedad_meses = antiguedad_relativa.months
    antiguedad_dias = antiguedad_relativa.days

    salario_normal_final = calcular_salario_normal(empleado, fecha_fin_relacion)
    salario_integral_final = calcular_salario_integral(empleado, fecha_fin_relacion, dias_utilidades_empresa)

    # 1. Prestaciones Sociales (Art. 142 LOTTT) 
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

    #2. Vacaciones No Disfrutadas y Bono Vacacional (Art. 192, 193 LOTTT) 
    dias_vacaciones_pendientes_calc = Decimal('0.00')
    monto_vacaciones_pendientes = Decimal('0.00')
    dias_bono_vacacional_pendiente_calc = Decimal('0.00')
    monto_bono_vacacional_pendiente = Decimal('0.00')

    if antiguedad_anios >= 1:
        dias_vacaciones_por_ano = Decimal('15') + min(Decimal(antiguedad_anios) - 1, Decimal('15'))
        dias_bono_vacacional_por_ano = Decimal('15') + min(Decimal(antiguedad_anios) - 1, Decimal('15'))
        
        fecha_ultimo_aniversario = empleado.fecha_contratacion + relativedelta(years=antiguedad_anios)
        dias_trabajados_ultimo_periodo = (fecha_fin_relacion - fecha_ultimo_aniversario).days

        if dias_trabajados_ultimo_periodo > 0 :
            meses_trabajados_ultimo_periodo_dec = Decimal(dias_trabajados_ultimo_periodo) / Decimal('30')
            
            dias_vacaciones_pendientes_calc = (dias_vacaciones_por_ano / Decimal('12')) * meses_trabajados_ultimo_periodo_dec
            dias_bono_vacacional_pendiente_calc = (dias_bono_vacacional_por_ano / Decimal('12')) * meses_trabajados_ultimo_periodo_dec
            
    monto_vacaciones_pendientes = (salario_normal_final / Decimal('30')) * dias_vacaciones_pendientes_calc.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    monto_bono_vacacional_pendiente = (salario_normal_final / Decimal('30')) * dias_bono_vacacional_pendiente_calc.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

   # 3. Utilidades Pendientes (Art. 131 LOTTT) 
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

        minimo_legal_utilidades = (salario_normal_final / Decimal('30')) * Decimal('30') # 30 días de salario normal
        maximo_legal_utilidades = (salario_normal_final / Decimal('30')) * Decimal('120') # 120 días de salario normal

        monto_utilidades_pendientes = max(minimo_legal_utilidades, min(monto_calculado_utilidades, maximo_legal_utilidades))
        

    # 4. Indemnización por Despido Injustificado (Art. 92 LOTTT) 
    monto_indemnizacion_despido = Decimal('0.00')
    if motivo_terminacion == 'despido_injustificado':
        anios_para_indemnizacion = Decimal(antiguedad_anios)
        if antiguedad_meses >= 6: 
            anios_para_indemnizacion += Decimal('1')
        
        anios_para_indemnizacion = min(anios_para_indemnizacion, Decimal('11'))
        
        monto_indemnizacion_despido = salario_integral_final * anios_para_indemnizacion

    # 5. Preaviso (Art. 81 LOTTT) 
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

    # Total Liquidación 
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
    }
"""
def calcular_salario_integral(empleado, fecha_fin_relacion, dias_utilidades_empresa):

    return calcular_salario_normal(empleado, fecha_fin_relacion) * Decimal('1.3') 

def calcular_liquidacion_detalle(empleado, fecha_fin_relacion, motivo_terminacion, dias_utilidades_empresa=Decimal('30'), dias_vacaciones_otorgados=None):
    """
    Función principal para calcular todos los componentes de la liquidación de un empleado.
.
    """
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
    salario_integral_final = calcular_salario_integral(empleado, fecha_fin_relacion, dias_utilidades_empresa)

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

    if motivo_terminacion != 'vacaciones':  # Solo calculamos vacaciones pendientes si no es por vacaciones
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

        minimo_legal_utilidades = (salario_normal_final / Decimal('30')) * Decimal('30') # 30 días de salario normal
        maximo_legal_utilidades = (salario_normal_final / Decimal('30')) * Decimal('120') # 120 días de salario normal

        monto_utilidades_pendientes = max(minimo_legal_utilidades, min(monto_calculado_utilidades, maximo_legal_utilidades))
        

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
            
            # Agarra los dias si el motivo es vacaciones
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

            # VERIFICACION DE ERROR
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
                # Campos específicos para vacaciones
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
@user_passes_test(es_superusuario, login_url='pagina_no_autorizada')
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



def generar_nomina_nueva(request):
    if request.method == 'POST':
        form = NominaNuevaForm(request.POST)
        if form.is_valid():
            nomina = form.save()

            # === Generar ítems automáticos ===
            conceptos = ConceptoNomina.objects.all()
            for concepto in conceptos:
                item = ItemNomina(nomina=nomina, concepto=concepto)
                if concepto.es_por_dias:
                    item.cantidad = nomina.dias_trabajados()
                item.save()

            # === Deducción de préstamo activo ===
            prestamo = Prestamo.objects.filter(
                id_empleado=nomina.empleado,
                activo=True,
                cuotas_restantes__gt=0
            ).first()
            if prestamo:
                deduccion = ItemNomina(
                    nomina=nomina,
                    concepto=ConceptoNomina.objects.get(codigo='PRESTAMO'),
                    cantidad=1,
                    monto=prestamo.monto_cuota_bs
                )
                deduccion.save()
                prestamo.cuotas_restantes -= 1
                prestamo.monto_pendiente_bs -= prestamo.monto_cuota_bs
                if prestamo.cuotas_restantes <= 0:
                    prestamo.activo = False
                prestamo.save()

            messages.success(request, "Nómina generada correctamente.")
            return redirect('nomina_pdf_nueva', nomina_id=nomina.id)
    else:
        form = NominaNuevaForm()

    return render(request, 'generar_nomina_nueva.html', {'form': form})


def nomina_pdf_nueva(request, nomina_id):
    nomina = get_object_or_404(NominaNueva, id=nomina_id)
    for item in nomina.items.all():
        item.save()  # Recalcula

    context = {
        'nomina': nomina,
        'hoy': timezone.now().date(),
        'instituto': {
            'nombre': 'KINKIWOKYIN EXPRESS',
            'sigla': 'Queso Express',
            'rif': 'J-075712846'
        }
    }

    html = render_to_string('nomina/pdf_nomina_nueva.html', context)
    pdf = HTML(string=html).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="nomina_{nomina.empleado.cedula}_{nomina.estado}.pdf"'
    return response

