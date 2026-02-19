let datos = [];

// 1️⃣ Cargar JSON
fetch("datos.json")
    .then(response => response.json())
    .then(data => {
        datos = data;
        llenarSelector();
        actualizarDashboard("todos");
    });


// 2️⃣ Llenar el selector con profesores únicos
function llenarSelector() {

    const selector = document.getElementById("selectorProfesor");

    const profesoresUnicos = [...new Set(datos.map(d => d.profesor))];

    profesoresUnicos.forEach(prof => {
        const option = document.createElement("option");
        option.value = prof;
        option.textContent = prof;
        selector.appendChild(option);
    });
}


// 3️⃣ Detectar cambio en selector
document.getElementById("selectorProfesor")
    .addEventListener("change", function () {
        actualizarDashboard(this.value);
    });


// 4️⃣ Función principal que recalcula todo
function actualizarDashboard(profesorSeleccionado) {

    let datosFiltrados = datos;

    if (profesorSeleccionado !== "todos") {
        datosFiltrados = datos.filter(d => d.profesor === profesorSeleccionado);
    }

    const total = datosFiltrados.length;
    const puntuales = datosFiltrados.filter(d => d.estado === "PUNTUAL").length;
    const faltas = datosFiltrados.filter(d => d.estado === "FALTA").length;

    const porcentajeAsistencia = total > 0 ? ((puntuales / total) * 100).toFixed(1) : 0;
    const porcentajeFalta = total > 0 ? ((faltas / total) * 100).toFixed(1) : 0;

    // Actualizar tarjetas
    document.getElementById("total").textContent = total;
    document.getElementById("asistencia").textContent = porcentajeAsistencia + "%";
    document.getElementById("falta").textContent = porcentajeFalta + "%";

    actualizarGrafica(puntuales, faltas);
}


// 5️⃣ Crear gráfica
let chart;

function actualizarGrafica(puntuales, faltas) {

    const options = {
        series: [puntuales, faltas],
        chart: {
            type: 'pie'
        },
        labels: ['Puntual', 'Falta'],
        colors: ['#198754', '#dc3545']
    };

    if (chart) {
        chart.updateOptions(options);
    } else {
        chart = new ApexCharts(document.querySelector("#grafica"), options);
        chart.render();
    }
}
