document.addEventListener('DOMContentLoaded', function () {
    const empleadoSelect = document.getElementById('id_empleado');
    const jornadaSelect = document.getElementById('id_jornada');
    const tasaSelect = document.getElementById('id_tasa');
    const infoEmpleado = document.getElementById('info-empleado');
    const resultadoCalculo = document.getElementById('resultado-calculo');
    const sueldoBsInput = document.getElementById('sueldo_bs');

    function calcularSueldo() {
        const jornadaOption = jornadaSelect.options[jornadaSelect.selectedIndex];
        const tasaOption = tasaSelect.options[tasaSelect.selectedIndex];

        if (jornadaOption.value && tasaOption.value) {
            const sueldoUsd = parseFloat(jornadaOption.getAttribute('data-sueldo-usd'));
            const tasa = parseFloat(tasaOption.getAttribute('data-valor-tasa'));
            const sueldoBs = sueldoUsd * tasa;

            resultadoCalculo.innerHTML = `${sueldoUsd} USD × ${tasa} Bs/USD = <strong>${sueldoBs.toFixed(2)} Bs</strong>`;
            sueldoBsInput.value = sueldoBs.toFixed(2);
        }
    }


    empleadoSelect.addEventListener('change', function () {
        const selectedOption = this.options[this.selectedIndex];
        const jornadaId = selectedOption.getAttribute('data-jornada');
        const sueldoActual = selectedOption.getAttribute('data-sueldo-actual');
        const jornadaNombre = selectedOption.getAttribute('data-jornada-nombre');
        const jornadaSueldo = selectedOption.getAttribute('data-jornada-sueldo');

        if (jornadaId) {
            infoEmpleado.innerHTML = `
                <p><strong>Jornada actual:</strong> ${jornadaNombre} (${jornadaSueldo} USD/semana)</p>
                <p><strong>Horas Semanales:</strong> ${sueldoActual} </p>
            `;


            for (let i = 0; i < jornadaSelect.options.length; i++) {
                if (jornadaSelect.options[i].value === jornadaId) {
                    jornadaSelect.selectedIndex = i;
                    break;
                }
            }

            calcularSueldo();
        } else {
            infoEmpleado.innerHTML = `<p>No se encontró información de jornada para este empleado</p>`;
        }
    });


    jornadaSelect.addEventListener('change', calcularSueldo);
    tasaSelect.addEventListener('change', calcularSueldo);
});