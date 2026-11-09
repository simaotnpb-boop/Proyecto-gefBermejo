"""
Servidor Web local e interactivo para generar Códigos QR individuales y por lote.
Permite renderizar y previsualizar la aplicación directamente en cualquier navegador (Chrome, Edge, etc.).
Funciona sin frameworks pesados utilizando únicamente librerías estándar de Python y qr_engine.
"""

import os
import io
import json
import base64
import zipfile
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import qr_engine

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Generador Pro de Códigos QR - Web</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    body { background-color: #0f172a; color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; }
    .glass-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
  </style>
</head>
<body class="min-h-screen p-4 md:p-8">
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <header class="flex flex-col md:flex-row items-center justify-between pb-6 border-b border-slate-800 mb-8 gap-4">
      <div class="flex items-center gap-3">
        <div class="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
          <i class="fa-solid fa-qrcode text-2xl text-white"></i>
        </div>
        <div>
          <h1 class="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-300 bg-clip-text text-transparent">
            Generador Pro de Códigos QR
          </h1>
          <p class="text-xs text-slate-400">Personalización con Logos, vCard 3.0 y Generación Masiva para Eventos</p>
        </div>
      </div>
      <!-- Mode Tabs -->
      <div class="flex bg-slate-900 p-1.5 rounded-xl border border-slate-800">
        <button id="tabIndividualBtn" onclick="switchTab('individual')" class="px-5 py-2 rounded-lg text-sm font-semibold transition bg-blue-600 text-white shadow-md">
          <i class="fa-solid fa-user mr-1.5"></i> Individual
        </button>
        <button id="tabBatchBtn" onclick="switchTab('batch')" class="px-5 py-2 rounded-lg text-sm font-semibold transition text-slate-400 hover:text-white">
          <i class="fa-solid fa-file-excel mr-1.5"></i> Masivo (Excel/CSV)
        </button>
      </div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <!-- Columna Izquierda: Controles y Formularios -->
      <div class="lg:col-span-7 space-y-6">

        <!-- PANEL INDIVIDUAL -->
        <div id="panelIndividual" class="glass-card rounded-2xl p-6 shadow-xl space-y-6">
          <h2 class="text-lg font-bold text-white flex items-center gap-2">
            <span class="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 text-xs flex items-center justify-center">1</span>
            Datos del Asistente / Persona
          </h2>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Nombre</label>
              <input type="text" id="firstName" value="Carlos" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:outline-none">
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Apellidos</label>
              <input type="text" id="lastName" value="Gutiérrez Morales" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:outline-none">
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Institución / Empresa</label>
              <input type="text" id="org" value="Comité Organizador 2026" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:outline-none">
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Cargo / Función</label>
              <input type="text" id="title" value="Director de Eventos" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:outline-none">
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Correo Electrónico</label>
              <input type="email" id="email" value="contacto@evento2026.com" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:outline-none">
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Teléfono / WhatsApp</label>
              <input type="text" id="phone" value="+591 71800000" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:outline-none">
            </div>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-400 mb-1">Notas / DNI / Mesa / Ticket</label>
            <input type="text" id="notes" value="Mesa 5 | Acceso VIP" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:outline-none">
          </div>

          <!-- Formato de salida -->
          <div class="flex items-center gap-6 pt-2 border-t border-slate-800">
            <span class="text-xs font-semibold text-slate-300">Formato al Escanear:</span>
            <label class="inline-flex items-center text-sm cursor-pointer">
              <input type="radio" name="formatType" value="plain" checked class="text-blue-600 focus:ring-0">
              <span class="ml-2 text-slate-300 font-semibold text-emerald-400">Texto Visible (Muestra la ficha en pantalla)</span>
            </label>
            <label class="inline-flex items-center text-sm cursor-pointer">
              <input type="radio" name="formatType" value="vcard" class="text-blue-600 focus:ring-0">
              <span class="ml-2 text-slate-300">vCard (Guardar en contactos)</span>
            </label>
          </div>

          <!-- Estilo Visual -->
          <h2 class="text-lg font-bold text-white flex items-center gap-2 pt-4 border-t border-slate-800">
            <span class="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-400 text-xs flex items-center justify-center">2</span>
            Geometría Avanzada (Módulos y Ojos)
          </h2>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Patrón de Módulos / Cuerpo</label>
              <select id="moduleStyle" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none">
                <option value="square" selected>Cuadrado clásico (100% Compatible con Celulares)</option>
                <option value="dots">Puntos / Dots (Estilo GEF)</option>
                <option value="rounded">Cuadrados redondeados</option>
                <option value="horizontal_bars">Barras horizontales</option>
                <option value="vertical_bars">Barras verticales</option>
                <option value="diamond">Rombos / Diamantes</option>
                <option value="star">Estrellas 4 puntas</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Forma Marco del Ojo</label>
              <select id="eyeFrameStyle" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none">
                <option value="square" selected>Cuadrado clásico</option>
                <option value="rounded">Cuadrado redondeado</option>
                <option value="leaf">Estilo Hoja (Leaf)</option>
                <option value="circle">Círculo concéntrico</option>
                <option value="dots">Marco punteado / Bolitas</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Forma Centro del Ojo</label>
              <select id="eyeBallStyle" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none">
                <option value="square" selected>Cuadrado clásico</option>
                <option value="circle">Círculo sólido</option>
                <option value="rounded">Cuadrado redondeado</option>
                <option value="leaf">Estilo Hoja (Leaf)</option>
                <option value="dots_3x3">Matriz 3x3 puntos</option>
                <option value="bars_v">3 Barras verticales</option>
                <option value="bars_h">3 Barras horizontales</option>
                <option value="paw">Huella 🐾</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Color del QR</label>
              <div class="flex gap-2">
                <input type="color" id="moduleColor" value="#000000" class="h-9 w-12 bg-transparent rounded cursor-pointer border border-slate-700">
                <input type="text" id="moduleColorText" value="#000000" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 text-xs font-mono">
              </div>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Color de Fondo</label>
              <div class="flex gap-2">
                <input type="color" id="bgColor" value="#ffffff" class="h-9 w-12 bg-transparent rounded cursor-pointer border border-slate-700">
                <input type="text" id="bgColorText" value="#FFFFFF" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 text-xs font-mono">
              </div>
            </div>
          </div>

          <label class="inline-flex items-center gap-2 text-sm cursor-pointer text-slate-300">
            <input type="checkbox" id="jaguarBg" onchange="updatePreview()" class="rounded">
            🐆 Fondo con figura de Jaguar (detrás de los puntos)
          </label>
          <div>
            <label class="block text-xs font-medium text-slate-400 mb-1">Imagen de fondo grande (opcional, por defecto jaguar)</label>
            <input type="file" id="bgImageInput" accept="image/*" class="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white cursor-pointer">
          </div>

          <!-- Logo Central Selector -->
          <div class="p-4 bg-slate-900/60 rounded-xl border border-slate-800 space-y-4">
            <div class="flex items-center justify-between flex-wrap gap-2">
              <span class="text-xs font-bold text-slate-300">Logo o Insignia Central:</span>
              <div class="flex gap-3 text-sm flex-wrap">
                <label class="inline-flex items-center cursor-pointer">
                  <input type="radio" name="logoType" value="badge_bar" checked class="text-blue-600" onchange="toggleLogoControls()">
                  <span class="ml-1 text-slate-300 text-xs font-bold text-blue-400">Insignia GEF</span>
                </label>
                <label class="inline-flex items-center cursor-pointer">
                  <input type="radio" name="logoType" value="image" class="text-blue-600" onchange="toggleLogoControls()">
                  <span class="ml-1 text-slate-300 text-xs">Imagen PNG/JPG</span>
                </label>
                <label class="inline-flex items-center cursor-pointer">
                  <input type="radio" name="logoType" value="text" class="text-blue-600" onchange="toggleLogoControls()">
                  <span class="ml-1 text-slate-300 text-xs">Texto simple</span>
                </label>
                <label class="inline-flex items-center cursor-pointer">
                  <input type="radio" name="logoType" value="none" class="text-blue-600" onchange="toggleLogoControls()">
                  <span class="ml-1 text-slate-300 text-xs">Sin logo</span>
                </label>
              </div>
            </div>

            <!-- Controles Insignia Barra GEF Bermejo -->
            <div id="badgeBarGroup" class="grid grid-cols-1 md:grid-cols-2 gap-3 p-3 bg-slate-950/40 rounded-lg border border-slate-800">
              <div>
                <label class="block text-xs font-medium text-slate-400 mb-1">Línea 1 (Arriba)</label>
                <input type="text" id="badgeLine1" value="Proyecto" placeholder="Ej: Proyecto" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-400 mb-1">Línea 2 (Negrita / Abajo)</label>
                <input type="text" id="badgeLine2" value="GEF Bermejo" placeholder="Ej: GEF Bermejo" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm font-bold focus:border-blue-500 focus:outline-none">
              </div>
            </div>

            <div id="logoTextGroup" class="hidden">
              <label class="block text-xs font-medium text-slate-400 mb-1">Texto del Isotipo Central</label>
              <input type="text" id="logoText" value="VIP" placeholder="Ej: VIP, OTN, 2026" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm font-bold tracking-wider">
            </div>

            <div id="logoImageGroup" class="hidden">
              <label class="block text-xs font-medium text-slate-400 mb-1">Cargar Imagen de Logotipo</label>
              <input type="file" id="logoFileInput" accept="image/*" class="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer">
            </div>
          </div>
        </div>

        <!-- PANEL MASIVO (EXCEL / CSV) -->
        <div id="panelBatch" class="glass-card rounded-2xl p-6 shadow-xl space-y-6 hidden">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
              <i class="fa-solid fa-users text-lg"></i>
            </div>
            <div>
              <h2 class="text-lg font-bold text-white">Generación Masiva para Eventos</h2>
              <p class="text-xs text-slate-400">Carga tu lista en Excel o CSV y descarga un ZIP con todos los QRs</p>
            </div>
          </div>

          <div class="p-4 bg-blue-900/20 border border-blue-500/30 rounded-xl text-xs text-blue-200">
            <i class="fa-solid fa-circle-info mr-1 text-blue-400"></i>
            <b>Reconocimiento automático:</b> Detecta columnas de Nombre, Apellido, Correo, Teléfono, Cargo, Mesa, DNI, etc.
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-400 mb-2">1. Seleccionar Archivo Excel (.xlsx) o CSV</label>
            <div class="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-xl p-6 text-center cursor-pointer transition bg-slate-900/40" onclick="document.getElementById('batchFileInput').click()">
              <i class="fa-solid fa-cloud-arrow-up text-3xl text-slate-500 mb-2"></i>
              <p id="batchFileLabel" class="text-sm font-medium text-slate-300">Haz clic aquí para seleccionar tu Excel o CSV</p>
              <p class="text-xs text-slate-500 mt-1">Soporta .xlsx, .xls y .csv</p>
              <input type="file" id="batchFileInput" accept=".xlsx,.xls,.csv" class="hidden" onchange="handleBatchFileSelect(event)">
            </div>
          </div>

          <div id="batchFileInfo" class="hidden p-4 bg-emerald-950/40 border border-emerald-500/30 rounded-xl space-y-2">
            <div class="flex items-center justify-between">
              <span id="batchCountBadge" class="text-xs font-bold bg-emerald-500/20 text-emerald-300 px-2.5 py-1 rounded-full">0 Asistentes</span>
              <span id="batchFileName" class="text-xs text-slate-400">archivo.xlsx</span>
            </div>
            <p id="batchColumnsPreview" class="text-xs text-slate-300"></p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Formato de salida</label>
              <select id="batchFormat" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none">
                <option value="plain" selected>Texto Visible (Muestra datos al escanear - Recomendado)</option>
                <option value="vcard">vCard 3.0 (Guardar en la agenda)</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Nombre de los archivos</label>
              <select id="batchNaming" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none">
                <option value="numbered">001_Nombre_Apellido.png (Ordenado)</option>
                <option value="clean">Nombre_Apellido.png</option>
              </select>
            </div>
          </div>

          <button onclick="startBatchProcess()" id="batchSubmitBtn" class="w-full py-3.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl shadow-lg shadow-blue-600/30 transition flex items-center justify-center gap-2">
            <i class="fa-solid fa-bolt"></i> Generar y Descargar Todos los QRs (.ZIP)
          </button>
          
          <div id="batchProgressContainer" class="hidden space-y-2">
            <div class="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
              <div id="batchProgressBar" class="bg-blue-500 h-3 w-0 transition-all duration-300"></div>
            </div>
            <p id="batchProgressText" class="text-xs text-center text-slate-400">Procesando lista...</p>
          </div>
        </div>
      </div>

      <!-- Columna Derecha: Vista Previa y Acciones -->
      <div class="lg:col-span-5 space-y-6">
        <div class="glass-card rounded-2xl p-6 shadow-xl space-y-6 sticky top-8">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-bold text-white flex items-center gap-2">
              <i class="fa-solid fa-eye text-blue-400"></i> Vista Previa en Vivo
            </h2>
            <span class="text-xs bg-emerald-500/10 text-emerald-400 px-2.5 py-1 rounded-full border border-emerald-500/20 font-semibold">
              Corrección H (30%)
            </span>
          </div>

          <!-- Lienzo del QR -->
          <div class="aspect-square bg-slate-900/80 rounded-2xl border border-slate-800 flex items-center justify-center p-6 relative group overflow-hidden">
            <img id="qrPreviewImg" src="" alt="Vista previa QR" class="max-w-full max-h-full object-contain rounded-lg shadow-2xl transition duration-300 group-hover:scale-105">
            <div id="loadingOverlay" class="absolute inset-0 bg-slate-950/70 flex flex-col items-center justify-center gap-3 backdrop-blur-sm hidden">
              <i class="fa-solid fa-circle-notch fa-spin text-3xl text-blue-500"></i>
              <span class="text-xs font-medium text-slate-300">Generando vista previa...</span>
            </div>
          </div>

          <!-- Info y Botones -->
          <div class="space-y-3">
            <div class="flex items-center justify-between text-xs text-slate-400 px-1">
              <span id="qrDimensions">Resolución: 480 x 480 px</span>
              <span>100% Escaneable</span>
            </div>

            <button onclick="updatePreview()" class="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold rounded-xl border border-slate-700 transition flex items-center justify-center gap-2">
              <i class="fa-solid fa-arrows-rotate"></i> Actualizar Vista Previa
            </button>

            <button onclick="downloadCurrentQR()" class="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-600/30 transition flex items-center justify-center gap-2">
              <i class="fa-solid fa-download"></i> Descargar Imagen QR (.PNG)
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let uploadedLogoBase64 = null;
    let uploadedBgBase64 = null;
    let selectedBatchFile = null;

    function switchTab(mode) {
      const pInd = document.getElementById('panelIndividual');
      const pBat = document.getElementById('panelBatch');
      const bInd = document.getElementById('tabIndividualBtn');
      const bBat = document.getElementById('tabBatchBtn');

      if (mode === 'individual') {
        pInd.classList.remove('hidden');
        pBat.classList.add('hidden');
        bInd.className = "px-5 py-2 rounded-lg text-sm font-semibold transition bg-blue-600 text-white shadow-md";
        bBat.className = "px-5 py-2 rounded-lg text-sm font-semibold transition text-slate-400 hover:text-white";
      } else {
        pInd.classList.add('hidden');
        pBat.classList.remove('hidden');
        bBat.className = "px-5 py-2 rounded-lg text-sm font-semibold transition bg-blue-600 text-white shadow-md";
        bInd.className = "px-5 py-2 rounded-lg text-sm font-semibold transition text-slate-400 hover:text-white";
      }
    }

    function toggleLogoControls() {
      const val = document.querySelector('input[name="logoType"]:checked').value;
      const barGrp = document.getElementById('badgeBarGroup');
      const textGrp = document.getElementById('logoTextGroup');
      const imgGrp = document.getElementById('logoImageGroup');

      barGrp.classList.add('hidden');
      textGrp.classList.add('hidden');
      imgGrp.classList.add('hidden');

      if (val === 'badge_bar') {
        barGrp.classList.remove('hidden');
      } else if (val === 'text') {
        textGrp.classList.remove('hidden');
      } else if (val === 'image') {
        imgGrp.classList.remove('hidden');
      }
      updatePreview();
    }

    // Color Pickers sync
    document.getElementById('moduleColor').addEventListener('input', (e) => {
      document.getElementById('moduleColorText').value = e.target.value.toUpperCase();
      updatePreview();
    });
    document.getElementById('bgColor').addEventListener('input', (e) => {
      document.getElementById('bgColorText').value = e.target.value.toUpperCase();
      updatePreview();
    });

    document.getElementById('bgImageInput').addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (evt) => {
          uploadedBgBase64 = evt.target.result;
          document.getElementById('jaguarBg').checked = true;
          updatePreview();
        };
        reader.readAsDataURL(file);
      }
    });

    document.getElementById('logoFileInput').addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (evt) => {
          uploadedLogoBase64 = evt.target.result;
          updatePreview();
        };
        reader.readAsDataURL(file);
      }
    });

    // Auto-update inputs
    ['firstName', 'lastName', 'org', 'title', 'email', 'phone', 'notes', 'moduleStyle', 'eyeFrameStyle', 'eyeBallStyle', 'badgeLine1', 'badgeLine2', 'logoText'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('input', debounce(updatePreview, 400));
      if (el && el.tagName === 'SELECT') el.addEventListener('change', updatePreview);
    });
    document.querySelectorAll('input[name="formatType"]').forEach(r => r.addEventListener('change', updatePreview));

    function debounce(func, wait) {
      let timeout;
      return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
      };
    }

    async function updatePreview() {
      const overlay = document.getElementById('loadingOverlay');
      overlay.classList.remove('hidden');

      const payload = {
        firstName: document.getElementById('firstName').value,
        lastName: document.getElementById('lastName').value,
        org: document.getElementById('org').value,
        title: document.getElementById('title').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value,
        notes: document.getElementById('notes').value,
        formatType: document.querySelector('input[name="formatType"]:checked').value,
        moduleStyle: document.getElementById('moduleStyle').value,
        eyeFrameStyle: document.getElementById('eyeFrameStyle').value,
        eyeBallStyle: document.getElementById('eyeBallStyle').value,
        moduleColor: document.getElementById('moduleColor').value,
        bgColor: document.getElementById('bgColor').value,
        logoType: document.querySelector('input[name="logoType"]:checked').value,
        badgeLine1: document.getElementById('badgeLine1').value,
        badgeLine2: document.getElementById('badgeLine2').value,
        logoText: document.getElementById('logoText').value,
        logoImage: uploadedLogoBase64,
        jaguarBg: document.getElementById('jaguarBg').checked,
        bgImage: uploadedBgBase64
      };

      try {
        const res = await fetch('/api/preview', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.error) {
          alert("Error al generar QR: " + data.error);
        }
        if (data.image) {
          const img = document.getElementById('qrPreviewImg');
          img.src = "data:image/png;base64," + data.image;
          document.getElementById('qrDimensions').innerText = `Resolución: ${data.width} x ${data.height} px`;
        }
      } catch (err) {
        console.error("Error preview:", err);
      } finally {
        overlay.classList.add('hidden');
      }
    }

    function downloadCurrentQR() {
      const img = document.getElementById('qrPreviewImg');
      if (!img.src) return;
      const fn = `${document.getElementById('firstName').value}_${document.getElementById('lastName').value}_QR.png`.replace(/\\s+/g, '_');
      const a = document.createElement('a');
      a.href = img.src;
      a.download = fn;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }

    // Manejo de Lote (Excel/CSV)
    async function handleBatchFileSelect(event) {
      const file = event.target.files[0];
      if (!file) return;
      selectedBatchFile = file;

      document.getElementById('batchFileLabel').innerText = file.name;

      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await fetch('/api/inspect-batch', { method: 'POST', body: formData });
        const info = await res.json();
        if (info.total_rows !== undefined) {
          document.getElementById('batchFileInfo').classList.remove('hidden');
          document.getElementById('batchCountBadge').innerText = `👥 ${info.total_rows} Asistentes`;
          document.getElementById('batchFileName').innerText = info.filename;
          document.getElementById('batchColumnsPreview').innerText = "Columnas: " + info.columns.join(", ");
        }
      } catch (e) {
        console.error(e);
      }
    }

    async function startBatchProcess() {
      if (!selectedBatchFile) {
        alert("Por favor selecciona primero un archivo Excel o CSV.");
        return;
      }

      const btn = document.getElementById('batchSubmitBtn');
      const progBox = document.getElementById('batchProgressContainer');
      const progBar = document.getElementById('batchProgressBar');
      const progText = document.getElementById('batchProgressText');

      btn.disabled = true;
      btn.classList.add('opacity-50');
      progBox.classList.remove('hidden');
      progBar.style.width = '20%';
      progText.innerText = 'Procesando lista y generando códigos QR...';

      const formData = new FormData();
      formData.append('file', selectedBatchFile);
      formData.append('formatType', document.getElementById('batchFormat').value);
      formData.append('namingStyle', document.getElementById('batchNaming').value);
      formData.append('moduleStyle', document.getElementById('moduleStyle').value);
      formData.append('eyeFrameStyle', document.getElementById('eyeFrameStyle').value);
      formData.append('eyeBallStyle', document.getElementById('eyeBallStyle').value);
      formData.append('moduleColor', document.getElementById('moduleColor').value);
      formData.append('bgColor', document.getElementById('bgColor').value);
      formData.append('logoType', document.querySelector('input[name="logoType"]:checked').value);
      formData.append('badgeLine1', document.getElementById('badgeLine1').value);
      formData.append('badgeLine2', document.getElementById('badgeLine2').value);
      formData.append('logoText', document.getElementById('logoText').value);
      formData.append('jaguarBg', document.getElementById('jaguarBg').checked ? '1' : '0');
      if (uploadedBgBase64) formData.append('bgImage', uploadedBgBase64);
      if (uploadedLogoBase64) {
        formData.append('logoImage', uploadedLogoBase64);
      }

      progBar.style.width = '60%';

      try {
        const res = await fetch('/api/process-batch', {
          method: 'POST',
          body: formData
        });

        if (res.ok) {
          progBar.style.width = '100%';
          progText.innerText = '¡Completado! Descargando archivo ZIP...';

          const blob = await res.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `QRs_${selectedBatchFile.name.replace(/\\.[^/.]+$/, "")}.zip`;
          document.body.appendChild(a);
          a.click();
          a.remove();
        } else {
          const err = await res.json();
          alert("Error: " + err.error);
        }
      } catch (err) {
        alert("Ocurrió un error al procesar el archivo: " + err);
      } finally {
        btn.disabled = false;
        btn.classList.remove('opacity-50');
        setTimeout(() => {
          progBox.classList.add('hidden');
          progBar.style.width = '0%';
        }, 3000);
      }
    }

    // Inicializar primera vista previa
    window.onload = () => updatePreview();
  </script>
</body>
</html>
"""


class QRHttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        try:
            self._handle_post()
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            except Exception:
                pass

    def _handle_post(self):
        if self.path == "/api/preview":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8"))

            data = {
                "first_name": payload.get("firstName", ""),
                "last_name": payload.get("lastName", ""),
                "org": payload.get("org", ""),
                "title": payload.get("title", ""),
                "email": payload.get("email", ""),
                "phone": payload.get("phone", ""),
                "notes": payload.get("notes", "")
            }
            content = qr_engine.format_contact_data(data, format_type=payload.get("formatType", "plain"))

            logo_type = payload.get("logoType", "none")
            temp_logo_path = None

            if logo_type == "image" and payload.get("logoImage"):
                try:
                    img_data = payload["logoImage"].split(",")[-1]
                    raw_bytes = base64.b64decode(img_data)
                    temp_logo_path = "temp_web_logo.png"
                    with open(temp_logo_path, "wb") as f:
                        f.write(raw_bytes)
                except Exception:
                    logo_type = "none"

            temp_bg_path = save_data_url(payload.get("bgImage"), "temp_web_bg.png")

            qr_img = qr_engine.generate_qr(
                content=content,
                module_color=payload.get("moduleColor", "#000000"),
                bg_color=payload.get("bgColor", "#FFFFFF"),
                module_style=payload.get("moduleStyle", "square"),
                eye_frame_style=payload.get("eyeFrameStyle", "square"),
                eye_ball_style=payload.get("eyeBallStyle", "square"),
                logo_type=logo_type,
                badge_line1=payload.get("badgeLine1", "Proyecto"),
                badge_line2=payload.get("badgeLine2", "GEF Bermejo"),
                logo_path=temp_logo_path,
                logo_text=payload.get("logoText", ""),
                logo_ratio=0.18,
                logo_badge=True,
                jaguar_background=bool(payload.get("jaguarBg", False)),
                jaguar_image_path=temp_bg_path
            )
            full_name = f"{data['first_name']} {data['last_name']}".strip()
            if full_name:
                qr_img = qr_engine.add_name_label_below_qr(
                    qr_img,
                    full_name=full_name,
                    bg_color=qr_engine.hex_to_rgb(payload.get("bgColor", "#FFFFFF")),
                    text_color=qr_engine.hex_to_rgb(payload.get("moduleColor", "#000000"))
                )
            if temp_bg_path and os.path.exists(temp_bg_path):
                os.remove(temp_bg_path)

            if temp_logo_path and os.path.exists(temp_logo_path):
                try:
                    os.remove(temp_logo_path)
                except Exception:
                    pass

            buf = io.BytesIO()
            qr_img.save(buf, format="PNG")
            b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")

            w, h = qr_img.size
            response = json.dumps({"image": b64_img, "width": w, "height": h})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))

        elif self.path == "/api/inspect-batch":
            content_type = self.headers.get("Content-Type", "")
            length = int(self.headers.get("Content-Length", 0))
            raw_data = self.rfile.read(length)

            # Extraer archivo del multipart
            filename, file_bytes = parse_multipart_file(raw_data, content_type)
            temp_path = os.path.join(os.getcwd(), f"temp_inspect_{filename}")
            with open(temp_path, "wb") as f:
                f.write(file_bytes)

            try:
                info = qr_engine.inspect_batch_file(temp_path)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(info).encode("utf-8"))

        elif self.path == "/api/process-batch":
            content_type = self.headers.get("Content-Type", "")
            length = int(self.headers.get("Content-Length", 0))
            raw_data = self.rfile.read(length)

            fields, files = parse_multipart_all(raw_data, content_type)
            if "file" not in files:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No se recibió archivo"}).encode("utf-8"))
                return

            upload_name, upload_bytes = files["file"]
            temp_batch_file = os.path.join(os.getcwd(), f"temp_batch_{upload_name}")
            with open(temp_batch_file, "wb") as f:
                f.write(upload_bytes)

            temp_out_dir = os.path.join(os.getcwd(), f"temp_batch_out_{int(os.times()[4])}")
            os.makedirs(temp_out_dir, exist_ok=True)

            # Logo opcional
            temp_logo_path = None
            logo_type = fields.get("logoType", "none")
            if logo_type == "image" and "logoImage" in fields:
                try:
                    img_data = fields["logoImage"].split(",")[-1]
                    raw_bytes = base64.b64decode(img_data)
                    temp_logo_path = os.path.join(os.getcwd(), "temp_batch_logo.png")
                    with open(temp_logo_path, "wb") as f:
                        f.write(raw_bytes)
                except Exception:
                    logo_type = "none"

            temp_bg_path = save_data_url(fields.get("bgImage"), os.path.join(os.getcwd(), "temp_batch_bg.png"))
            qr_opts = {
                "module_color": fields.get("moduleColor", "#000000"),
                "bg_color": fields.get("bgColor", "#FFFFFF"),
                "module_style": fields.get("moduleStyle", "square"),
                "eye_frame_style": fields.get("eyeFrameStyle", "square"),
                "eye_ball_style": fields.get("eyeBallStyle", "square"),
                "logo_type": logo_type,
                "badge_line1": fields.get("badgeLine1", "Proyecto"),
                "badge_line2": fields.get("badgeLine2", "GEF Bermejo"),
                "logo_path": temp_logo_path,
                "logo_text": fields.get("logoText", ""),
                "logo_ratio": 0.18,
                "logo_badge": True,
                "jaguar_background": fields.get("jaguarBg", "0") == "1",
                "jaguar_image_path": temp_bg_path
            }

            try:
                res = qr_engine.process_batch(
                    file_path=temp_batch_file,
                    output_dir=temp_out_dir,
                    format_type=fields.get("formatType", "plain"),
                    qr_options=qr_opts,
                    filename_style=fields.get("namingStyle", "numbered")
                )

                # Empaquetar todo en un ZIP en memoria
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for root, _, filenames in os.walk(temp_out_dir):
                        for fn in filenames:
                            fp = os.path.join(root, fn)
                            zf.write(fp, arcname=fn)

                zip_bytes = zip_buffer.getvalue()

                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", f'attachment; filename="QRs_{upload_name}.zip"')
                self.send_header("Content-Length", str(len(zip_bytes)))
                self.end_headers()
                self.wfile.write(zip_bytes)

            finally:
                # Limpieza de archivos temporales
                if os.path.exists(temp_batch_file):
                    os.remove(temp_batch_file)
                if temp_logo_path and os.path.exists(temp_logo_path):
                    os.remove(temp_logo_path)
                if temp_bg_path and os.path.exists(temp_bg_path):
                    os.remove(temp_bg_path)
                import shutil
                if os.path.exists(temp_out_dir):
                    shutil.rmtree(temp_out_dir, ignore_errors=True)


def save_data_url(data_url, path):
    """Guarda una imagen enviada como data URL base64; devuelve la ruta o None."""
    if not data_url:
        return None
    try:
        with open(path, "wb") as f:
            f.write(base64.b64decode(data_url.split(",")[-1]))
        return path
    except Exception:
        return None


def parse_multipart_file(raw_data: bytes, content_type: str):
    """Extrae el primer archivo de un payload multipart sin truncar bytes binarios."""
    boundary = content_type.split("boundary=")[-1].strip().strip('"').encode()
    parts = raw_data.split(b"--" + boundary)
    for p in parts:
        if b'filename="' in p and b"\r\n\r\n" in p:
            header, content = p.split(b"\r\n\r\n", 1)
            if content.endswith(b"\r\n"):
                content = content[:-2]
            header_str = header.decode("latin1", errors="ignore")
            import re
            m = re.search(r'filename="([^"]+)"', header_str)
            fn = m.group(1) if m else "archivo.xlsx"
            return fn, content
    return "archivo.xlsx", b""


def parse_multipart_all(raw_data: bytes, content_type: str):
    """Extrae todos los campos de texto y archivos de un multipart sin corromper binarios."""
    boundary = content_type.split("boundary=")[-1].strip().strip('"').encode()
    parts = raw_data.split(b"--" + boundary)
    fields = {}
    files = {}

    for p in parts:
        if not p or p == b"--" or p == b"--\r\n":
            continue
        if b"\r\n\r\n" in p:
            header, content = p.split(b"\r\n\r\n", 1)
            if content.endswith(b"\r\n"):
                content = content[:-2]
            header_str = header.decode("latin1", errors="ignore")
            import re
            name_m = re.search(r'name="([^"]+)"', header_str)
            fn_m = re.search(r'filename="([^"]+)"', header_str)

            if fn_m and name_m:
                files[name_m.group(1)] = (fn_m.group(1), content)
            elif name_m:
                fields[name_m.group(1)] = content.decode("utf-8", errors="ignore")

    return fields, files


def run_web_server(port=5000):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, QRHttpHandler)
    print("==================================================================")
    print(f"Servidor Web del Generador QR activo en: http://localhost:{port}")
    print("==================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Servidor detenido.")


if __name__ == "__main__":
    run_web_server(5000)
