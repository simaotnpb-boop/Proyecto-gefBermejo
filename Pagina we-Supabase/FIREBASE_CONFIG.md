# Guía de Conexión y Base de Datos Firebase (Cloud Firestore)
## Sistema de Asistencia y Escáner QR - Proyecto GEF Bermejo

Esta guía explica cómo activar tu base de datos en Google Firebase y conectar el sistema para que toda la información se guarde en la nube en tiempo real.

---

### Paso 1: Activar Cloud Firestore en tu Consola de Firebase

1. Ingresa a la [Consola de Firebase](https://console.firebase.google.com/) con tu cuenta de Google.
2. Selecciona tu proyecto (o crea uno si aún no lo hiciste).
3. En el menú de navegación izquierdo, ve a **Compilación (Build)** > **Firestore Database**.
4. Haz clic en el botón **"Crear base de datos"** (*Create database*).
5. En la ventana de configuración:
   - **Ubicación de la base de datos:** Elige la más cercana (ejemplo: `us-central1` o `southamerica-east1`).
   - **Reglas de seguridad:** Selecciona **"Iniciar en modo de prueba"** (*Start in test mode*) para permitir lectura y escritura inmediatas sin restricciones de autenticación.
6. Haz clic en **Habilitar** (*Enable*).

---

### Paso 2: Copiar las Reglas de Seguridad (Imprescindible para sincronización multigrupo)

En la pestaña **Reglas** (*Rules*) de Firestore Database, copia y pega estas reglas para permitir que todas las listas y la configuración de grupos se sincronicen entre PC, celulares y GitHub Pages:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```
Haz clic en **Publicar** (*Publish*).

---

### Paso 3: Obtener las Credenciales de tu Aplicación Web

1. En la consola de Firebase, haz clic en el icono del engranaje ⚙️ (arriba a la izquierda, junto a *Descripción general del proyecto*) y elige **Configuración del proyecto** (*Project settings*).
2. En la pestaña **General**, baja hasta la sección **"Tus apps"** (*Your apps*).
3. Haz clic en el icono Web **`</>`**.
4. Escribe un apodo (ej: `Asistencia QR`) y haz clic en **Registrar app**.
5. Firebase te mostrará un bloque de código como este:

```javascript
const firebaseConfig = {
  apiKey: "TU_API_KEY_DE_FIREBASE",
  authDomain: "tu-proyecto.firebaseapp.com",
  projectId: "tu-proyecto-id",
  storageBucket: "tu-proyecto.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdef123456"
};
```
Copia todo ese texto.

---

### Paso 4: Conectar y Subir los 123 Participantes

#### Opción A: Desde la Página Web del Escáner (Más Fácil)
1. Abre el sistema en tu navegador (doble clic en `iniciar_asistencia_qr.bat` o `http://localhost:8000`).
2. Haz clic en el botón superior **"Firebase: Desconectado"** (con el ícono de fuego 🔥).
3. Pega el bloque de código que copiaste en el paso anterior.
4. Haz clic en **"Guardar y Conectar"**. El indicador cambiará a color verde: **"Firebase: Conectado"**.
5. Haz clic en el botón verde **"Subir 123 Asistentes"**.
   - En 1 segundo se creará la colección `asistencia_gef_bermejo` con los 123 documentos iniciales.

#### Opción B: Desde la Consola con Python
Si prefieres subirlos desde la terminal:
```bash
cd "Pagina we-Supabase"
python subir_a_firebase.py
```
Introduce el `Project ID` cuando te lo pida y listo.

---

### Estructura de la Colección en Firestore

* **Nombre de la colección:** `asistencia_gef_bermejo`
* **ID de cada documento:** Número de participante (`1`, `2`, ..., `123`)
* **Campos almacenados por participante:**
  - `numero`: Entero (1 a 123)
  - `nombre`: Nombre completo
  - `institucion`: Organización o cargo
  - `estado_general`: `"Pendiente"` o `"PRESENTE"`
  - `dia_1`: `"Ausente"` o `"PRESENTE"`
  - `dia_1_fecha_hora`: Fecha y hora del escaneo (ej. `2026-11-07 15:30:12`)
  - `dia_1_observacion`: Observaciones agregadas al escanear
  - `dia_2`, `dia_2_fecha_hora`, `dia_2_observacion`: Asistencia Día 2
  - `dia_3`, `dia_3_fecha_hora`, `dia_3_observacion`: Asistencia Día 3
  - `actualizado_en`: Timestamp del servidor de Firebase

---

### Sincronización en Tiempo Real

* Cada vez que se escanea un código QR o se confirma la asistencia desde la PC o celular, se actualiza:
  1. El archivo Excel local `asistencia_gef_bermejo.xlsx`.
  2. El archivo CSV local `asistencia_gef_bermejo.csv`.
  3. **Cloud Firestore en Firebase en tiempo real.**
* Cualquier otro dispositivo conectado verá la pantalla actualizarse automáticamente sin necesidad de recargar la página.

