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
    path('nomina/crear/', views.nomina_create, name='crear_nomina'),
    path('nomina/editar/<int:id_nomina>/', views.editar_nomina, name='editar_nomina'),
    path('nomina/eliminar/<int:id_nomina>/', views.eliminar_nomina, name='eliminar_nomina'),
    path('buscar-nomina/', views.buscar_nomina, name='buscar_nomina'),
    path('sueldos/', views.sueldo_list, name='sueldo_lista'),
    path('sueldo/crear/', views.sueldo_create, name='sueldo_creacion'),
    path('sueldos/editar/<int:id_sueldo>/', views.sueldo_editar, name='sueldo_editar'),
    path('sueldos/eliminar/<int:id_sueldo>/', views.sueldo_eliminar, name='sueldo_eliminar'),
    path('gestion-datos/', views.gestion_datos, name='gestion_datos'),
    path('tasas/', views.actualizar_y_listar_tasas, name='tasa'),
]
