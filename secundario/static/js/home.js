const titulo = document.querySelector('h1');
const textoOriginal = titulo.textContent;
titulo.textContent = '';

let i = 0;
function escribir() {
    if (i < textoOriginal.length) {
        titulo.textContent += textoOriginal.charAt(i);
        i++;
        setTimeout(escribir, 100);
    }
}

window.addEventListener('load', escribir);


