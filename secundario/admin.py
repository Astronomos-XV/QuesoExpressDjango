from django.contrib import admin
from .models import Usuarios  

@admin.register(Usuarios)  
class UsuarioAdmin(admin.ModelAdmin):  
    list_display = ('user', 'puesto')
