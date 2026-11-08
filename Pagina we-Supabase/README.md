# Sistema de Asistencia y Escáner QR - Proyecto GEF Bermejo

Sistema web completo para el registro y control de asistencia con lectura de Códigos QR, sincronizado automáticamente con hojas de cálculo en **Excel (.xlsx)**, **CSV** y base de datos en la nube **Google Firebase (Cloud Firestore)** o **Supabase**.

Pre-cargado con los **123 participantes confirmados** del **Taller de Incepción Proyecto GEF Bermejo**.

---

## 📁 Archivos en esta Carpeta

- **`iniciar_asistencia.bat`**: Archivo para iniciar el sistema con un solo doble clic. Abre tu navegador y corre el servidor.
- **`servidor.py`**: Servidor web local en Python (utiliza librerías estándar y `openpyxl`). Guarda en tiempo real los registros en el archivo Excel y CSV.
- **`subir_a_firebase.py`**: Script para subir masivamente los 123 asistentes a Google Cloud Firestore.
- **`firestore.rules`**: Reglas de seguridad listas para copiar y pegar en Firestore.
- **`FIREBASE_CONFIG.md`**: Guía paso a paso para configurar tu base de datos en Firebase.
- **`index.html`**: Aplicación web interactiva y moderna con:
  - Escáner de cámara en vivo (soporta celular y PC).
  - Reconocimiento automático de códigos QR generados por el programa.
  - Modal de confirmación al escanear (**"Al Aceptar"**): registra Hora, Fecha, Día (1, 2 o 3) y Observación.
  - Tabla interactiva con búsqueda en vivo, filtros y descarga de Excel con un clic.
- **`asistencia_gef_bermejo.xlsx`**: Hoja de cálculo oficial en Excel con encabezados estilizados, anchos de columna adaptados y celdas con resaltado verde para los presentes.
- **`asistencia_gef_bermejo.csv`**: Versión en formato CSV plano.
- **`supabase_schema.sql`**: Script SQL completo listo para copiar y pegar en el SQL Editor de Supabase.

---

## 🚀 Cómo Iniciar el Programa

### Opción 1: Con doble clic (Recomendado)
Haz doble clic en:
- `iniciar_asistencia.bat` (dentro de esta carpeta `Pagina we-Supabase`), o
- `iniciar_asistencia_qr.bat` (en la carpeta principal `QR`).

### Opción 2: Desde la consola / terminal
```powershell
cd "Pagina we-Supabase"
python servidor.py
```
El sistema te mostrará dos enlaces:
- **Desde tu PC:** `http://localhost:8000`
- **Desde teléfonos móviles en la misma red Wi-Fi:** `http://TU_IP_LOCAL:8000` *(Permite que los recepcionistas escaneen los gafetes desde sus propios celulares).*

---

## 🔗 Conexión entre los Dos Programas (Generador de QR y Escáner)

1. **Generación del QR:**
   El programa principal de QR (`gui.py` o `web_app.py`) genera los códigos QR con los datos de cada persona (`Nombre`, `Institución` y `Notas: N° X`).
2. **Reconocimiento por el Escáner:**
   El escáner QR de esta página web cuenta con un analizador inteligente capaz de:
   - Leer el número asignado (`#1` al `#123`).
   - Leer el nombre de la persona en texto plano o formato vCard.
   - Enlazar inmediatamente al asistente correspondiente de la lista oficial de 123 invitados.
3. **Flujo de Asistencia ("Al Escanear -> Al Aceptar"):**
   - Cuando la cámara detecta el QR (o subes la foto del QR), se abre una ventana con los datos del participante.
   - Seleccionas el día correspondiente (**DÍA 1**, **DÍA 2** o **DÍA 3**).
   - El sistema registra automáticamente la **Fecha y Hora exacta**.
   - Puedes escribir una **Observación** opcional (ej: *"Presente en la primera fila"*, *"Ingresó a las 9:30"*).
   - Al pulsar **"ACEPTAR Y MARCAR"**:
     - Se actualiza el archivo Excel `asistencia_gef_bermejo.xlsx`.
     - Se actualiza el archivo CSV.
     - Si conectaste Supabase, se actualiza también en la nube en tiempo real.
     - Suena un tono de confirmación sonoro y la tabla se actualiza al instante en verde.

---

## ☁️ Conexión con Supabase (Opcional para Nube en Tiempo Real)

Si deseas que varios teléfonos celulares o computadoras sincronicen la asistencia simultáneamente a través de internet:

1. Entra a tu cuenta en [https://supabase.com](https://supabase.com) y crea tu proyecto.
2. Ve a la sección **SQL Editor** en Supabase, copia y pega todo el contenido de [`supabase_schema.sql`](supabase_schema.sql) y haz clic en **Run**.
3. En la página web del escáner, haz clic en el botón superior **"Supabase: Desconectado"**.
4. Pega tu **Project URL** y tu **Anon Key** (los obtienes en *Project Settings > API* en Supabase).
5. Haz clic en **"Guardar y Conectar"**.
6. Puedes presionar el botón **"Subir 123 Asistentes"** para cargar toda la nómina a Supabase en un solo clic.

> **Nota:** La aplicación funciona al 100% en modo local guardando directamente en tu archivo Excel aunque no configures Supabase.

