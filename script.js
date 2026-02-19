let datosRaw = null; // contenido completo de data.json
let porProfesor = [];
let chart;

// Cargar JSON (nota: el archivo en el repo se llama data.json)
fetch("data.json")
    .then(response => response.json())
    .then(data => {
        datosRaw = data;

        // Soportar dos formatos:
        // 1) Formato antiguo: un array de registros con {profesor, estado}
        // 2) Formato actual en repo: {resumen_general, por_profesor: [{PROFESOR,PUNTUAL,TOLERANCIA,FALTA}, ...]}
        if (Array.isArray(data)) {
            // convertir al formato porProfesor esperado
            porProfesor = aggregateFromRecords(data);
            renderResumenFromAggregates(porProfesor);
        } else if (data.por_profesor) {
            porProfesor = data.por_profesor.map(p => ({
                profesor: p.PROFESOR,
                puntual: Number(p.PUNTUAL) || 0,
                tolerancia: Number(p.TOLERANCIA) || 0,
                falta: Number(p.FALTA) || 0
            }));

            renderResumenFromDataJSON(data, porProfesor);
        } else {
            console.error('Formato de JSON no reconocido');
        }

        llenarSelector();
        actualizarDashboard('todos');
    })
    .catch(err => console.error('Error cargando data.json', err));


function aggregateFromRecords(records) {
    const map = {};
    records.forEach(r => {
        const prof = r.profesor || r.PROFESOR || 'Sin nombre';
        if (!map[prof]) map[prof] = { profesor: prof, puntual: 0, tolerancia: 0, falta: 0 };
        const estado = (r.estado || '').toUpperCase();
        if (estado === 'PUNTUAL' || estado === 'A TIEMPO') map[prof].puntual += 1;
        else if (estado === 'TOLERANCIA') map[prof].tolerancia += 1;
        else if (estado === 'FALTA' || estado === 'NO ASISTIÓ') map[prof].falta += 1;
        else map[prof].falta += 0;
    });
    return Object.values(map);
}


// Llenar selector con los profesores
function llenarSelector() {
    const selector = document.getElementById('selectorProfesor');
    // limpiar opciones excepto 'todos'
    selector.innerHTML = '<option value="todos">Todos</option>';
    porProfesor.forEach(p => {
        const option = document.createElement('option');
        option.value = p.profesor;
        option.textContent = p.profesor;
        selector.appendChild(option);
    });

    selector.addEventListener('change', function () {
        actualizarDashboard(this.value);
    });
}


function renderResumenFromDataJSON(data, profData) {
    // resumen_general contiene totales y porcentajes
    const resumen = data.resumen_general || {};
    document.getElementById('total').textContent = resumen.total || profData.reduce((s, x) => s + x.puntual + x.tolerancia + x.falta, 0);
    document.getElementById('asistencia').textContent = (resumen.asistencia !== undefined ? resumen.asistencia : 0) + '%';
    document.getElementById('falta').textContent = (resumen.falta !== undefined ? resumen.falta : 0) + '%';
}


function renderResumenFromAggregates(profData) {
    const total = profData.reduce((s, x) => s + x.puntual + x.tolerancia + x.falta, 0);
    const totalPuntual = profData.reduce((s, x) => s + x.puntual, 0);
    const totalFalta = profData.reduce((s, x) => s + x.falta, 0);
    const porcentajeAsistencia = total > 0 ? ((totalPuntual / total) * 100).toFixed(1) : 0;
    const porcentajeFalta = total > 0 ? ((totalFalta / total) * 100).toFixed(1) : 0;
    document.getElementById('total').textContent = total;
    document.getElementById('asistencia').textContent = porcentajeAsistencia + '%';
    document.getElementById('falta').textContent = porcentajeFalta + '%';
}


// Actualizar dashboard según profesor seleccionado
function actualizarDashboard(profesorSeleccionado) {
    let lista = porProfesor;
    if (profesorSeleccionado !== 'todos') lista = porProfesor.filter(p => p.profesor === profesorSeleccionado);

    // Para la gráfica usamos suma de puntuales vs faltas
    const puntuales = lista.reduce((s, x) => s + (x.puntual || 0), 0);
    const faltas = lista.reduce((s, x) => s + (x.falta || 0), 0);

    actualizarGrafica(puntuales, faltas);

    // Llenar tabla por profesor
    const tbody = document.querySelector('#tablaProfesores tbody');
    tbody.innerHTML = '';
    porProfesor.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${p.profesor}</td><td>${p.puntual}</td><td>${p.tolerancia}</td><td>${p.falta}</td>`;
        tbody.appendChild(tr);
    });
}


function actualizarGrafica(puntuales, faltas) {
    const options = {
        series: [puntuales, faltas],
        chart: { type: 'pie' },
        labels: ['Puntual', 'Falta'],
        colors: ['#198754', '#dc3545']
    };

    if (chart) chart.updateOptions(options);
    else {
        chart = new ApexCharts(document.querySelector('#grafica'), options);
        chart.render();
    }
}
