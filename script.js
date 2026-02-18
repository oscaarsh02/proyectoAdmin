fetch("data.json")
    .then(response => response.json())
    .then(data => {

        // ===== CARDS =====
        document.getElementById("total").innerText = data.resumen_general.total;
        document.getElementById("asistencia").innerText = data.resumen_general.asistencia + "%";
        document.getElementById("retardo").innerText = data.resumen_general.retardo + "%";
        document.getElementById("falta").innerText = data.resumen_general.falta + "%";

        // ===== GRAFICA =====
        var options = {
            chart: { type: 'donut' },
            series: [
                data.resumen_general.asistencia,
                data.resumen_general.retardo,
                data.resumen_general.falta
            ],
            labels: ['Asistencia', 'Retardo', 'Falta'],
            colors: ['#198754', '#ffc107', '#dc3545']
        };

        var chart = new ApexCharts(document.querySelector("#grafica"), options);
        chart.render();

        // ===== TABLA =====
        const tbody = document.querySelector("#tablaProfesores tbody");

        data.por_profesor.forEach(prof => {

            const row = `
                <tr>
                    <td>${prof.PROFESOR}</td>
                    <td>${prof.PUNTUAL || 0}</td>
                    <td>${prof.TOLERANCIA || 0}</td>
                    <td>${prof.RETARDO || 0}</td>
                    <td>${prof.FALTA || 0}</td>
                </tr>
            `;

            tbody.innerHTML += row;
        });

    });
