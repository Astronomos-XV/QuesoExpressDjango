# Recordatorio

- en settings.py cambiar el nombre, contra y nombre de la base de datos
- python manage.py migrate es necesario ejecutarlo

# Se encuentra en la carpeta principal en settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nombrebasededats',
        'USER': 'usuario',
        'PASSWORD': 'contraseña',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
