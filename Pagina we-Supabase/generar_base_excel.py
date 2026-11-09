import csv
import json
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_csv = os.path.join(base_dir, "datos_asistentes.csv")
    xlsx_path = os.path.join(base_dir, "asistencia_gef_bermejo.xlsx")
    csv_path = os.path.join(base_dir, "asistencia_gef_bermejo.csv")
    json_path = os.path.join(base_dir, "asistencia_inicial.json")

    rows = []
    with open(source_csv, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for r in reader:
            if not r or not r[0]:
                continue
            try:
                num = int(r[0].strip())
            except ValueError:
                continue
            nombre = r[1].strip() if len(r) > 1 else ""
            institucion = r[2].strip() if len(r) > 2 else ""
            institucion = institucion.replace("\n", " ").replace("\r", " ")
            rows.append({
                "numero": num,
                "nombre": nombre,
                "institucion": institucion,
                "estado_general": "Pendiente",
                "dia_1": "Ausente",
                "dia_1_fecha_hora": "",
                "dia_1_observacion": "",
                "dia_2": "Ausente",
                "dia_2_fecha_hora": "",
                "dia_2_observacion": "",
                "dia_3": "Ausente",
                "dia_3_fecha_hora": "",
                "dia_3_observacion": ""
            })

    print(f"Total registros leídos: {len(rows)}")

    # 1. Guardar JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"JSON guardado: {json_path}")

    # 2. Guardar CSV
    fieldnames = [
        "Nº", "NOMBRE", "INSTITUCIÓN", "ESTADO GENERAL",
        "DIA 1", "DIA 1 FECHA Y HORA", "DIA 1 OBSERVACIÓN",
        "DIA 2", "DIA 2 FECHA Y HORA", "DIA 2 OBSERVACIÓN",
        "DIA 3", "DIA 3 FECHA Y HORA", "DIA 3 OBSERVACIÓN"
    ]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["REGISTRO DE ASISTENCIA Y QR - TALLER GEF BERMEJO"] + [""] * (len(fieldnames) - 1))
        writer.writerow(fieldnames)
        for item in rows:
            writer.writerow([
                item["numero"],
                item["nombre"],
                item["institucion"],
                item["estado_general"],
                item["dia_1"],
                item["dia_1_fecha_hora"],
                item["dia_1_observacion"],
                item["dia_2"],
                item["dia_2_fecha_hora"],
                item["dia_2_observacion"],
                item["dia_3"],
                item["dia_3_fecha_hora"],
                item["dia_3_observacion"]
            ])
    print(f"CSV guardado: {csv_path}")

    # 3. Guardar Excel (.xlsx) con formato profesional
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Control de Asistencia"

    # Titulo
    ws.merge_cells("A1:M1")
    title_cell = ws["A1"]
    title_cell.value = "LISTA DE ASISTENCIA Y CONTROL QR - TALLER DE INCEPCIÓN PROYECTO GEF BERMEJO"
    title_cell.font = Font(name="Calibri", size=13, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Dark Blue
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    # Encabezados
    headers = [
        "Nº", "NOMBRE COMPLETO", "INSTITUCIÓN / CARGO", "ESTADO GENERAL",
        "DÍA 1", "DÍA 1 HORA Y FECHA", "DÍA 1 OBSERVACIÓN",
        "DÍA 2", "DÍA 2 HORA Y FECHA", "DÍA 2 OBSERVACIÓN",
        "DÍA 3", "DÍA 3 HORA Y FECHA", "DÍA 3 OBSERVACIÓN"
    ]
    ws.append(headers)
    ws.row_dimensions[2].height = 28

    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid") # Royal Blue
    dia1_fill = PatternFill(start_color="0D9488", end_color="0D9488", fill_type="solid") # Teal
    dia2_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid") # Indigo
    dia3_fill = PatternFill(start_color="9333EA", end_color="9333EA", fill_type="solid") # Purple

    thin_border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )

    for col_idx, col_name in enumerate(headers, start=1):
        cell = ws.cell(row=2, column=col_idx)
        cell.font = header_font
        if col_idx in [5, 6, 7]:
            cell.fill = dia1_fill
        elif col_idx in [8, 9, 10]:
            cell.fill = dia2_fill
        elif col_idx in [11, 12, 13]:
            cell.fill = dia3_fill
        else:
            cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Insertar filas
    for r_idx, item in enumerate(rows, start=3):
        row_vals = [
            item["numero"],
            item["nombre"],
            item["institucion"],
            item["estado_general"],
            item["dia_1"],
            item["dia_1_fecha_hora"],
            item["dia_1_observacion"],
            item["dia_2"],
            item["dia_2_fecha_hora"],
            item["dia_2_observacion"],
            item["dia_3"],
            item["dia_3_fecha_hora"],
            item["dia_3_observacion"]
        ]
        ws.append(row_vals)
        ws.row_dimensions[r_idx].height = 20

        for c_idx in range(1, len(row_vals) + 1):
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.border = thin_border
            cell.font = Font(name="Calibri", size=9)
            if c_idx == 1:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif c_idx in [4, 5, 8, 11]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # Anchos de columna
    col_widths = {
        1: 6,   # Nº
        2: 36,  # NOMBRE
        3: 50,  # INSTITUCION
        4: 16,  # ESTADO GENERAL
        5: 14,  # DIA 1
        6: 22,  # DIA 1 FECHA
        7: 28,  # DIA 1 OBS
        8: 14,  # DIA 2
        9: 22,  # DIA 2 FECHA
        10: 28, # DIA 2 OBS
        11: 14, # DIA 3
        12: 22, # DIA 3 FECHA
        13: 28  # DIA 3 OBS
    }
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    wb.save(xlsx_path)
    print(f"Excel guardado con éxito: {xlsx_path}")

if __name__ == "__main__":
    main()
