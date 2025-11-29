from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.cerrar_sesion, name='cerrar_sesion'),
    path('registrar/', views.crear_superuser, name='crear_superuser'),
    path('', views.home, name='home'),
    path('empleado/', views.vista_empleado, name='vista_empleado'),
    path('empleados/', views.listar_empleados, name='listar_empleados'),
    path('empleados/crear/', views.crear_empleado, name='crear_empleado'),
    path('empleados/editar/<int:empleado_id>/', views.editar_empleado, name='editar_empleado'),
    path('empleados/eliminar/<int:empleado_id>/', views.eliminar_empleado, name='eliminar_empleado'),
    #path('nomina/crear/', views.nomina_create, name='crear_nomina'),
    path('nomina/editar/<int:id_nomina>/', views.editar_nomina, name='editar_nomina'),
    path('conceptos/crear/', views.crear_concepto_nomina, name='crear_concepto_nomina'),
    path('nomina/eliminar/<int:id_nomina>/', views.eliminar_nomina, name='eliminar_nomina'),
    path('buscar-nomina/', views.buscar_nomina, name='buscar_nomina'),
    path('sueldos/', views.sueldo_list, name='sueldo_lista'),
    path('sueldo/crear/', views.sueldo_create, name='sueldo_creacion'),
    path('sueldos/editar/<int:id_sueldo>/', views.sueldo_editar, name='sueldo_editar'),
    path('sueldos/eliminar/<int:id_sueldo>/', views.sueldo_eliminar, name='sueldo_eliminar'),
    path('sueldos/labor/gestion/', views.sueldo_labor_list_create, name='sueldo_labor_list_create'),
    path('sueldos/labor/editar/<int:pk>/', views.sueldo_labor_edit, name='sueldo_labor_edit'),
    path('gestion-datos/', views.gestion_datos, name='gestion_datos'),
    path('tasas/', views.actualizar_y_listar_tasas, name='tasa'),
    path('nomina/concepto/<int:pk>/', views.ver_concepto_nomina, name='ver_concepto_nomina'),
    path('configuracion/parametros/', views.editar_parametros_nomina, name='editar_parametros_nomina'),
    #path('asistencias/', views.AsistenciaListView.as_view(), name='lista_asistencias'),
   # path('asistencias/toggle/<int:pk>/', views.toggle_asistencia, name='toggle_asistencia'),
    #path('asistencias/registrar/', views.registrar_asistencias, name='registrar_asistencias'),
    
    path('prestamos/crear/', views.crear_prestamo, name='crear_prestamo'),
    path('prestamos/', views.listar_prestamos, name='listar_prestamos'),
    path('prestamos/editar/<int:pk>/', views.editar_prestamo, name='editar_prestamo'),
    path('prestamos/eliminar/<int:pk>/', views.eliminar_prestamo, name='eliminar_prestamo'),
    path('prestamos/eliminar-todos/', views.eliminar_todos_los_prestamos, name='eliminar_todos_los_prestamos'),
    path('nomina/grupal/', views.generar_nomina_grupal, name='generar_nomina_grupal'),
    path('nominas/eliminar-todas/', views.eliminar_todas_nominas, name='eliminar_todas_nominas'),
    path('inasistencias/', views.inasistencia_list, name='inasistencia_list'),
    path('inasistencias/crear/', views.inasistencia_create, name='inasistencia_create'),
    path('inasistencias/editar/<int:id_asistencia>/', views.inasistencia_edit, name='inasistencia_edit'),
    path('inasistencias/eliminar/<int:id_asistencia>/', views.inasistencia_delete, name='inasistencia_delete'),
    path('nomina/pdf/<int:id_nomina>/', views.exportar_nomina_pdf, name='exportar_nomina_pdf'),
    path('registrar_asistencia_diaria/', views.registrar_asistencia_diaria, name='registrar_asistencia_diaria'),
    path('asistencias/confirmadas/', views.asistencia_confirmada_list, name='asistencia_confirmada_list'),
    path('inasistencias/histograma/', views.inasistencias_histograma, name='inasistencias_histograma'),
    path('inasistencias/histograma/imagen/', views.inasistencias_histograma_imagen, name='inasistencias_histograma_imagen'),
    path('sueldos/grupal/', views.generar_sueldo_grupal, name='generar_sueldo_grupal'),
  
    path('crear_liquidacion_individual/', views.crear_liquidacion_individual, name='crear_liquidacion_individual'),
    path('crear_liquidacion_grupal/', views.crear_liquidacion_grupal, name='crear_liquidacion_grupal'),
    path('lista_liquidaciones/', views.lista_liquidaciones, name='lista_liquidaciones'),
    path('liquidacion_pdf/<int:pk>/', views.ver_liquidacion_pdf, name='ver_liquidacion_pdf'),
    path('eliminar_todas_liquidaciones/', views.eliminar_todas_liquidaciones, name='eliminar_todas_liquidaciones'),
     path('trigger-create-absences/', views.trigger_create_missing_attendances, name='trigger_create_missing_attendances'),

 # 🌟 NUEVA: Ruta para Listar/Gestionar todos los conceptos
    path('conceptos/gestion/', views.gestionar_conceptos_nomina, name='gestionar_conceptos_nomina'),
    
    # Existente: Ruta para Crear un nuevo concepto
    path('conceptos/crear/', views.crear_concepto_nomina, name='crear_concepto_nomina'), 
    
    # 🌟 NUEVA: Ruta para Editar un concepto específico (se pasa el ID: pk)
    path('conceptos/editar/<int:pk>/', views.editar_concepto_nomina, name='editar_concepto_nomina'),
    
    # 🌟 NUEVA: Ruta para Eliminar un concepto específico (se pasa el ID: pk)
    path('conceptos/eliminar/<int:pk>/', views.eliminar_concepto_nomina, name='eliminar_concepto_nomina'),

]
