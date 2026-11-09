"""
Servidor Backend HTTP para el Sistema de Asistencia y Escáner QR - GEF Bermejo y Multi-Grupos.
Gestiona la lectura y escritura en tiempo real de los archivos Excel (.xlsx) y CSV por Grupos,
administración de asistentes (crear, modificar, eliminar), cambio de estado de asistencia y reseteo de pruebas.
"""

import os
import sys
import json
import socket
import re
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRUPOS_JSON_PATH = os.path.join(BASE_DIR, "grupos.json")

# Configuración por defecto si no existe grupos.json
CONFIG_GRUPOS = {
    "grupos": [
        {
            "id": "gef_bermejo",
            "nombre": "Taller de Incepción GEF Bermejo",
            "archivo_excel": "asistencia_gef_bermejo.xlsx",
            "archivo_csv": "asistencia_gef_bermejo.csv",
            "archivo_json": "asistencia_inicial.json"
        }
    ],
    "grupo_activo": "gef_bermejo"
}

ASISTENTES_CACHE = []

def normalizar_id(texto):
    s = re.sub(r'[^\w\s-]', '', texto.lower())
    return re.sub(r'[-\s]+', '_', s).strip('_')

def cargar_config_grupos():
    global CONFIG_GRUPOS
    if os.path.exists(GRUPOS_JSON_PATH):
        try:
            with open(GRUPOS_JSON_PATH, "r", encoding="utf-8") as f:
                CONFIG_GRUPOS = json.load(f)
        except Exception as e:
            print(f"Aviso al cargar grupos.json: {e}")
    else:
        guardar_config_grupos()

def guardar_config_grupos():
    try:
        with open(GRUPOS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(CONFIG_GRUPOS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error al guardar grupos.json: {e}")

def obtener_grupo_actual():
    activo_id = CONFIG_GRUPOS.get("grupo_activo", "gef_bermejo")
    for g in CONFIG_GRUPOS.get("grupos", []):
        if g["id"] == activo_id:
            return g
    if CONFIG_GRUPOS.get("grupos"):
        return CONFIG_GRUPOS["grupos"][0]
    return {
        "id": "gef_bermejo",
        "nombre": "Taller de Incepción GEF Bermejo",
        "archivo_excel": "asistencia_gef_bermejo.xlsx",
        "archivo_csv": "asistencia_gef_bermejo.csv",
        "archivo_json": "asistencia_inicial.json"
    }

def obtener_rutas_grupo(g=None):
    if g is None:
        g = obtener_grupo_actual()
    return (
        os.path.join(BASE_DIR, g.get("archivo_excel", f"asistencia_{g['id']}.xlsx")),
        os.path.join(BASE_DIR, g.get("archivo_csv", f"asistencia_{g['id']}.csv")),
        os.path.join(BASE_DIR, g.get("archivo_json", f"asistencia_{g['id']}.json"))
    )

def generar_excel_formateado(xlsx_path, asistentes, titulo):
    """Crea una hoja Excel profesional con encabezados, estilos y formato condicional."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Control de Asistencia"

    # Fuentes y estilos
    font_titulo = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    fill_titulo = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # Slate 800

    font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    fill_header = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid") # Slate 900

    thin_border_side = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

    fill_presente = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid") # Verde suave
    fill_ausente = PatternFill(fill_type=None)
    font_presente = Font(name="Calibri", size=9, bold=True, color="166534") # Verde oscuro
    font_ausente = Font(name="Calibri", size=9, color="64748B") # Gris
    font_datos = Font(name="Calibri", size=9)

    columnas = [
        "Nº", "NOMBRE", "INSTITUCIÓN", "ESTADO GENERAL",
        "DIA 1", "DIA 1 FECHA Y HORA", "DIA 1 OBSERVACIÓN",
        "DIA 2", "DIA 2 FECHA Y HORA", "DIA 2 OBSERVACIÓN",
        "DIA 3", "DIA 3 FECHA Y HORA", "DIA 3 OBSERVACIÓN"
    ]

    # Fila 1: Título
    ws.merge_cells("A1:M1")
    c1 = ws["A1"]
    c1.value = f"REGISTRO DE ASISTENCIA Y QR - {titulo.upper()}"
    c1.font = font_titulo
    c1.fill = fill_titulo
    c1.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32

    # Fila 2: Encabezados
    for col_num, col_name in enumerate(columnas, 1):
        cell = ws.cell(row=2, column=col_num, value=col_name)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = cell_border
    ws.row_dimensions[2].height = 24

    # Filas de datos
    for idx, a in enumerate(asistentes, 3):
        ws.row_dimensions[idx].height = 20
        row_vals = [
            a.get("numero", idx - 2),
            a.get("nombre", ""),
            a.get("institucion", ""),
            a.get("estado_general", "Pendiente"),
            a.get("dia_1", "Ausente"),
            a.get("dia_1_fecha_hora", ""),
            a.get("dia_1_observacion", ""),
            a.get("dia_2", "Ausente"),
            a.get("dia_2_fecha_hora", ""),
            a.get("dia_2_observacion", ""),
            a.get("dia_3", "Ausente"),
            a.get("dia_3_fecha_hora", ""),
            a.get("dia_3_observacion", "")
        ]

        for c_idx, val in enumerate(row_vals, 1):
            cell = ws.cell(row=idx, column=c_idx, value=val)
            cell.font = font_datos
            cell.border = cell_border

            # Centrar números y estados
            if c_idx in (1, 4, 5, 8, 11):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

            # Colorear estado general y días
            if c_idx in (4, 5, 8, 11):
                if str(val).upper() == "PRESENTE":
                    cell.fill = fill_presente
                    cell.font = font_presente
                else:
                    cell.fill = fill_ausente
                    cell.font = font_ausente

    # Anchos de columna automáticos
    anchos_sugeridos = {1: 6, 2: 32, 3: 40, 4: 15, 5: 12, 6: 20, 7: 25, 8: 12, 9: 20, 10: 25, 11: 12, 12: 20, 13: 25}
    for col_num, ancho in anchos_sugeridos.items():
        ws.column_dimensions[get_column_letter(col_num)].width = ancho

    wb.save(xlsx_path)

def guardar_asistentes_en_archivos():
    """Actualiza de forma completa tanto el archivo Excel (.xlsx) como el CSV y JSON del grupo activo."""
    global ASISTENTES_CACHE
    g = obtener_grupo_actual()
    xlsx_p, csv_p, json_p = obtener_rutas_grupo(g)

    # 1. Guardar JSON
    try:
        with open(json_p, "w", encoding="utf-8") as f:
            json.dump(ASISTENTES_CACHE, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando JSON: {e}")

    # 2. Guardar CSV
    fieldnames = [
        "Nº", "NOMBRE", "INSTITUCIÓN", "ESTADO GENERAL",
        "DIA 1", "DIA 1 FECHA Y HORA", "DIA 1 OBSERVACIÓN",
        "DIA 2", "DIA 2 FECHA Y HORA", "DIA 2 OBSERVACIÓN",
        "DIA 3", "DIA 3 FECHA Y HORA", "DIA 3 OBSERVACIÓN"
    ]
    try:
        with open(csv_p, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([f"REGISTRO DE ASISTENCIA Y QR - {g['nombre'].upper()}"] + [""] * (len(fieldnames) - 1))
            writer.writerow(fieldnames)
            for item in ASISTENTES_CACHE:
                writer.writerow([
                    item.get("numero", ""),
                    item.get("nombre", ""),
                    item.get("institucion", ""),
                    item.get("estado_general", "Pendiente"),
                    item.get("dia_1", "Ausente"),
                    item.get("dia_1_fecha_hora", ""),
                    item.get("dia_1_observacion", ""),
                    item.get("dia_2", "Ausente"),
                    item.get("dia_2_fecha_hora", ""),
                    item.get("dia_2_observacion", ""),
                    item.get("dia_3", "Ausente"),
                    item.get("dia_3_fecha_hora", ""),
                    item.get("dia_3_observacion", "")
                ])
    except Exception as e:
        print(f"Error guardando CSV: {e}")

    # 3. Guardar XLSX
    try:
        generar_excel_formateado(xlsx_p, ASISTENTES_CACHE, g["nombre"])
    except Exception as e:
        print(f"Error guardando XLSX: {e}")

def cargar_asistentes(grupo_id=None):
    global ASISTENTES_CACHE
    cargar_config_grupos()
    if grupo_id:
        CONFIG_GRUPOS["grupo_activo"] = grupo_id
        guardar_config_grupos()

    g = obtener_grupo_actual()
    xlsx_p, csv_p, json_p = obtener_rutas_grupo(g)

    # Intentar cargar desde JSON primero (más rápido y limpio)
    if os.path.exists(json_p):
        try:
            with open(json_p, "r", encoding="utf-8") as f:
                ASISTENTES_CACHE = json.load(f)
                print(f"Cargados {len(ASISTENTES_CACHE)} asistentes para el grupo '{g['nombre']}' desde JSON.")
                return
        except Exception as e:
            print(f"Aviso leyendo JSON: {e}")

    # Fallback a Excel
    if os.path.exists(xlsx_p):
        try:
            wb = openpyxl.load_workbook(xlsx_p, data_only=True)
            ws = wb.active
            rows_data = []
            for r in range(3, ws.max_row + 1):
                num_val = ws.cell(row=r, column=1).value
                if num_val is None:
                    continue
                try:
                    num = int(num_val)
                except ValueError:
                    continue
                rows_data.append({
                    "numero": num,
                    "nombre": str(ws.cell(row=r, column=2).value or "").strip(),
                    "institucion": str(ws.cell(row=r, column=3).value or "").strip(),
                    "estado_general": str(ws.cell(row=r, column=4).value or "Pendiente").strip(),
                    "dia_1": str(ws.cell(row=r, column=5).value or "Ausente").strip(),
                    "dia_1_fecha_hora": str(ws.cell(row=r, column=6).value or "").strip(),
                    "dia_1_observacion": str(ws.cell(row=r, column=7).value or "").strip(),
                    "dia_2": str(ws.cell(row=r, column=8).value or "Ausente").strip(),
                    "dia_2_fecha_hora": str(ws.cell(row=r, column=9).value or "").strip(),
                    "dia_2_observacion": str(ws.cell(row=r, column=10).value or "").strip(),
                    "dia_3": str(ws.cell(row=r, column=11).value or "Ausente").strip(),
                    "dia_3_fecha_hora": str(ws.cell(row=r, column=12).value or "").strip(),
                    "dia_3_observacion": str(ws.cell(row=r, column=13).value or "").strip()
                })
            ASISTENTES_CACHE = rows_data
            print(f"Cargados {len(ASISTENTES_CACHE)} asistentes para '{g['nombre']}' desde Excel.")
            return
        except Exception as e:
            print(f"Aviso leyendo Excel: {e}")

    ASISTENTES_CACHE = []

class AsistenciaRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def responder_json(self, codigo, data):
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/asistentes":
            params = urllib.parse.parse_qs(parsed.query)
            grupo_id = params.get("grupo", [None])[0]
            if grupo_id and grupo_id != CONFIG_GRUPOS.get("grupo_activo"):
                cargar_asistentes(grupo_id)
            self.responder_json(200, ASISTENTES_CACHE)
            return

        elif path == "/api/grupos":
            cargar_config_grupos()
            self.responder_json(200, {
                "grupos": CONFIG_GRUPOS.get("grupos", []),
                "activo": CONFIG_GRUPOS.get("grupo_activo", "gef_bermejo")
            })
            return

        elif path == "/api/descargar-excel":
            g = obtener_grupo_actual()
            xlsx_p, _, _ = obtener_rutas_grupo(g)
            if os.path.exists(xlsx_p):
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(xlsx_p)}"')
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(xlsx_p, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "Archivo Excel no encontrado")
                return

        elif path == "/api/descargar-csv":
            g = obtener_grupo_actual()
            _, csv_p, _ = obtener_rutas_grupo(g)
            if os.path.exists(csv_p):
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(csv_p)}"')
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(csv_p, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "Archivo CSV no encontrado")
                return

        elif path == "/" or path == "":
            self.path = "/index.html"

        return super().do_GET()

    def do_POST(self):
        global ASISTENTES_CACHE
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = {}
        if body:
            try:
                data = json.loads(body.decode("utf-8"))
            except Exception as e:
                self.responder_json(400, {"error": f"JSON inválido: {e}"})
                return

        # 1. REGISTRAR O CAMBIAR ASISTENCIA (PRESENTE / AUSENTE)
        if path == "/api/registrar":
            num = data.get("numero")
            dia = int(data.get("dia", 1))
            estado = data.get("estado", "PRESENTE") # "PRESENTE" o "Ausente"
            fecha_hora = data.get("fecha_hora", "")
            observacion = data.get("observacion", "").strip()

            target_item = None
            for item in ASISTENTES_CACHE:
                if item["numero"] == int(num):
                    target_item = item
                    break

            if not target_item:
                self.responder_json(404, {"error": f"Participante con Nº {num} no encontrado"})
                return

            dia_key = f"dia_{dia}"
            dia_fh_key = f"dia_{dia}_fecha_hora"
            dia_obs_key = f"dia_{dia}_observacion"

            target_item[dia_key] = estado
            target_item[dia_fh_key] = fecha_hora if estado == "PRESENTE" else ""
            target_item[dia_obs_key] = observacion if estado == "PRESENTE" else ""

            # Recalcular estado general
            if target_item.get("dia_1") == "PRESENTE" or target_item.get("dia_2") == "PRESENTE" or target_item.get("dia_3") == "PRESENTE":
                target_item["estado_general"] = "PRESENTE"
            else:
                target_item["estado_general"] = "Pendiente"

            guardar_asistentes_en_archivos()

            self.responder_json(200, {
                "success": True,
                "mensaje": f"Asistencia del Día {dia} actualizada a '{estado}' para Nº {num}",
                "asistente": target_item
            })
            return

        # 2. CREAR NUEVO GRUPO (MASIVO EXCEL/CSV)
        elif path == "/api/grupos/crear":
            nombre = data.get("nombre", "").strip()
            asistentes_nuevos = data.get("asistentes", [])
            if not nombre:
                self.responder_json(400, {"error": "El nombre del grupo es obligatorio"})
                return

            grupo_id = normalizar_id(nombre) or f"grupo_{len(CONFIG_GRUPOS['grupos']) + 1}"
            # Asegurar id único
            base_id = grupo_id
            contador = 1
            ids_existentes = [g["id"] for g in CONFIG_GRUPOS.get("grupos", [])]
            while grupo_id in ids_existentes:
                grupo_id = f"{base_id}_{contador}"
                contador += 1

            archivo_excel = f"asistencia_{grupo_id}.xlsx"
            archivo_csv = f"asistencia_{grupo_id}.csv"
            archivo_json = f"asistencia_{grupo_id}.json"

            nuevo_grupo = {
                "id": grupo_id,
                "nombre": nombre,
                "archivo_excel": archivo_excel,
                "archivo_csv": archivo_csv,
                "archivo_json": archivo_json
            }

            CONFIG_GRUPOS["grupos"].append(nuevo_grupo)
            CONFIG_GRUPOS["grupo_activo"] = grupo_id
            guardar_config_grupos()

            # Formatear lista de asistentes
            rows = []
            for idx, a in enumerate(asistentes_nuevos, 1):
                rows.append({
                    "numero": a.get("numero", idx),
                    "nombre": str(a.get("nombre", "")).strip(),
                    "institucion": str(a.get("institucion", "")).strip(),
                    "estado_general": a.get("estado_general", "Pendiente"),
                    "dia_1": a.get("dia_1", "Ausente"),
                    "dia_1_fecha_hora": a.get("dia_1_fecha_hora", ""),
                    "dia_1_observacion": a.get("dia_1_observacion", ""),
                    "dia_2": a.get("dia_2", "Ausente"),
                    "dia_2_fecha_hora": a.get("dia_2_fecha_hora", ""),
                    "dia_2_observacion": a.get("dia_2_observacion", ""),
                    "dia_3": a.get("dia_3", "Ausente"),
                    "dia_3_fecha_hora": a.get("dia_3_fecha_hora", ""),
                    "dia_3_observacion": a.get("dia_3_observacion", "")
                })

            ASISTENTES_CACHE = rows
            guardar_asistentes_en_archivos()

            self.responder_json(200, {
                "success": True,
                "mensaje": f"Grupo '{nombre}' creado con éxito con {len(rows)} asistentes",
                "grupo": nuevo_grupo,
                "asistentes": ASISTENTES_CACHE
            })
            return

        # 3. SELECCIONAR GRUPO ACTIVO
        elif path == "/api/grupos/seleccionar":
            gid = data.get("id")
            if not gid:
                self.responder_json(400, {"error": "ID de grupo no especificado"})
                return

            cargar_asistentes(gid)
            self.responder_json(200, {
                "success": True,
                "grupo_activo": gid,
                "asistentes": ASISTENTES_CACHE
            })
            return

        # 4. ELIMINAR GRUPO
        elif path == "/api/grupos/eliminar":
            gid = data.get("id")
            if not gid:
                self.responder_json(400, {"error": "ID de grupo no especificado"})
                return

            grupo_a_borrar = next((g for g in CONFIG_GRUPOS["grupos"] if g["id"] == gid), None)
            if not grupo_a_borrar:
                self.responder_json(404, {"error": "Grupo no encontrado"})
                return

            # Eliminar archivos asociados del grupo (proteger plantilla inicial)
            for key in ["archivo_excel", "archivo_csv", "archivo_json"]:
                fn = grupo_a_borrar.get(key)
                if fn and fn != "asistencia_inicial.json":
                    fp = os.path.join(BASE_DIR, fn)
                    if os.path.exists(fp):
                        try:
                            os.remove(fp)
                        except Exception as e:
                            print(f"Aviso al borrar {fp}: {e}")

            # Eliminar posibles carpetas de QRs generados para este grupo
            for d in [f"qr_out_{gid}", f"qrs_{gid}", f"test_qr_out_{gid}"]:
                dp = os.path.join(BASE_DIR, d)
                if os.path.exists(dp) and os.path.isdir(dp):
                    import shutil
                    try:
                        shutil.rmtree(dp)
                    except Exception as e:
                        print(f"Aviso al borrar carpeta {dp}: {e}")

            CONFIG_GRUPOS["grupos"] = [g for g in CONFIG_GRUPOS["grupos"] if g["id"] != gid]

            if not CONFIG_GRUPOS["grupos"]:
                # Si se eliminó el único grupo, crear uno limpio en blanco
                nuevo_default = {
                    "id": "nuevo_grupo",
                    "nombre": "Grupo Principal (En blanco)",
                    "archivo_excel": "asistencia_nuevo_grupo.xlsx",
                    "archivo_csv": "asistencia_nuevo_grupo.csv",
                    "archivo_json": "asistencia_nuevo_grupo.json"
                }
                CONFIG_GRUPOS["grupos"] = [nuevo_default]
                CONFIG_GRUPOS["grupo_activo"] = "nuevo_grupo"
                generar_excel_formateado(os.path.join(BASE_DIR, nuevo_default["archivo_excel"]), [], nuevo_default["nombre"])
                with open(os.path.join(BASE_DIR, nuevo_default["archivo_json"]), "w", encoding="utf-8") as f:
                    json.dump([], f)
                with open(os.path.join(BASE_DIR, nuevo_default["archivo_csv"]), "w", encoding="utf-8") as f:
                    f.write("")
            elif CONFIG_GRUPOS.get("grupo_activo") == gid:
                CONFIG_GRUPOS["grupo_activo"] = CONFIG_GRUPOS["grupos"][0]["id"]

            guardar_config_grupos()
            cargar_asistentes(CONFIG_GRUPOS["grupo_activo"])

            self.responder_json(200, {
                "success": True,
                "mensaje": f"Grupo '{grupo_a_borrar['nombre']}' eliminado correctamente",
                "grupos": CONFIG_GRUPOS["grupos"],
                "activo": CONFIG_GRUPOS["grupo_activo"],
                "asistentes": ASISTENTES_CACHE
            })
            return

        # 5. CREAR O MODIFICAR ASISTENTE
        elif path == "/api/asistente/guardar":
            num = data.get("numero")
            nombre = str(data.get("nombre", "")).strip()
            institucion = str(data.get("institucion", "")).strip()

            if not nombre:
                self.responder_json(400, {"error": "El nombre es obligatorio"})
                return

            item_existente = None
            if num is not None:
                for item in ASISTENTES_CACHE:
                    if item["numero"] == int(num):
                        item_existente = item
                        break

            if item_existente:
                # Modificar existente
                item_existente["nombre"] = nombre
                item_existente["institucion"] = institucion
                if "dia_1" in data: item_existente["dia_1"] = data["dia_1"]
                if "dia_2" in data: item_existente["dia_2"] = data["dia_2"]
                if "dia_3" in data: item_existente["dia_3"] = data["dia_3"]
                # Recalcular general
                if item_existente.get("dia_1") == "PRESENTE" or item_existente.get("dia_2") == "PRESENTE" or item_existente.get("dia_3") == "PRESENTE":
                    item_existente["estado_general"] = "PRESENTE"
                else:
                    item_existente["estado_general"] = "Pendiente"
            else:
                # Crear nuevo participante
                max_num = max([a.get("numero", 0) for a in ASISTENTES_CACHE], default=0)
                nuevo_num = int(num) if num is not None else max_num + 1
                item_existente = {
                    "numero": nuevo_num,
                    "nombre": nombre,
                    "institucion": institucion,
                    "estado_general": "Pendiente",
                    "dia_1": "Ausente", "dia_1_fecha_hora": "", "dia_1_observacion": "",
                    "dia_2": "Ausente", "dia_2_fecha_hora": "", "dia_2_observacion": "",
                    "dia_3": "Ausente", "dia_3_fecha_hora": "", "dia_3_observacion": ""
                }
                ASISTENTES_CACHE.append(item_existente)
                # Ordenar por número
                ASISTENTES_CACHE.sort(key=lambda x: x.get("numero", 0))

            guardar_asistentes_en_archivos()
            self.responder_json(200, {
                "success": True,
                "mensaje": "Participante guardado exitosamente",
                "asistente": item_existente,
                "asistentes": ASISTENTES_CACHE
            })
            return

        # 6. ELIMINAR ASISTENTE
        elif path == "/api/asistente/eliminar":
            num = data.get("numero")
            if num is None:
                self.responder_json(400, {"error": "Número no especificado"})
                return

            inicial = len(ASISTENTES_CACHE)
            ASISTENTES_CACHE = [a for a in ASISTENTES_CACHE if a["numero"] != int(num)]
            if len(ASISTENTES_CACHE) == inicial:
                self.responder_json(404, {"error": f"Participante Nº {num} no encontrado"})
                return

            guardar_asistentes_en_archivos()
            self.responder_json(200, {
                "success": True,
                "mensaje": f"Participante Nº {num} eliminado correctamente",
                "asistentes": ASISTENTES_CACHE
            })
            return

        # 7. LIMPIAR ASISTENCIAS DE PRUEBAS
        elif path == "/api/asistencia/limpiar-pruebas":
            dia_objetivo = data.get("dia", "todos") # 1, 2, 3 o "todos"

            for a in ASISTENTES_CACHE:
                if dia_objetivo in (1, "1", "todos"):
                    a["dia_1"] = "Ausente"
                    a["dia_1_fecha_hora"] = ""
                    a["dia_1_observacion"] = ""
                if dia_objetivo in (2, "2", "todos"):
                    a["dia_2"] = "Ausente"
                    a["dia_2_fecha_hora"] = ""
                    a["dia_2_observacion"] = ""
                if dia_objetivo in (3, "3", "todos"):
                    a["dia_3"] = "Ausente"
                    a["dia_3_fecha_hora"] = ""
                    a["dia_3_observacion"] = ""

                # Recalcular general
                if a.get("dia_1") == "PRESENTE" or a.get("dia_2") == "PRESENTE" or a.get("dia_3") == "PRESENTE":
                    a["estado_general"] = "PRESENTE"
                else:
                    a["estado_general"] = "Pendiente"

            guardar_asistentes_en_archivos()
            self.responder_json(200, {
                "success": True,
                "mensaje": f"Asistencias de pruebas restablecidas a 'Ausente' exitosamente",
                "asistentes": ASISTENTES_CACHE
            })
            return

        return super().do_POST()

def obtener_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def iniciar_servidor(puerto=8000):
    cargar_grupos_init = cargar_config_grupos()
    cargar_asistentes()
    server_address = ("0.0.0.0", puerto)
    httpd = HTTPServer(server_address, AsistenciaRequestHandler)
    local_ip = obtener_ip_local()
    g = obtener_grupo_actual()

    print("=" * 65)
    print(" 🚀 SISTEMA DE ASISTENCIA Y ESCÁNER QR - MULTI-GRUPOS")
    print(f" 📂 Grupo Activo: '{g['nombre']}' ({len(ASISTENTES_CACHE)} asistentes)")
    print("=" * 65)
    print(f" ✅ Servidor activo en:")
    print(f"    - Desde tu PC:       http://localhost:{puerto}")
    print(f"    - Desde tu Celular:  http://{local_ip}:{puerto}")
    print("=" * 65)
    print(" Presiona Ctrl + C para detener el servidor.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        httpd.server_close()

if __name__ == "__main__":
    puerto = 8000
    if len(sys.argv) > 1:
        try:
            puerto = int(sys.argv[1])
        except ValueError:
            pass
    iniciar_servidor(puerto)
