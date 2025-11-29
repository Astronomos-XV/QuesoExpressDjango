
const cerrarSesionBtn = document.querySelector('.cerrar_sesion');
if (cerrarSesionBtn) {
    cerrarSesionBtn.addEventListener('click', (e) => {
        if (!confirm('¿Estás seguro de que deseas cerrar sesión?')) {
            e.preventDefault();
        }
    });
}