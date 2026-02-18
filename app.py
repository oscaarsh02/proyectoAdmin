import pandas as pd
import datetime as dt
import unicodedata
from datetime import datetime
import time; t=time.perf_counter()


# ==================================================
# CONFIG
# ==================================================

ARCHIVO_HORARIO = "Horario_oficial.xlsx"
ARCHIVO_REGISTRO = "REGISTRO ASISTENCIA ENE-26.xlsx"

TOLERANCIA_MINUTOS = 10
VENTANA_ANTES = 15
VENTANA_DESPUES = 10

# ==================================================
# FUNCIONES
# ==================================================

def limpiar_id(v):
    if pd.isna(v):
        return None

    s = str(v).strip().replace("'", "")
    s = ''.join(c for c in s if c.isdigit())

    # Tomar últimos 6 dígitos (corrige problema real de IDs)
    if len(s) > 6:
        s = s[-6:]

    return s


def limpiar_texto(texto):
    texto = str(texto).upper()
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ASCII', 'ignore').decode('utf-8')
    texto = texto.replace("-", " ")
    texto = " ".join(texto.split())
    return texto


def clave_horario(nombre):
    nombre = limpiar_texto(nombre)
    partes = nombre.split()
    if len(partes) >= 2:
        return partes[0] + " " + partes[1]
    return nombre


def clave_registro(nombre):
    nombre = limpiar_texto(nombre)
    partes = nombre.split()
    if len(partes) >= 2:
        return partes[-2] + " " + partes[-1]
    return nombre


def parse_hora_horario(v):
    if pd.isna(v):
        return None

    s = str(v)

    if "-" in s:
        s = s.split("-")[0]

    digits = ''.join(c for c in s if c.isdigit())

    if len(digits) == 3:
        digits = "0" + digits

    if len(digits) == 4:
        try:
            return dt.datetime.strptime(digits, "%H%M").time()
        except:
            return None

    return None


def parse_hora_registro(v):
    if pd.isna(v):
        return None

    if isinstance(v, dt.time):
        return v

    if isinstance(v, dt.datetime):
        return v.time()

    try:
        return dt.datetime.strptime(str(v), "%H:%M:%S").time()
    except:
        try:
            return dt.datetime.strptime(str(v), "%H:%M").time()
        except:
            return None


def convertir_dias(dias):
    if pd.isna(dias):
        return []

    dias = str(dias).upper()
    mapa = {"L":0, "A":1, "M":2, "J":3, "V":4, "S":5, "D":6}

    return [mapa[d] for d in dias if d in mapa]

# ==================================================
# CARGAR ARCHIVOS
# ==================================================

horarios = pd.read_excel(ARCHIVO_HORARIO)
registro = pd.read_excel(ARCHIVO_REGISTRO)

# ==================================================
# LIMPIAR HORARIO
# ==================================================

horarios['ID_DOCENTE'] = horarios['ID_DOCENTE'].apply(limpiar_id)
horarios['HORA_ENTRADA'] = horarios['HORA'].apply(parse_hora_horario)
horarios['DIAS_NUM'] = horarios['DIA'].apply(convertir_dias)
horarios['CLAVE'] = horarios['PROFESOR'].apply(clave_horario)

horarios = horarios.dropna(subset=['HORA_ENTRADA'])

# ==================================================
# LIMPIAR REGISTRO
# ==================================================

registro['ID_DOCENTE'] = registro['ID_DOCENTE'].apply(limpiar_id)
registro['FECHA'] = pd.to_datetime(registro['FECHA'], errors='coerce')
registro['HORA_REGISTRO'] = registro['HORA'].apply(parse_hora_registro)
registro['CLAVE'] = registro['PROFESOR'].apply(clave_registro)

registro = registro.dropna(subset=['FECHA'])

# ==================================================
# MAPEAR IDS POR CLAVE
# ==================================================

mapa_ids = horarios.drop_duplicates('CLAVE').set_index('CLAVE')['ID_DOCENTE'].to_dict()

registro['ID_DOCENTE'] = registro.apply(
    lambda row: mapa_ids.get(row['CLAVE'], row['ID_DOCENTE']),
    axis=1
)

# ==================================================
# GENERAR REPORTE
# ==================================================

resultados = []

fecha_min = registro['FECHA'].min().date()
fecha_max = registro['FECHA'].max().date()
rango_fechas = pd.date_range(start=fecha_min, end=fecha_max)

for _, fila_horario in horarios.iterrows():

    id_docente = fila_horario['ID_DOCENTE']
    profesor = fila_horario['PROFESOR']
    dias_validos = fila_horario['DIAS_NUM']
    hora_oficial = fila_horario['HORA_ENTRADA']

    for fecha in rango_fechas:

        if fecha.weekday() not in dias_validos:
            continue

        registros_dia = registro[
            (registro['ID_DOCENTE'] == id_docente) &
            (registro['FECHA'].dt.date == fecha.date())
        ].copy()

        if registros_dia.empty:
            resultados.append({
                "ID_DOCENTE": id_docente,
                "PROFESOR": profesor,
                "FECHA": fecha.date(),
                "HORA_OFICIAL": hora_oficial,
                "HORA_REGISTRO": None,
                "DIF_MINUTOS": None,
                "ESTATUS": "FALTA"
            })
            continue

        mejor_registro = None
        mejor_diferencia = None
        indice_mejor = None

        for idx, fila_reg in registros_dia.iterrows():

            hora_reg = fila_reg['HORA_REGISTRO']

            dt_oficial = datetime.combine(fecha, hora_oficial)
            dt_reg = datetime.combine(fecha, hora_reg)

            diff_min = (dt_reg - dt_oficial).total_seconds() / 60

            if -VENTANA_ANTES <= diff_min <= VENTANA_DESPUES:

                if mejor_diferencia is None or abs(diff_min) < abs(mejor_diferencia):
                    mejor_diferencia = diff_min
                    mejor_registro = hora_reg
                    indice_mejor = idx

        if mejor_registro is not None:

            if mejor_diferencia <= 0:
                estatus = "PUNTUAL"
            elif 0 < mejor_diferencia <= TOLERANCIA_MINUTOS:
                estatus = "TOLERANCIA"
            else:
                estatus = "RETARDO"

            resultados.append({
                "ID_DOCENTE": id_docente,
                "PROFESOR": profesor,
                "FECHA": fecha.date(),
                "HORA_OFICIAL": hora_oficial,
                "HORA_REGISTRO": mejor_registro,
                "DIF_MINUTOS": round(mejor_diferencia, 2),
                "ESTATUS": estatus
            })
            registro = registro.drop(indice_mejor)

        else:
            resultados.append({
                "ID_DOCENTE": id_docente,
                "PROFESOR": profesor,
                "FECHA": fecha.date(),
                "HORA_OFICIAL": hora_oficial,
                "HORA_REGISTRO": None,
                "DIF_MINUTOS": None,
                "ESTATUS": "FALTA"
            })

# ==================================================
# EXPORTAR
# ==================================================
print(f"Tiempo total: {time.perf_counter() - t} segundos")
reporte_final = pd.DataFrame(resultados)
reporte_final = reporte_final.sort_values(
    by=['PROFESOR', 'FECHA', 'HORA_OFICIAL']
)

reporte_final.to_excel("reporte_asistencia.xlsx", index=False)

print("\n✅ REPORTE DEFINITIVO GENERADO CORRECTAMENTE")
print(reporte_final['ESTATUS'].value_counts())

# ==================================================
# GENERAR ESTADISTICAS
# ==================================================

reporte_final['FECHA'] = pd.to_datetime(reporte_final['FECHA'])

# Crear columnas de periodo
reporte_final['SEMANA'] = reporte_final['FECHA'].dt.isocalendar().week
reporte_final['MES'] = reporte_final['FECHA'].dt.month

# Definir quincena
def obtener_quincena(fecha):
    return 1 if fecha.day <= 15 else 2

reporte_final['QUINCENA'] = reporte_final['FECHA'].apply(obtener_quincena)

# Clasificar asistencia general
reporte_final['ASISTENCIA'] = reporte_final['ESTATUS'].apply(
    lambda x: 'ASISTENCIA' if x in ['PUNTUAL','TOLERANCIA'] else x
)

# Estadisticas por profesor
estadisticas = reporte_final.groupby(['PROFESOR']).agg(
    TOTAL_REGISTROS=('ESTATUS','count'),
    ASISTENCIAS=('ASISTENCIA', lambda x: (x=='ASISTENCIA').sum()),
    RETARDOS=('ESTATUS', lambda x: (x=='RETARDO').sum()),
    FALTAS=('ESTATUS', lambda x: (x=='FALTA').sum())
).reset_index()

# Calcular porcentajes
estadisticas['%ASISTENCIA'] = (estadisticas['ASISTENCIAS'] / estadisticas['TOTAL_REGISTROS'] * 100).round(2)
estadisticas['%RETARDO'] = (estadisticas['RETARDOS'] / estadisticas['TOTAL_REGISTROS'] * 100).round(2)
estadisticas['%FALTA'] = (estadisticas['FALTAS'] / estadisticas['TOTAL_REGISTROS'] * 100).round(2)

estadisticas.to_excel("estadisticas_profesores.xlsx", index=False)

print("\n📊 ESTADISTICAS GENERADAS")
