import pandas as pd
import datetime as dt
import unicodedata
from datetime import datetime
import time; t=time.perf_counter()
import json
import os


# ==================================================
# CONFIG
# ==================================================

# Obtener directorio actual del script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Rutas de entrada (en la misma carpeta que el script)
ARCHIVO_HORARIO = os.path.join(SCRIPT_DIR, "Horario_oficial.xlsx")
ARCHIVO_REGISTRO = os.path.join(SCRIPT_DIR, "REGISTRO ASISTENCIA ENE-26.xlsx")

TOLERANCIA_MINUTOS = 10
VENTANA_ANTES = 15
VENTANA_DESPUES = 10

# Rutas de salida
OUTPUT_DIR = os.path.join(SCRIPT_DIR, '..', 'output')
REPORTE_PATH = os.path.join(OUTPUT_DIR, 'reporte_asistencia.xlsx')
DATA_JSON_PATH = os.path.join(OUTPUT_DIR, 'data.json')

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


def obtener_quincena(fecha):
    """Determina si una fecha pertenece a la quincena 1 (1-15) o quincena 2 (16-fin de mes)"""
    dia = fecha.day
    if dia <= 15:
        return "Quincena 1"
    else:
        return "Quincena 2"

# ==================================================
# CARGAR ARCHIVOS
# ==================================================

print(f"📁 Directorio del script: {SCRIPT_DIR}")
print(f"📄 Leyendo: {ARCHIVO_HORARIO}")
print(f"📄 Leyendo: {ARCHIVO_REGISTRO}")
print(f"💾 Guardando en: {OUTPUT_DIR}")
print()

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

reporte_final.to_excel(REPORTE_PATH, index=False)

print("\n✅ REPORTE DEFINITIVO GENERADO CORRECTAMENTE")
print(reporte_final['ESTATUS'].value_counts())

# ==================================================
# EXPORTAR DATA.JSON PARA FRONTEND
# ==================================================
# Agregar columna de quincena
reporte_final['QUINCENA'] = reporte_final['FECHA'].apply(obtener_quincena)

# Agregar conteos por profesor (general y quincena 1-15)
def contar_por_profesor_con_quincenas(df):
    """Contabiliza estatus por profesor incluyendo general y quincenas"""
    rows = []
    # Filtrar NaN en PROFESOR
    df_valido = df[df['PROFESOR'].notna()]
    
    for profesor in df_valido['PROFESOR'].unique():
        df_prof = df_valido[df_valido['PROFESOR'] == profesor]
        
        # General (todo el mes)
        gp_general = df_prof['ESTATUS'].value_counts()
        general_data = {
            'PUNTUAL': int(gp_general.get('PUNTUAL', 0)),
            'TOLERANCIA': int(gp_general.get('TOLERANCIA', 0)),
            'RETARDO': int(gp_general.get('RETARDO', 0)),
            'FALTA': int(gp_general.get('FALTA', 0)),
            'TOTAL': len(df_prof)
        }
        
        # Quincena 1
        df_q1 = df_prof[df_prof['QUINCENA'] == 'Quincena 1']
        gp_q1 = df_q1['ESTATUS'].value_counts()
        quincena_1_data = {
            'PUNTUAL': int(gp_q1.get('PUNTUAL', 0)),
            'TOLERANCIA': int(gp_q1.get('TOLERANCIA', 0)),
            'RETARDO': int(gp_q1.get('RETARDO', 0)),
            'FALTA': int(gp_q1.get('FALTA', 0)),
            'TOTAL': len(df_q1)
        }
        
        # Quincena 2
        df_q2 = df_prof[df_prof['QUINCENA'] == 'Quincena 2']
        gp_q2 = df_q2['ESTATUS'].value_counts()
        quincena_2_data = {
            'PUNTUAL': int(gp_q2.get('PUNTUAL', 0)),
            'TOLERANCIA': int(gp_q2.get('TOLERANCIA', 0)),
            'RETARDO': int(gp_q2.get('RETARDO', 0)),
            'FALTA': int(gp_q2.get('FALTA', 0)),
            'TOTAL': len(df_q2)
        }
        
        rows.append({
            'PROFESOR': profesor,
            'general': general_data,
            'quincena_1': quincena_1_data,
            'quincena_2': quincena_2_data
        })
    return rows


def contar_por_profesor_quincena(df, quincena_num):
    """Contabiliza estatus por profesor para una quincena específica"""
    quincena_label = f"Quincena {quincena_num}"
    df_quincena = df[df['QUINCENA'] == quincena_label]
    # Filtrar NaN en PROFESOR
    df_quincena = df_quincena[df_quincena['PROFESOR'].notna()]
    
    rows = []
    for profesor in df_quincena['PROFESOR'].unique():
        df_prof = df_quincena[df_quincena['PROFESOR'] == profesor]
        gp = df_prof['ESTATUS'].value_counts()
        rows.append({
            'PROFESOR': profesor,
            'PUNTUAL': int(gp.get('PUNTUAL', 0)),
            'TOLERANCIA': int(gp.get('TOLERANCIA', 0)),
            'RETARDO': int(gp.get('RETARDO', 0)),
            'FALTA': int(gp.get('FALTA', 0)),
            'TOTAL': len(df_prof)
        })
    return rows


# General
por_profesor = contar_por_profesor_con_quincenas(reporte_final)
quincena_1 = contar_por_profesor_quincena(reporte_final, 1)
quincena_2 = contar_por_profesor_quincena(reporte_final, 2)

total_registros = int(reporte_final.shape[0])
total_asistencias = int((reporte_final['ESTATUS'].isin(['PUNTUAL', 'TOLERANCIA'])).sum())
total_retardos = int((reporte_final['ESTATUS'] == 'RETARDO').sum())
total_faltas = int((reporte_final['ESTATUS'] == 'FALTA').sum())

resumen_general = {
    'total': total_registros,
    'asistencia': round(100 * total_asistencias / total_registros, 2) if total_registros else 0,
    'retardo': round(100 * total_retardos / total_registros, 2) if total_registros else 0,
    'falta': round(100 * total_faltas / total_registros, 2) if total_registros else 0
}



# Escribir archivo JSON
out = {
    'resumen_general': resumen_general,
    'por_profesor': por_profesor,
    'quincena_1': quincena_1,
    'quincena_2': quincena_2,
}

with open(DATA_JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print('\n✅ data.json generado')
