# Sistema de Control y Asistencia QR · Proyecto GEF Bermejo

Sistema integral para el control, registro y validación de asistencia en tiempo real mediante códigos QR, sincronizado en vivo con **Microsoft Excel (`.xlsx`)** y la nube **Google Firebase Cloud Firestore**.

---

## 🚀 Inicio Rápido

### Opción 1: Ejecución Local con Excel (Recomendado para la Organización)
Si descargaste o clonaste este repositorio a tu computadora:
1. Haz doble clic en el archivo:
   ```text
   iniciar_asistencia_qr.bat
   ```
2. El sistema iniciará automáticamente el servidor local en `http://localhost:8000` y abrirá la aplicación en tu navegador predeterminado.
3. Todas las asistencias marcadas se guardarán en vivo tanto en el archivo **Excel (`asistencia_gef_bermejo.xlsx`)** como en **Firebase Cloud Firestore**.

---

### Opción 2: Uso Directo en la Web (GitHub Pages / Sin Servidor)
Puedes acceder y administrar el sistema directamente desde la web o teléfono móvil sin necesidad de instalar Python:
1. Abre el archivo `index.html` o la URL de **GitHub Pages**.
2. El sistema se conectará en tiempo real a la base de datos de **Firebase Cloud Firestore** del proyecto `otn-pbregistr`.

---

## 📱 Módulos del Sistema

1. **💻 Panel de Administración de Escritorio (`Pagina we-Supabase/index.html`):**
   * Gestión completa de participantes con tabla interactiva de 123 invitados.
   * Administración multigrupo (permite crear nuevos grupos importando archivos Excel o CSV, renombrarlos o eliminarlos).
   * Marcar y alternar asistencia por días (**Día 1**, **Día 2**, **Día 3**) o desmarcar para pruebas de ensayo.
   * Botón para restablecer pruebas y descargar el Excel actualizado en cualquier momento.

2. **📱 Versión Móvil para Recepcionistas (`Pagina we-Supabase/celular.html`):**
   * Interfaz vertical adaptada al 100% para pantallas táctiles de celulares.
   * Escáner QR de alta velocidad con la cámara del smartphone (soporta cambio de cámara trasera/frontal).
   * Búsqueda rápida por número `#N` o apellido.
   * Botones táctiles amplios para marcar asistencia al instante.

3. **📲 Emulador de Teléfono Móvil (`Pagina we-Supabase/emulador.html`):**
   * Simulador visual interactivo que permite probar la aplicación móvil desde una computadora.

---

## 📁 Estructura del Repositorio

```text
QR/
├── index.html                   # Punto de entrada principal y redirección al sistema
├── iniciar_asistencia_qr.bat    # Script de inicio del servidor local en 1 clic
├── abrir_emulador_celular.bat   # Acceso directo al emulador de celular
├── requirements.txt             # Dependencias de Python (openpyxl, etc.)
├── .gitignore                   # Protección de credenciales y archivos temporales
├── README.md                    # Documentación del sistema
└── Pagina we-Supabase/          # Núcleo de la aplicación web y servidor
    ├── index.html               # Panel de administración completo (Desktop)
    ├── celular.html             # Aplicación móvil táctil con escáner QR
    ├── emulador.html            # Emulador de celular
    ├── servidor.py              # Servidor backend Python (REST API y sync con Excel)
    ├── grupos.json              # Registro de grupos y eventos
    ├── asistencia_inicial.json  # Catálogo inicial de los 123 participantes
    └── asistencia_gef_bermejo.xlsx # Hoja de cálculo Excel oficial
```

---

## ☁️ Conexión con Firebase Firestore
El sistema incluye la configuración directa a Cloud Firestore:
* **Proyecto:** `otn-pbregistr`
* **Colección Principal:** `asistencia_gef_bermejo`
* **Colecciones Multigrupo:** `asistencia_<id_grupo>`

---

## 🛠️ Tecnologías Utilizadas
* **Frontend:** HTML5, Tailwind CSS, FontAwesome 6, Html5-QRCode Scanner Library.
* **Backend:** Python 3 (servidor HTTP nativo con soporte REST JSON y openpyxl).
* **Bases de Datos:** Google Cloud Firestore (SDK v9) y Microsoft Excel (.xlsx).
