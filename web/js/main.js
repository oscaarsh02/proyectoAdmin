// Cargar datos del JSON
async function loadData() {
    try {
        const response = await fetch('../../output/data.json');
        const data = await response.json();
        displayStats(data);
        displayProfessors(data);
    } catch (error) {
        console.error('Error cargando datos:', error);
    }
}

function displayStats(data) {
    const statsDiv = document.getElementById('stats-general');
    const general = data.resumen_general;
    
    statsDiv.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Registros</h3>
                <p>${general.total}</p>
            </div>
            <div class="stat-card">
                <h3>Asistencia %</h3>
                <p>${general.asistencia}%</p>
            </div>
            <div class="stat-card">
                <h3>Retardo %</h3>
                <p>${general.retardo}%</p>
            </div>
            <div class="stat-card">
                <h3>Faltas %</h3>
                <p>${general.falta}%</p>
            </div>
        </div>
    `;
}

function displayProfessors(data) {
    const profesorsDiv = document.getElementById('professors-list');
    const professors = data.por_profesor;
    
    let html = '<table><thead><tr><th>Profesor</th><th>General</th><th>Quincena 1</th><th>Quincena 2</th></tr></thead><tbody>';
    
    professors.forEach(prof => {
        html += `
            <tr>
                <td>${prof.PROFESOR}</td>
                <td>P: ${prof.general.PUNTUAL} | T: ${prof.general.TOLERANCIA} | R: ${prof.general.RETARDO} | F: ${prof.general.FALTA}</td>
                <td>P: ${prof.quincena_1.PUNTUAL} | T: ${prof.quincena_1.TOLERANCIA} | R: ${prof.quincena_1.RETARDO} | F: ${prof.quincena_1.FALTA}</td>
                <td>P: ${prof.quincena_2.PUNTUAL} | T: ${prof.quincena_2.TOLERANCIA} | R: ${prof.quincena_2.RETARDO} | F: ${prof.quincena_2.FALTA}</td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    profesorsDiv.innerHTML = html;
}

// Cargar datos al abrir la página
document.addEventListener('DOMContentLoaded', loadData);
