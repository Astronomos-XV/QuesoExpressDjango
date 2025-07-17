from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Empleado,  Tasa, Nomina, Sueldo, TipoDeJornada, Departamento, Profesion, Labor, TipoDeJornada, Asistencia, Asistenciaconfirmada, Usuarios, PrestacionSocialAcumulada
from .forms import EmpleadoForm, SueldoForm, SuperuserForm, DepartamentoForm, ProfesionForm, LaborForm, TipoDeJornadaForm, NominaForm, BuscarNominaForm, AsistenciaForm, NominaGrupalForm, SueldoGrupalForm
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib import messages
from datetime import datetime, timedelta
from django.views.generic import ListView
from django.utils import timezone
from django.db.models import Q
import requests
from decimal import Decimal, InvalidOperation

"""
Logica relacionada con la autenticación de usuarios, incluyendo inicio de sesión, cierre de sesión y creación de superusuarios.

"""



def es_superusuario(user):
    return user.is_superuser  

@user_passes_test(es_superusuario, login_url='pagina_no_autorizada')  
def vista_empleado(request):
    return render(request, 'empleadopagina.html')  


def cerrar_sesion(request):
    logout(request)
    return redirect('login')


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

def crear_superuser(request):
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


"""
Vista principal del sistema, mostrando un listado de nóminas, accesible solo para superusuarios(administradores)

"""

@login_required

def home(request):
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
    sueldos = Sueldo.objects.all().select_related('id_empleado', 'id_tasa', 'id_jornada')
    return render(request, 'sueldo_lista.html', {'sueldos': sueldos})

#Aqui estas funciones tienen el objetivo de actualizar la tasa y guardar esa actualizacion en el modelo llamado tasa

def actualizar_tasa():
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
    success, message = actualizar_tasa() 
    tasas = Tasa.objects.all()
    
    return render(request, 'tasa.html', {
        'tasas': tasas,
        'message': message,
        'success': success
    })









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



@login_required
def generar_sueldo_grupal(request):
    if request.method == 'POST':
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






"""
Gestiona exclusivamente todo lo relacionado a departamentos profesiones labores y jornadas Un Crud unificado para los 4

"""

@login_required
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





"""
Busquedad de nomina por numero de cedula del empleado(Se autocompleta por la cedula del empleado registrado)

"""

@login_required
def buscar_nomina(request):
    nominas = []
    cedula_buscada = ""

    if hasattr(request.user, 'usuarios') and request.user.usuarios.empleado:
        empleado = request.user.usuarios.empleado
        cedula_buscada = empleado.cedula
        nominas = Nomina.objects.filter(id_empleado=empleado).order_by('-fecha_emision')
    else:
        if request.method == 'POST':
            form = BuscarNominaForm(request.POST)
            if form.is_valid():
                cedula_buscada = form.cleaned_data['cedula']
                empleados = Empleado.objects.filter(cedula__icontains=cedula_buscada)
                nominas = Nomina.objects.filter(id_empleado__in=empleados).order_by('-fecha_emision')
        else:
            form = BuscarNominaForm()
            return render(request, 'buscar_nomina.html', {
                'form': form,
                'nominas': nominas,
                'cedula_buscada': cedula_buscada
            })
            
    return render(request, 'buscar_nomina.html', {
        'nominas': nominas,
        'cedula_buscada': cedula_buscada,
        'form': None 
    })




"""
Exportacion de la nomina a pdf

"""

@login_required
def exportar_nomina_pdf(request, id_nomina):
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
   
    inasistencias = Asistencia.objects.filter(asistio=False).order_by('-fecha_asistencia')
    return render(request, 'inasistencia_list.html', {'inasistencias': inasistencias})

@login_required
def inasistencia_create(request):
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
    hora_actual = timezone.localtime()

   
    if hasattr(request.user, 'usuarios') and request.user.usuarios.empleado:
        empleado_encontrado = request.user.usuarios.empleado
        cedula_buscada = empleado_encontrado.cedula 
        
        asistencia_hoy = Asistenciaconfirmada.objects.filter(
            id_empleado=empleado_encontrado,
            fecha_asistencia=hoy
        ).first()

        if request.method == 'POST':
            if 'registrar_entrada' in request.POST:
                asistencia_obj, created = Asistenciaconfirmada.objects.get_or_create(
                    id_empleado=empleado_encontrado,
                    fecha_asistencia=hoy,
                    defaults={'asistio': True, 'hora_entrada': hora_actual}
                )
                if not created:
                    if not asistencia_obj.hora_entrada:
                        asistencia_obj.hora_entrada = hora_actual
                        asistencia_obj.asistio = True
                        asistencia_obj.save()
                        messages.success(request, f"Entrada registrada para {empleado_encontrado.nombre} {empleado_encontrado.apellido} a las {hora_actual.strftime('%H:%M')}.")
                    else:
                        messages.info(request, f"La entrada para {empleado_encontrado.nombre} {empleado_encontrado.apellido} ya fue registrada hoy a las {asistencia_obj.hora_entrada.strftime('%H:%M')}.")
                else:
                    messages.success(request, f"Entrada registrada para {empleado_encontrado.nombre} {empleado_encontrado.apellido} a las {hora_actual.strftime('%H:%M')}.")
                
                asistencia_hoy = Asistenciaconfirmada.objects.filter(
                    id_empleado=empleado_encontrado,
                    fecha_asistencia=hoy
                ).first()

            elif 'registrar_salida' in request.POST:
                if asistencia_hoy and not asistencia_hoy.hora_salida:
                    asistencia_hoy.hora_salida = hora_actual
                    asistencia_hoy.save()
                    messages.success(request, f"Salida registrada para {empleado_encontrado.nombre} {empleado_encontrado.apellido} a las {hora_actual.strftime('%H:%M')}.")
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
        return redirect('home') 

    context = {
        'empleado_encontrado': empleado_encontrado,
        'asistencia_hoy': asistencia_hoy,
        'cedula_buscada': cedula_buscada, 
        'hora_actual': hora_actual,
    }
    return render(request, 'registrar_asistencia_diaria.html', context)


@login_required
def asistencia_confirmada_list(request):

    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    cedula = request.GET.get('cedula')
    nombre = request.GET.get('nombre')
    
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
    
    hoy = timezone.localdate()
    primer_dia_mes = hoy.replace(day=1)
    
    context = {
        'asistencias_confirmadas': asistencias,
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

            empleados_por_labor = Empleado.objects.filter(id_trabajo=labor_seleccionada)
            
            nominas_generadas = []
            errores_generacion = []

            if not empleados_por_labor.exists():
                messages.warning(request, f"No se encontraron empleados para la labor '{labor_seleccionada.nombre_trabajo}'.")
                return render(request, 'generar_nomina_grupal.html', {'form': form})

            for empleado in empleados_por_labor:
                try:
                    sueldo_empleado = Sueldo.objects.get(id_empleado=empleado)
                    
                    sueldo_semanal_usd = sueldo_empleado.id_jornada.sueldo_semanal_usd
                    valor_tasa = sueldo_empleado.id_tasa.valor_tasa
                    sueldo_semanal_bs = sueldo_semanal_usd * valor_tasa

                    sueldo_bs_base_periodo = Decimal('0.00') 
                    dias_en_periodo = (fecha_fin - fecha_inicio).days + 1

                    sueldo_semanal_bs = Decimal(str(sueldo_semanal_bs)) 
                    
                    if tipo_periodo == 'semanal':
                        sueldo_diario_bs = sueldo_semanal_bs / Decimal('5')
                        sueldo_bs_base_periodo = sueldo_diario_bs * Decimal(str(dias_en_periodo))
                    elif tipo_periodo == 'quincenal':
                        sueldo_quincenal_usd = sueldo_semanal_usd * Decimal('2') 
                        sueldo_quincenal_bs = sueldo_quincenal_usd * valor_tasa
                        sueldo_bs_base_periodo = sueldo_quincenal_bs * (Decimal(str(dias_en_periodo)) / Decimal('15.0')) 
                    elif tipo_periodo == 'mensual':
                        sueldo_mensual_usd = sueldo_semanal_usd * Decimal('4') 
                        sueldo_mensual_bs = sueldo_mensual_usd * valor_tasa
                        sueldo_bs_base_periodo = sueldo_mensual_bs * (Decimal(str(dias_en_periodo)) / Decimal('30.0')) 
                    
                    cestaticket_bs_calculado = Decimal('1300.00') 

                    horas_semanales = empleado.id_jornada.horas_semanales
                    horas_ordinarias_periodo = Decimal('0.00')
                    if tipo_periodo == 'semanal':
                        horas_ordinarias_periodo = Decimal(str(horas_semanales))
                    elif tipo_periodo == 'quincenal':
                        horas_ordinarias_periodo = Decimal(str(horas_semanales)) * Decimal('2')
                    elif tipo_periodo == 'mensual':
                        horas_ordinarias_periodo = Decimal(str(horas_semanales)) * Decimal('4')

                    pago_horas_extras_bs = Decimal('0.00')
                    pago_horas_festivas_bs = Decimal('0.00')

                    pago_prestaciones_calculado = sueldo_bs_base_periodo * Decimal('0.0833') # 8.33% mensual

                    total_asignaciones_bs = (
                        sueldo_bs_base_periodo + 
                        cestaticket_bs_calculado + 
                        pago_horas_extras_bs + 
                        pago_horas_festivas_bs +
                        pago_prestaciones_calculado 
                    )

                    ivss_bs = total_asignaciones_bs * Decimal('0.04')
                    rpe_bs = total_asignaciones_bs * Decimal('0.01')
                    faov_bs = total_asignaciones_bs * Decimal('0.02')
                    total_deducciones_bs = ivss_bs + rpe_bs + faov_bs

                    sueldo_neto_bs = total_asignaciones_bs - total_deducciones_bs

                  
                    print(f"Calculando para {empleado.nombre} {empleado.apellido}:")
                    print(f"  Sueldo Base Periodo: {sueldo_bs_base_periodo}")
                    print(f"  Cestaticket: {cestaticket_bs_calculado}")
                    print(f"  Pago Prestaciones: {pago_prestaciones_calculado}")
                    print(f"  Total Asignaciones: {total_asignaciones_bs}")
                    print(f"  Total Deducciones: {total_deducciones_bs}")
                    print(f"  Sueldo Neto: {sueldo_neto_bs}")

                    nomina = Nomina(
                        id_empleado=empleado,
                        id_sueldo=sueldo_empleado,
                        id_trabajo=labor_seleccionada,
                        periodo_inicio=fecha_inicio,
                        periodo_fin=fecha_fin,
                        tipo_periodo=tipo_periodo,
                        sueldo_bs_base=round(sueldo_bs_base_periodo, 2),
                        cestaticket_bs=round(cestaticket_bs_calculado, 2),
                        pago_prestaciones_bs=round(pago_prestaciones_calculado, 2), 
                        horas_extras=0,
                        horas_ordinarias=round(horas_ordinarias_periodo, 2), 
                        pago_horas_extras_bs=round(pago_horas_extras_bs, 2),
                        horas_festivas=0,
                        pago_horas_festivas_bs=round(pago_horas_festivas_bs, 2),
                        dias_vacaciones=0,
                        dias_enfermedad=0,
                        total_asignaciones_bs=round(total_asignaciones_bs, 2),
                        ivss_bs=round(ivss_bs, 2),
                        rpe_bs=round(rpe_bs, 2),
                        faov_bs=round(faov_bs, 2),
                        total_deducciones_bs=round(total_deducciones_bs, 2),
                        sueldo_neto_bs=round(sueldo_neto_bs, 2),
                    )
                    nomina.save()
                    nominas_generadas.append(nomina)
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

