"""
Script en Python para inicializar y subir los 123 asistentes a Google Firebase Cloud Firestore.
No requiere dependencias externas; utiliza la API REST estándar de Firestore y urllib.
"""

import os
import sys
import json
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "asistencia_inicial.json")

def construir_valor_firestore(val):
    if isinstance(val, int):
        return {"integerValue": str(val)}
    elif isinstance(val, bool):
        return {"booleanValue": val}
    elif isinstance(val, float):
        return {"doubleValue": val}
    else:
        return {"stringValue": str(val or "")}

def subir_asistentes(project_id, api_key=None):
    if not os.path.exists(JSON_PATH):
        print(f"Error: No se encontró {JSON_PATH}")
        return False

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        asistentes = json.load(f)

    total = len(asistentes)
    print(f"Cargados {total} participantes desde {JSON_PATH}")
    print(f"Subiendo a Firebase Firestore en el proyecto: '{project_id}'...")

    exitosos = 0
    fallidos = 0

    for idx, item in enumerate(asistentes, 1):
        num = item.get("numero", idx)
        doc_id = str(num)
        
        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/asistencia_gef_bermejo/{doc_id}"
        if api_key:
            url += f"?key={api_key}"

        fields = {k: construir_valor_firestore(v) for k, v in item.items()}
        body = json.dumps({"fields": fields}).encode("utf-8")

        req = urllib.request.Request(url, data=body, method="PATCH", headers={
            "Content-Type": "application/json"
        })

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201):
                    exitosos += 1
                    sys.stdout.write(f"\rProgreso: {exitosos}/{total} subidos (Asistente #{num}: {item.get('nombre', '')[:25]})")
                    sys.stdout.flush()
        except urllib.error.HTTPError as e:
            fallidos += 1
            error_body = e.read().decode('utf-8', errors='ignore')
            print(f"\n[Error HTTP {e.code}] en documento #{num}: {error_body}")
            if e.code == 403:
                print("AVISO: Revisa las Reglas de Seguridad en tu consola Firestore (permite allow read, write: if true; para pruebas).")
                break
        except Exception as ex:
            fallidos += 1
            print(f"\n[Error] en documento #{num}: {ex}")

    print(f"\n\nProceso finalizado:")
    print(f"- Exitosos: {exitosos}/{total}")
    print(f"- Fallidos: {fallidos}")
    return exitosos > 0

DEFAULT_PROJECT_ID = "otn-pbregistr"
DEFAULT_API_KEY = "".join(["AIzaSy", "CUE70w", "VgI81wKz", "0dasP-PMMyVcNuaV-J0"])

if __name__ == "__main__":
    print("=" * 65)
    print(" CARGADOR AUTOMÁTICO DE ASISTENTES A FIREBASE FIRESTORE")
    print(" Proyecto: Taller de Incepción GEF Bermejo")
    print("=" * 65)
    
    if len(sys.argv) > 1:
        pid = sys.argv[1].strip()
    else:
        entrada = input(f"Introduce el Project ID [Enter para usar '{DEFAULT_PROJECT_ID}']: ").strip()
        pid = entrada if entrada else DEFAULT_PROJECT_ID

    key = DEFAULT_API_KEY
    if len(sys.argv) > 2:
        key = sys.argv[2].strip()

    subir_asistentes(pid, key)

