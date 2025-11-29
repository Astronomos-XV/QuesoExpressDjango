from django.contrib import admin
from .models import ParametrosNomina,SueldoLabor,TipoDeJornada, Labor, SueldoLabor, CambioLabor,BonoExtra, DetalleConceptoNomina, ConceptoNomina, CodigoActivacionSuperuser
from django.contrib import admin
from .models import TipoDeJornada, Labor, SueldoLabor 
from .forms import FormularioCodigoActivacion

@admin.register(ParametrosNomina)
class ParametrosNominaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'periodicidad', 'monto_fijo', 'monto_fijo_usd', 'porcentaje', 'es_concepto_fijo', 'fecha_ultima_actualizacion')
    
    list_filter = ('tipo', 'periodicidad', 'es_concepto_fijo')
    
    search_fields = ('nombre', 'tipo')
    
    readonly_fields = ('fecha_ultima_actualizacion',)
    
    fieldsets = (
        ("Definición de la Regla", {
            'fields': ('nombre', 'tipo', 'periodicidad', 'es_concepto_fijo', ),
        }),
        ("Valores de Cálculo (Solo ingrese en Monto Fijo O Porcentaje)", {
            'fields': ('monto_fijo', 'porcentaje'),
            'description': "Si una regla usa el monto fijo, el porcentaje será ignorado, y viceversa."
        }),
                ("Cálculo en USD → Automático a Bs (Recomendado para Cestaticket 2025+)", {
            'fields': ('monto_fijo_usd',),

        }),
        ("Auditoría", {
            'fields': ('fecha_ultima_actualizacion',),
        }),
    )

@admin.register(DetalleConceptoNomina)
class DetalleConceptoNominaAdmin(admin.ModelAdmin):
    list_display = ('id_nomina', 'nombre_concepto', 'tipo_concepto', 'monto_calculado_bs')
    
    readonly_fields = ('id_nomina', 'id_regla', 'nombre_concepto', 'tipo_concepto', 'monto_calculado_bs')
    
    list_filter = ('tipo_concepto',)
    search_fields = ('nombre_concepto', 'id_nomina__id_empleado__nombre') 
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(SueldoLabor)
class SueldoLaborAdmin(admin.ModelAdmin):
    list_display = ('id_labor', 'sueldo_base_semanal_usd', 'fecha_establecimiento')
    search_fields = ('id_labor__nombre_trabajo', )
    list_filter = ('fecha_establecimiento', )
    
    

@admin.register(TipoDeJornada)
class TipoDeJornadaAdmin(admin.ModelAdmin):
    list_display = ('nombre_jornada', 'horas_diarias', 'horas_semanales')
    fields = ('nombre_jornada', 'horas_diarias') 
    search_fields = ('nombre_jornada',)



@admin.register(CambioLabor)
class CambioLaborAdmin(admin.ModelAdmin):
    list_display = ('id_empleado', 'labor_anterior', 'labor_nueva', 'fecha_cambio', 'motivo')
    
    list_filter = ('fecha_cambio', 'labor_anterior', 'labor_nueva')
    
    search_fields = ('id_empleado__nombre', 'id_empleado__apellido', 'motivo')
    
    readonly_fields = ('id_empleado', 'labor_anterior', 'labor_nueva', 'fecha_cambio', 'motivo')
    
    def has_add_permission(self, request):
        return False


@admin.register(BonoExtra)
class BonoExtraAdmin(admin.ModelAdmin):
    list_display = ('id_empleado', 'concepto', 'monto_bs', 'fecha_aplicacion', 'pagado_en_nomina')
    
    list_filter = ('pagado_en_nomina', 'fecha_aplicacion', 'concepto')
    
    search_fields = ('id_empleado__nombre', 'id_empleado__apellido', 'concepto')
    
    fields = ('id_empleado', 'concepto', 'monto_bs', 'fecha_aplicacion', 'pagado_en_nomina')
    
    readonly_fields = ('fecha_registro',)



@admin.register(CodigoActivacionSuperuser)
class CodigoActivacionAdmin(admin.ModelAdmin):
    form = FormularioCodigoActivacion
    list_display = ('activado', 'fecha_actualizacion')
    readonly_fields = ('fecha_actualizacion',)

    fieldsets = (
        ("Configurar Código de Activación", {
            'fields': ('codigo_nuevo', 'confirmar'),
            'description': "<strong>Una vez guardado, este código permite crear superusuarios desde el formulario público.</strong>"
        }),
        ("Estado", {
            'fields': ('activado', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return not CodigoActivacionSuperuser.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False