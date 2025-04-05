document.addEventListener('DOMContentLoaded', function () {
    // ELEMENTOS DEL FORMULARIO
    const empleadoSelect = document.getElementById('id_empleado');
    const sueldoDisplay = document.getElementById('sueldo_bs_base_display');
    const sueldoHidden = document.getElementById('sueldo_bs_base');
    const idSueldoInput = document.getElementById('id_sueldo');
    const horasOrdinariasInput = document.getElementById('horas_ordinarias');
    const valorHoraInput = document.getElementById('valor_hora_ordinaria');
    const diasTrabajadosInput = document.getElementById('dias_trabajados');
    const semanasLaboradasInput = document.getElementById('semanas_laboradas');
    const horasExtrasInput = document.getElementById('horas_extras');
    const horasFestivasInput = document.getElementById('horas_festivas');
    const cestaticketInput = document.getElementById('cestaticket_bs');
    const diasVacacionesInput = document.getElementById('dias_vacaciones');
    const diasEnfermedadInput = document.getElementById('dias_enfermedad');

    // INFORMACION DEL EMPLEADO
    const infoJornada = document.getElementById('info-jornada');
    const infoSueldoBase = document.getElementById('info-sueldo-base');
    const infoHorasSemanales = document.getElementById('info-horas-semanales');
    const infoHorasMensuales = document.getElementById('info-horas-mensuales');
    const infoValorHora = document.getElementById('info-valor-hora');

    // RESULTADOS CALCULADOS
    const sueldoBaseProporcionalDisplay = document.getElementById('sueldo-base-proporcional');
    const pagoHorasExtrasDisplay = document.getElementById('pago-horas-extras');
    const pagoHorasFestivasDisplay = document.getElementById('pago-horas-festivas');
    const cestaticketDisplay = document.getElementById('display-cestaticket');
    const totalAsignacionesDisplay = document.getElementById('total-asignaciones');
    const deduccionIvssDisplay = document.getElementById('deduccion-ivss');
    const deduccionFaovDisplay = document.getElementById('deduccion-faov');
    const deduccionRpeDisplay = document.getElementById('deduccion-rpe');
    const totalDeduccionesDisplay = document.getElementById('total-deducciones');
    const sueldoNetoDisplay = document.getElementById('sueldo-neto');

    // CAMPOS OCULTADOS PARA UN ENVIO POSTERIOR
    const sueldoBaseProporcionalInput = document.getElementById('sueldo_base_proporcional');
    const pagoHorasExtrasInput = document.getElementById('pago_horas_extras_bs');
    const pagoHorasFestivasInput = document.getElementById('pago_horas_festivas_bs');
    const totalAsignacionesInput = document.getElementById('total_asignaciones_bs');
    const ivssInput = document.getElementById('ivss_bs');
    const faovInput = document.getElementById('faov_bs');
    const rpeInput = document.getElementById('rpe_bs');
    const totalDeduccionesInput = document.getElementById('total_deducciones_bs');
    const sueldoNetoInput = document.getElementById('sueldo_neto_bs');


    let sueldoMensual = 0;
    let horasSemanales = 0;
    let jornadaNombre = '';
    let valorHora = 0;
    let cestaticketBase = 0;

    //Cara los datos del empleado seleccionado
    empleadoSelect.addEventListener('change', function () {
        const selectedOption = this.options[this.selectedIndex];

        sueldoMensual = parseFloat(selectedOption.getAttribute('data-sueldo-bs')) || 0;
        horasSemanales = parseFloat(selectedOption.getAttribute('data-horas-semanales')) || 0;
        jornadaNombre = selectedOption.getAttribute('data-jornada-nombre') || '';
        cestaticketBase = parseFloat(selectedOption.getAttribute('data-cestaticket')) || 0;


        const horasMensuales = horasSemanales * 4;


        valorHora = sueldoMensual * 4 / horasMensuales;

        infoJornada.textContent = jornadaNombre;
        infoSueldoBase.textContent = sueldoMensual.toFixed(2) + ' Bs';
        infoHorasSemanales.textContent = horasSemanales;
        infoHorasMensuales.textContent = horasMensuales;
        infoValorHora.textContent = valorHora.toFixed(2) + ' Bs/h';


        sueldoDisplay.value = sueldoMensual.toFixed(2);
        sueldoHidden.value = sueldoMensual.toFixed(2);
        idSueldoInput.value = selectedOption.getAttribute('data-sueldo-id');
        horasOrdinariasInput.value = horasMensuales;
        valorHoraInput.value = valorHora.toFixed(2);


        if (cestaticketBase > 0) {
            cestaticketInput.value = cestaticketBase.toFixed(2);
        }

        calcularNomina();
    });


    [diasTrabajadosInput, semanasLaboradasInput, horasExtrasInput,
        horasFestivasInput, cestaticketInput, diasVacacionesInput,
        diasEnfermedadInput].forEach(input => {
            input.addEventListener('input', calcularNomina);
        });


    function calcularNomina() {
        const diasTrabajados = parseInt(diasTrabajadosInput.value) || 30;
        const semanasLaboradas = parseFloat(semanasLaboradasInput.value) || 4.33;
        const horasExtras = parseInt(horasExtrasInput.value) || 0;
        const horasFestivas = parseInt(horasFestivasInput.value) || 0;
        const cestaticket = parseFloat(cestaticketInput.value) || 0;
        const diasVacaciones = parseInt(diasVacacionesInput.value) || 0;
        const diasEnfermedad = parseInt(diasEnfermedadInput.value) || 0;


        const sueldoBaseProporcional = sueldoMensual * 4;

        const pagoHorasExtras = horasExtras * valorHora * 1.5;


        const pagoHorasFestivas = horasFestivas * valorHora * 1.5;


        const totalAsignaciones = sueldoBaseProporcional + pagoHorasExtras + pagoHorasFestivas + cestaticket;


        const ivss = sueldoBaseProporcional * 0.04;  // 4% IVSS
        const faov = sueldoBaseProporcional * 0.005; // 0.5% FAOV
        const rpe = sueldoBaseProporcional * 0.01;   // 1% RPE
        const totalDeducciones = ivss + faov + rpe;


        const sueldoNeto = totalAsignaciones - totalDeducciones;


        sueldoBaseProporcionalDisplay.textContent = sueldoBaseProporcional.toFixed(2) + ' Bs';
        pagoHorasExtrasDisplay.textContent = pagoHorasExtras.toFixed(2) + ' Bs';
        pagoHorasFestivasDisplay.textContent = pagoHorasFestivas.toFixed(2) + ' Bs';
        cestaticketDisplay.textContent = cestaticket.toFixed(2) + ' Bs';
        totalAsignacionesDisplay.textContent = totalAsignaciones.toFixed(2) + ' Bs';
        deduccionIvssDisplay.textContent = ivss.toFixed(2) + ' Bs';
        deduccionFaovDisplay.textContent = faov.toFixed(2) + ' Bs';
        deduccionRpeDisplay.textContent = rpe.toFixed(2) + ' Bs';
        totalDeduccionesDisplay.textContent = totalDeducciones.toFixed(2) + ' Bs';
        sueldoNetoDisplay.textContent = sueldoNeto.toFixed(2) + ' Bs';

        sueldoBaseProporcionalInput.value = sueldoBaseProporcional.toFixed(2);
        pagoHorasExtrasInput.value = pagoHorasExtras.toFixed(2);
        pagoHorasFestivasInput.value = pagoHorasFestivas.toFixed(2);
        totalAsignacionesInput.value = totalAsignaciones.toFixed(2);
        ivssInput.value = ivss.toFixed(2);
        faovInput.value = faov.toFixed(2);
        rpeInput.value = rpe.toFixed(2);
        totalDeduccionesInput.value = totalDeducciones.toFixed(2);
        sueldoNetoInput.value = sueldoNeto.toFixed(2);
    }

    if (empleadoSelect.value) {
        empleadoSelect.dispatchEvent(new Event('change'));
    }
});