import pandas as pd
import json

ARCHIVO = "reporte_asistencia.xlsx"

df = pd.read_excel(ARCHIVO)

total = len(df)

puntual = len(df[df['ESTATUS'] == 'PUNTUAL'])
tolerancia = len(df[df['ESTATUS'] == 'TOLERANCIA'])
retardo = len(df[df['ESTATUS'] == 'RETARDO'])
falta = len(df[df['ESTATUS'] == 'FALTA'])

asistencia = puntual + tolerancia

porcentaje_asistencia = round((asistencia / total) * 100, 2) if total else 0
porcentaje_retardo = round((retardo / total) * 100, 2) if total else 0
porcentaje_falta = round((falta / total) * 100, 2) if total else 0

por_profesor = df.groupby("PROFESOR")["ESTATUS"].value_counts().unstack(fill_value=0)
por_profesor = por_profesor.reset_index()

data = {
    "resumen_general": {
        "total": total,
        "asistencia": porcentaje_asistencia,
        "retardo": porcentaje_retardo,
        "falta": porcentaje_falta
    },
    "por_profesor": por_profesor.to_dict(orient="records")
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print("✅ data.json generado correctamente")
