"""
Interfaz gráfica de usuario moderna con CustomTkinter para la generación
de códigos QR personalizados con logos y datos de contacto.
"""

import os
import threading
from tkinter import colorchooser, filedialog, messagebox
from typing import Optional
from PIL import Image
import customtkinter as ctk

from qr_engine import (
    format_contact_data,
    generate_qr,
    add_name_label_below_qr,
    compose_gafete_image,
    detect_gafete_layout,
    hex_to_rgb,
    process_batch,
    inspect_batch_file
)

# Configuración inicial de CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class QRGeneratorApp(ctk.CTk):
    """Aplicación principal de escritorio para generar códigos QR personalizados."""

    def __init__(self):
        super().__init__()

        # Configuración de la ventana principal
        self.title("Generador Pro de Códigos QR Personalizados")
        self.geometry("1100x760")
        self.minsize(980, 680)

        # Variables de estado
        self.current_qr_img: Optional[Image.Image] = None
        self.logo_path_var = ctk.StringVar(value="")
        self.module_color_var = ctk.StringVar(value="#000000")
        self.bg_color_var = ctk.StringVar(value="#FFFFFF")
        self.format_type_var = ctk.StringVar(value="quick")
        self.module_style_var = ctk.StringVar(value="square")
        self.eye_frame_style_var = ctk.StringVar(value="square")
        self.eye_ball_style_var = ctk.StringVar(value="square")
        self.logo_type_var = ctk.StringVar(value="badge_bar")
        self.badge_line1_var = ctk.StringVar(value="Proyecto")
        self.badge_line2_var = ctk.StringVar(value="GEF Bermejo")
        self.logo_ratio_var = ctk.DoubleVar(value=0.18)
        self.logo_badge_var = ctk.BooleanVar(value=True)
        self.jaguar_bg_var = ctk.BooleanVar(value=False)
        self.bg_image_path_var = ctk.StringVar(value="")
        self.eye_image_path_var = ctk.StringVar(value="")
        self.gafete_enabled_var = ctk.BooleanVar(value=False)
        self.gafete_path_var = ctk.StringVar(value="")

        default_gafete_layout = detect_gafete_layout(None)
        self.gafete_qr_x_var = ctk.DoubleVar(value=default_gafete_layout["qr_x"])
        self.gafete_qr_y_var = ctk.DoubleVar(value=default_gafete_layout["qr_y"])
        self.gafete_qr_size_var = ctk.DoubleVar(value=default_gafete_layout["qr_size"])
        self.gafete_name_x_var = ctk.DoubleVar(value=default_gafete_layout["name_x"])
        self.gafete_name_y_var = ctk.DoubleVar(value=default_gafete_layout["name_y"])
        self.gafete_name_size_var = ctk.DoubleVar(value=default_gafete_layout["name_size"])
        self.gafete_name_font_var = ctk.StringVar(value="Montserrat (Moderna y Limpia)")
        self.gafete_name_spacing_var = ctk.DoubleVar(value=100.0)      # Espaciado horizontal entre letras (%)
        self.gafete_name_line_spacing_var = ctk.DoubleVar(value=100.0) # Separación vertical entre líneas (%)
        self._preview_drag_target: Optional[str] = None
        self._preview_rendered_size = (380, 440)
        self._cached_base_qr_img: Optional[Image.Image] = None
        self._cached_base_qr_key: Optional[tuple] = None

        # Variables para proceso por lote
        self.batch_file_var = ctk.StringVar(value="")
        self.batch_output_var = ctk.StringVar(value="")

        # Construcción del layout principal
        self._build_layout()

        # Generar un QR inicial de demostración
        self.after(300, self._generate_preview)

    def _build_layout(self):
        """Construye las dos columnas principales: panel de control y vista previa."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ==========================================
        # COLUMNA IZQUIERDA: Pestañas / Controles
        # ==========================================
        self.left_frame = ctk.CTkFrame(self, corner_radius=12)
        self.left_frame.grid(row=0, column=0, padx=(16, 8), pady=16, sticky="nsew")
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        # Cabecera con selector de modo (Individual vs Lote)
        self.mode_segmented = ctk.CTkSegmentedButton(
            self.left_frame,
            values=["Datos Individuales", "Generación Masiva (Lote)"],
            command=self._on_mode_change,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.mode_segmented.set("Datos Individuales")
        self.mode_segmented.grid(row=0, column=0, padx=16, pady=(16, 10), sticky="ew")

        # Contenedor para vista individual
        self.individual_container = ctk.CTkScrollableFrame(self.left_frame, corner_radius=8)
        self.individual_container.grid(row=1, column=0, padx=14, pady=(0, 14), sticky="nsew")
        self.individual_container.grid_columnconfigure(0, weight=1)
        self.individual_container.grid_columnconfigure(1, weight=1)

        # Contenedor para vista masiva
        self.batch_container = ctk.CTkScrollableFrame(self.left_frame, corner_radius=8)
        self.batch_container.grid_columnconfigure(0, weight=1)

        # Construir contenido de cada pestaña
        self._build_individual_form()
        self._build_batch_form()

        # ==========================================
        # COLUMNA DERECHA: Vista Previa y Exportación
        # ==========================================
        self.right_frame = ctk.CTkFrame(self, corner_radius=12)
        self.right_frame.grid(row=0, column=1, padx=(8, 16), pady=16, sticky="nsew")
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        # Barra superior derecha: Tema de apariencia
        theme_bar = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        theme_bar.grid(row=0, column=0, padx=16, pady=(14, 4), sticky="ew")
        theme_bar.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(
            theme_bar,
            text="Vista Previa en Alta Resolución",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_lbl.grid(row=0, column=0, sticky="w")

        self.theme_menu = ctk.CTkOptionMenu(
            theme_bar,
            values=["Dark", "Light", "System"],
            command=ctk.set_appearance_mode,
            width=90,
            height=28
        )
        self.theme_menu.set("Dark")
        self.theme_menu.grid(row=0, column=1, sticky="e")

        # Lienzo / Marco de imagen QR
        self.preview_canvas_frame = ctk.CTkFrame(self.right_frame, fg_color=("gray85", "#18181b"), corner_radius=10)
        self.preview_canvas_frame.grid(row=1, column=0, padx=16, pady=10, sticky="nsew")
        self.preview_canvas_frame.grid_rowconfigure(0, weight=1)
        self.preview_canvas_frame.grid_columnconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(self.preview_canvas_frame, text="Generando código QR...")
        self.preview_label.grid(row=0, column=0, padx=10, pady=10)
        self.preview_label.bind("<ButtonPress-1>", self._on_preview_press)
        self.preview_label.bind("<B1-Motion>", self._on_preview_drag)
        self.preview_label.bind("<MouseWheel>", self._on_preview_wheel)

        # Barra de ajuste rápido de tamaño de texto justo debajo de la Vista Previa
        quick_text_bar = ctk.CTkFrame(self.right_frame, fg_color=("gray90", "#27272a"), corner_radius=8)
        quick_text_bar.grid(row=2, column=0, padx=16, pady=(0, 6), sticky="ew")

        ctk.CTkLabel(
            quick_text_bar,
            text="🔤 Tamaño Texto:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=(10, 4), pady=4)

        ctk.CTkButton(
            quick_text_bar, text="➖ Achicar", width=85, height=26,
            fg_color="#475569", hover_color="#334155", font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self._shrink_text_size(5.0)
        ).pack(side="left", padx=2, pady=4)

        self.lbl_quick_nm_sz = ctk.CTkLabel(
            quick_text_bar,
            text=f"{self.gafete_name_size_var.get():.0f}%",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38bdf8",
            width=45
        )
        self.lbl_quick_nm_sz.pack(side="left", padx=2, pady=4)

        ctk.CTkButton(
            quick_text_bar, text="➕ Agrandar", width=90, height=26,
            fg_color="#2563eb", hover_color="#1d4ed8", font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self._grow_text_size(5.0)
        ).pack(side="left", padx=2, pady=4)

        ctk.CTkButton(
            quick_text_bar, text="Normal 100%", width=90, height=26,
            fg_color="#0f766e", hover_color="#115e59", font=ctk.CTkFont(size=11),
            command=lambda: self._set_name_size_preset(100.0)
        ).pack(side="left", padx=2, pady=4)

        ctk.CTkButton(
            quick_text_bar, text="Grande 120%", width=90, height=26,
            fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=11),
            command=lambda: self._set_name_size_preset(120.0)
        ).pack(side="left", padx=2, pady=4)

        # Barra de estado informativo
        self.status_label = ctk.CTkLabel(
            self.right_frame,
            text="Listo | Redundancia: Alta (H 30%)",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        self.status_label.grid(row=3, column=0, padx=16, pady=(0, 6), sticky="w")

        # Botones de acción inferior
        actions_bar = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        actions_bar.grid(row=4, column=0, padx=16, pady=(0, 16), sticky="ew")
        actions_bar.grid_columnconfigure((0, 1), weight=1)

        self.btn_preview = ctk.CTkButton(
            actions_bar,
            text="🔄 Actualizar Vista Previa",
            command=self._generate_preview,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.btn_preview.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.btn_save = ctk.CTkButton(
            actions_bar,
            text="💾 Guardar Imagen QR",
            command=self._save_qr_image,
            fg_color="#10b981",
            hover_color="#059669",
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.btn_save.grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def _build_individual_form(self):
        """Construye el formulario de entrada de datos individuales y opciones de diseño."""
        f = self.individual_container

        # --- SECCIÓN 1: DATOS DE LA PERSONA ---
        sec1 = ctk.CTkLabel(f, text="1. Datos de la Persona", font=ctk.CTkFont(size=14, weight="bold"))
        sec1.grid(row=0, column=0, columnspan=2, sticky="w", pady=(4, 6))

        # Nombre y Apellidos
        self.entry_first_name = ctk.CTkEntry(f, placeholder_text="Nombre(s)")
        self.entry_first_name.insert(0, "Carlos")
        self.entry_first_name.grid(row=1, column=0, padx=(0, 6), pady=4, sticky="ew")

        self.entry_last_name = ctk.CTkEntry(f, placeholder_text="Apellidos")
        self.entry_last_name.insert(0, "Gutiérrez Morales")
        self.entry_last_name.grid(row=1, column=1, padx=(6, 0), pady=4, sticky="ew")

        # Institución y Cargo
        self.entry_org = ctk.CTkEntry(f, placeholder_text="Institución / Organización")
        self.entry_org.insert(0, "OTN Pilcomayo y Bermejo")
        self.entry_org.grid(row=2, column=0, padx=(0, 6), pady=4, sticky="ew")

        self.entry_title = ctk.CTkEntry(f, placeholder_text="Cargo / Función")
        self.entry_title.insert(0, "Director de Tecnología")
        self.entry_title.grid(row=2, column=1, padx=(6, 0), pady=4, sticky="ew")

        # Correo y Teléfono
        self.entry_email = ctk.CTkEntry(f, placeholder_text="Correo Electrónico")
        self.entry_email.insert(0, "contacto@otnpb.gob.bo")
        self.entry_email.grid(row=3, column=0, padx=(0, 6), pady=4, sticky="ew")

        self.entry_phone = ctk.CTkEntry(f, placeholder_text="Teléfono / Móvil")
        self.entry_phone.insert(0, "+591 71800000")
        self.entry_phone.grid(row=3, column=1, padx=(6, 0), pady=4, sticky="ew")

        # Notas / Observaciones
        self.entry_notes = ctk.CTkEntry(f, placeholder_text="Notas / Otros datos adicionales")
        self.entry_notes.insert(0, "Identificación autorizada 2026")
        self.entry_notes.grid(row=4, column=0, columnspan=2, pady=4, sticky="ew")

        # Formato de codificación
        fmt_frame = ctk.CTkFrame(f, fg_color="transparent")
        fmt_frame.grid(row=5, column=0, columnspan=2, pady=(6, 12), sticky="ew")
        ctk.CTkLabel(fmt_frame, text="Formato de salida:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")

        ctk.CTkRadioButton(
            fmt_frame, text="Credencial / Asistencia (Jala datos de Firebase en Escritorio y Web)",
            variable=self.format_type_var, value="quick"
        ).pack(side="left", padx=6)

        ctk.CTkRadioButton(
            fmt_frame, text="vCard (Tarjeta de Contacto)",
            variable=self.format_type_var, value="vcard"
        ).pack(side="left", padx=6)

        ctk.CTkRadioButton(
            fmt_frame, text="Texto Completo",
            variable=self.format_type_var, value="plain"
        ).pack(side="left", padx=6)

        # --- SECCIÓN 2: ESTILO VISUAL DEL QR (MÓDULOS Y OJOS) ---
        sec2 = ctk.CTkLabel(f, text="2. Estilo Visual y Geometría (Módulos y Ojos)", font=ctk.CTkFont(size=14, weight="bold"))
        sec2.grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 6))

        # 2.1 Estilo de módulos / cuerpo
        ctk.CTkLabel(f, text="Forma de Puntos / Módulos:", font=ctk.CTkFont(size=12)).grid(row=7, column=0, sticky="w", pady=2)
        self.module_style_menu = ctk.CTkOptionMenu(
            f,
            values=[
                "Cuadrado clásico (100% Compatible iPhone y Android)",
                "Puntos / Dots (Estilo GEF Bermejo)",
                "Círculos completos",
                "Cuadrados redondeados",
                "Barras horizontales",
                "Barras verticales",
                "Rombos / Diamantes",
                "Estrellas 4 puntas"
            ],
            command=self._on_style_selected
        )
        self.module_style_menu.set("Cuadrado clásico (100% Compatible iPhone y Android)")
        self.module_style_menu.grid(row=7, column=1, sticky="ew", pady=2)

        # 2.2 Forma del Marco del Ojo (Finder Frame)
        ctk.CTkLabel(f, text="Forma Marco del Ojo:", font=ctk.CTkFont(size=12)).grid(row=8, column=0, sticky="w", pady=2)
        self.eye_frame_menu = ctk.CTkOptionMenu(
            f,
            values=[
                "Cuadrado clásico",
                "Cuadrado redondeado",
                "Estilo Hoja (Leaf)",
                "Círculo concéntrico",
                "Marco punteado / Bolitas"
            ],
            command=self._on_eye_frame_selected
        )
        self.eye_frame_menu.set("Cuadrado clásico")
        self.eye_frame_menu.grid(row=8, column=1, sticky="ew", pady=2)

        # 2.3 Forma del Centro del Ojo (Finder Core)
        ctk.CTkLabel(f, text="Forma Centro del Ojo:", font=ctk.CTkFont(size=12)).grid(row=9, column=0, sticky="w", pady=2)
        self.eye_ball_menu = ctk.CTkOptionMenu(
            f,
            values=[
                "Cuadrado clásico",
                "Círculo sólido",
                "Cuadrado redondeado",
                "Estilo Hoja (Leaf)",
                "Matriz 3x3 puntos",
                "3 Barras verticales",
                "3 Barras horizontales",
                "Huella 🐾",
                "Imagen personalizada..."
            ],
            command=self._on_eye_ball_selected
        )
        self.eye_ball_menu.set("Cuadrado clásico")
        self.eye_ball_menu.grid(row=9, column=1, sticky="ew", pady=2)

        # Fondo con figura de jaguar detrás de los puntos
        self.switch_jaguar = ctk.CTkSwitch(
            f, text="🐆 Fondo con figura de Jaguar (detrás de los puntos)",
            variable=self.jaguar_bg_var,
            command=self._generate_preview
        )
        self.switch_jaguar.grid(row=17, column=0, columnspan=2, pady=(0, 4), sticky="w")

        bg_img_box = ctk.CTkFrame(f, fg_color="transparent")
        bg_img_box.grid(row=18, column=0, columnspan=2, pady=(0, 12), sticky="ew")
        ctk.CTkButton(
            bg_img_box, text="🖼 Elegir imagen de fondo...", height=28,
            command=self._choose_bg_image
        ).pack(side="left", padx=(0, 6))
        self.bg_image_label = ctk.CTkLabel(
            bg_img_box, text="(jaguar por defecto)",
            font=ctk.CTkFont(size=11), text_color="gray60"
        )
        self.bg_image_label.pack(side="left")

        # --- SECCIÓN 4: PLANTILLA DE GAFETE (OPCIONAL Y ADAPTABLE) ---
        sec4 = ctk.CTkLabel(f, text="4. Diseño de Gafete (Opcional y Adaptable)", font=ctk.CTkFont(size=14, weight="bold"))
        sec4.grid(row=19, column=0, columnspan=2, sticky="w", pady=(8, 4))

        self.switch_gafete = ctk.CTkSwitch(
            f, text="🪪 Habilitar imagen de Gafete (Adaptable a cualquier estilo)",
            variable=self.gafete_enabled_var,
            command=self._generate_preview
        )
        self.switch_gafete.grid(row=20, column=0, columnspan=2, pady=(0, 4), sticky="w")

        gafete_img_box = ctk.CTkFrame(f, fg_color="transparent")
        gafete_img_box.grid(row=21, column=0, columnspan=2, pady=(0, 6), sticky="ew")
        ctk.CTkButton(
            gafete_img_box, text="🪪 Elegir imagen de gafete...", height=28,
            command=self._choose_gafete_image
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            gafete_img_box, text="🎯 Auto-ajustar a plantilla", height=28,
            fg_color="#0ea5e9", hover_color="#0284c7",
            command=self._auto_detect_gafete_layout
        ).pack(side="left", padx=(0, 6))
        self.gafete_image_label = ctk.CTkLabel(
            gafete_img_box, text="(plantilla GEF Bermejo por defecto)",
            font=ctk.CTkFont(size=11), text_color="gray60"
        )
        self.gafete_image_label.pack(side="left")

        # Panel de ajuste libre de Posición (X, Y) y Tamaño para el QR y el Nombre en el Gafete
        self.gafete_adjust_frame = ctk.CTkFrame(f, fg_color=("gray90", "#27272a"), corner_radius=8)
        self.gafete_adjust_frame.grid(row=22, column=0, columnspan=2, pady=(0, 14), sticky="ew")
        self.gafete_adjust_frame.grid_columnconfigure(1, weight=1)
        self.gafete_adjust_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            self.gafete_adjust_frame,
            text="📐 Ajustes de Gafete (Posición, Tamaño y Tipografía):",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, columnspan=4, padx=8, pady=(6, 4), sticky="w")

        # Controles QR y Nombre: Posición X
        self.lbl_gaf_qr_x = ctk.CTkLabel(self.gafete_adjust_frame, text=f"QR Pos X ({self.gafete_qr_x_var.get():.0f}%):", font=ctk.CTkFont(size=11))
        self.lbl_gaf_qr_x.grid(row=1, column=0, padx=(8, 4), pady=2, sticky="w")
        ctk.CTkSlider(
            self.gafete_adjust_frame, from_=10, to=90, variable=self.gafete_qr_x_var,
            command=lambda _: self._on_gafete_layout_change()
        ).grid(row=1, column=1, padx=4, pady=2, sticky="ew")

        self.lbl_gaf_nm_x = ctk.CTkLabel(self.gafete_adjust_frame, text=f"Nombre X ({self.gafete_name_x_var.get():.0f}%):", font=ctk.CTkFont(size=11))
        self.lbl_gaf_nm_x.grid(row=1, column=2, padx=(8, 4), pady=2, sticky="w")
        ctk.CTkSlider(
            self.gafete_adjust_frame, from_=10, to=90, variable=self.gafete_name_x_var,
            command=lambda _: self._on_gafete_layout_change()
        ).grid(row=1, column=3, padx=(4, 8), pady=2, sticky="ew")

        # Controles QR y Nombre: Posición Y
        self.lbl_gaf_qr_y = ctk.CTkLabel(self.gafete_adjust_frame, text=f"QR Pos Y ({self.gafete_qr_y_var.get():.0f}%):", font=ctk.CTkFont(size=11))
        self.lbl_gaf_qr_y.grid(row=2, column=0, padx=(8, 4), pady=2, sticky="w")
        ctk.CTkSlider(
            self.gafete_adjust_frame, from_=10, to=92, variable=self.gafete_qr_y_var,
            command=lambda _: self._on_gafete_layout_change()
        ).grid(row=2, column=1, padx=4, pady=2, sticky="ew")

        self.lbl_gaf_nm_y = ctk.CTkLabel(self.gafete_adjust_frame, text=f"Nombre Y ({self.gafete_name_y_var.get():.0f}%):", font=ctk.CTkFont(size=11))
        self.lbl_gaf_nm_y.grid(row=2, column=2, padx=(8, 4), pady=2, sticky="w")
        ctk.CTkSlider(
            self.gafete_adjust_frame, from_=5, to=95, variable=self.gafete_name_y_var,
            command=lambda _: self._on_gafete_layout_change()
        ).grid(row=2, column=3, padx=(4, 8), pady=2, sticky="ew")

        # Controles QR: Tamaño QR
        self.lbl_gaf_qr_sz = ctk.CTkLabel(self.gafete_adjust_frame, text=f"Tamaño QR ({self.gafete_qr_size_var.get():.0f}%):", font=ctk.CTkFont(size=11))
        self.lbl_gaf_qr_sz.grid(row=3, column=0, padx=(8, 4), pady=(2, 4), sticky="w")
        ctk.CTkSlider(
            self.gafete_adjust_frame, from_=15, to=75, variable=self.gafete_qr_size_var,
            command=lambda _: self._on_gafete_layout_change()
        ).grid(row=3, column=1, padx=4, pady=(2, 4), sticky="ew")

        # --- SECCIÓN DEDICADA: AGRANDAR O ACHICAR TEXTO ---
        text_size_box = ctk.CTkFrame(self.gafete_adjust_frame, fg_color=("gray85", "#1e1e24"), corner_radius=6)
        text_size_box.grid(row=4, column=0, columnspan=4, padx=6, pady=(6, 4), sticky="ew")

        ts_head = ctk.CTkFrame(text_size_box, fg_color="transparent")
        ts_head.pack(fill="x", padx=6, pady=(4, 2))

        self.lbl_gaf_nm_sz = ctk.CTkLabel(
            ts_head,
            text=f"🔤 Tamaño del Texto: {self.gafete_name_size_var.get():.0f}%",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_gaf_nm_sz.pack(side="left")

        ctk.CTkButton(
            ts_head, text="➖ Achicar", width=75, height=24,
            fg_color="#475569", hover_color="#334155", font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self._shrink_text_size(5.0)
        ).pack(side="right", padx=(2, 0))

        ctk.CTkButton(
            ts_head, text="➕ Agrandar", width=80, height=24,
            fg_color="#2563eb", hover_color="#1d4ed8", font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self._grow_text_size(5.0)
        ).pack(side="right", padx=2)

        ts_slider_row = ctk.CTkFrame(text_size_box, fg_color="transparent")
        ts_slider_row.pack(fill="x", padx=6, pady=2)
        ctk.CTkLabel(ts_slider_row, text="40%", font=ctk.CTkFont(size=10), text_color="gray60").pack(side="left")
        self.slider_indiv_nm_sz = ctk.CTkSlider(
            ts_slider_row, from_=40, to=180, variable=self.gafete_name_size_var,
            command=lambda _: self._on_gafete_layout_change()
        )
        self.slider_indiv_nm_sz.pack(side="left", fill="x", expand=True, padx=6)
        ctk.CTkLabel(ts_slider_row, text="180%", font=ctk.CTkFont(size=10), text_color="gray60").pack(side="right")

        ts_presets_row = ctk.CTkFrame(text_size_box, fg_color="transparent")
        ts_presets_row.pack(fill="x", padx=6, pady=(2, 6))
        ctk.CTkButton(ts_presets_row, text="Chico 75%", width=75, height=22, font=ctk.CTkFont(size=10),
                      fg_color="#334155", hover_color="#1e293b",
                      command=lambda: self._set_name_size_preset(75)).pack(side="left", padx=1)
        ctk.CTkButton(ts_presets_row, text="Normal 100%", width=85, height=22, font=ctk.CTkFont(size=10),
                      fg_color="#2563eb", hover_color="#1d4ed8",
                      command=lambda: self._set_name_size_preset(100)).pack(side="left", padx=1)
        ctk.CTkButton(ts_presets_row, text="Grande 120%", width=85, height=22, font=ctk.CTkFont(size=10),
                      fg_color="#0d9488", hover_color="#0f766e",
                      command=lambda: self._set_name_size_preset(120)).pack(side="left", padx=1)
        ctk.CTkButton(ts_presets_row, text="Extra Grande 140%", width=110, height=22, font=ctk.CTkFont(size=10),
                      fg_color="#059669", hover_color="#047857",
                      command=lambda: self._set_name_size_preset(140)).pack(side="left", padx=1)

        # Fuente
        ctk.CTkLabel(self.gafete_adjust_frame, text="Fuente:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=5, column=0, padx=(8, 4), pady=(4, 2), sticky="w")
        self.combo_font_indiv = ctk.CTkOptionMenu(
            self.gafete_adjust_frame,
            values=[
                "Montserrat (Moderna y Limpia)",
                "Arial Black (Fuerte y Gruesa)",
                "Impact (Titular y Grande)",
                "Segoe UI (Corporativa y Nítida)",
                "Trebuchet MS (Geométrica)",
                "Georgia (Serif Formal y Elegante)",
                "Arial (Negrita Clásica)"
            ],
            variable=self.gafete_name_font_var,
            command=lambda _: self._on_gafete_layout_change(),
            height=26
        )
        self.combo_font_indiv.grid(row=5, column=1, columnspan=3, padx=(4, 8), pady=(4, 2), sticky="ew")

        # Separación de líneas y espaciado de letras
        self.lbl_gaf_line_sp = ctk.CTkLabel(self.gafete_adjust_frame, text=f"↕ Interlineado ({self.gafete_name_line_spacing_var.get():.0f}%):", font=ctk.CTkFont(size=11))
        self.lbl_gaf_line_sp.grid(row=6, column=0, padx=(8, 4), pady=(2, 6), sticky="w")
        ctk.CTkSlider(
            self.gafete_adjust_frame, from_=30, to=250, variable=self.gafete_name_line_spacing_var,
            command=lambda _: self._on_gafete_layout_change()
        ).grid(row=6, column=1, padx=4, pady=(2, 6), sticky="ew")

        self.lbl_gaf_trk = ctk.CTkLabel(self.gafete_adjust_frame, text=f"↔ Esp. Letras ({self.gafete_name_spacing_var.get():.0f}%):", font=ctk.CTkFont(size=11))
        self.lbl_gaf_trk.grid(row=6, column=2, padx=(8, 4), pady=(2, 6), sticky="w")
        ctk.CTkSlider(
            self.gafete_adjust_frame, from_=0, to=250, variable=self.gafete_name_spacing_var,
            command=lambda _: self._on_gafete_layout_change()
        ).grid(row=6, column=3, padx=(4, 8), pady=(2, 6), sticky="ew")

        # Color de módulos (Foreground)
        ctk.CTkLabel(f, text="Color QR:", font=ctk.CTkFont(size=12)).grid(row=10, column=0, sticky="w", pady=4)
        c_mod_frame = ctk.CTkFrame(f, fg_color="transparent")
        c_mod_frame.grid(row=10, column=1, sticky="ew", pady=4)

        self.btn_mod_color_sample = ctk.CTkButton(
            c_mod_frame, text="", width=28, height=28,
            fg_color=self.module_color_var.get(),
            hover_color=self.module_color_var.get(),
            command=lambda: self._choose_color("module")
        )
        self.btn_mod_color_sample.pack(side="left", padx=(0, 6))

        self.entry_mod_color = ctk.CTkEntry(c_mod_frame, textvariable=self.module_color_var, width=90)
        self.entry_mod_color.pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            c_mod_frame, text="Elegir", width=65, height=28,
            command=lambda: self._choose_color("module")
        ).pack(side="left")

        # Color de Fondo (Background)
        ctk.CTkLabel(f, text="Color Fondo:", font=ctk.CTkFont(size=12)).grid(row=11, column=0, sticky="w", pady=4)
        c_bg_frame = ctk.CTkFrame(f, fg_color="transparent")
        c_bg_frame.grid(row=11, column=1, sticky="ew", pady=4)

        self.btn_bg_color_sample = ctk.CTkButton(
            c_bg_frame, text="", width=28, height=28,
            fg_color=self.bg_color_var.get(),
            hover_color=self.bg_color_var.get(),
            command=lambda: self._choose_color("bg")
        )
        self.btn_bg_color_sample.pack(side="left", padx=(0, 6))

        self.entry_bg_color = ctk.CTkEntry(c_bg_frame, textvariable=self.bg_color_var, width=90)
        self.entry_bg_color.pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            c_bg_frame, text="Elegir", width=65, height=28,
            command=lambda: self._choose_color("bg")
        ).pack(side="left")

        # --- SECCIÓN 3: LOGO O ISOTIPO CENTRAL ---
        sec3 = ctk.CTkLabel(f, text="3. Logo o Insignia Central (Corrección H ~30%)", font=ctk.CTkFont(size=14, weight="bold"))
        sec3.grid(row=12, column=0, columnspan=2, sticky="w", pady=(12, 6))

        # Selector de tipo de logo
        logo_type_frame = ctk.CTkFrame(f, fg_color="transparent")
        logo_type_frame.grid(row=13, column=0, columnspan=2, pady=4, sticky="ew")

        ctk.CTkRadioButton(
            logo_type_frame, text="Insignia Barra (GEF Bermejo)",
            variable=self.logo_type_var, value="badge_bar",
            command=self._update_logo_ui
        ).pack(side="left", padx=(0, 6))

        ctk.CTkRadioButton(
            logo_type_frame, text="Imagen",
            variable=self.logo_type_var, value="image",
            command=self._update_logo_ui
        ).pack(side="left", padx=(0, 6))

        ctk.CTkRadioButton(
            logo_type_frame, text="Texto",
            variable=self.logo_type_var, value="text",
            command=self._update_logo_ui
        ).pack(side="left", padx=(0, 6))

        ctk.CTkRadioButton(
            logo_type_frame, text="Sin Logo",
            variable=self.logo_type_var, value="none",
            command=self._update_logo_ui
        ).pack(side="left")

        # Controles para Insignia con Barra Lateral (Estilo GEF Bermejo)
        self.badge_bar_controls = ctk.CTkFrame(f, fg_color=("gray90", "#27272a"), corner_radius=8)
        self.badge_bar_controls.grid(row=14, column=0, columnspan=2, pady=4, sticky="ew")
        self.badge_bar_controls.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(self.badge_bar_controls, text="Línea 1 (Arriba):").grid(row=0, column=0, padx=8, pady=(6, 2), sticky="w")
        self.entry_badge_line1 = ctk.CTkEntry(self.badge_bar_controls, textvariable=self.badge_line1_var)
        self.entry_badge_line1.grid(row=1, column=0, padx=8, pady=(0, 6), sticky="ew")

        ctk.CTkLabel(self.badge_bar_controls, text="Línea 2 (Negrita/Abajo):").grid(row=0, column=1, padx=8, pady=(6, 2), sticky="w")
        self.entry_badge_line2 = ctk.CTkEntry(self.badge_bar_controls, textvariable=self.badge_line2_var)
        self.entry_badge_line2.grid(row=1, column=1, padx=8, pady=(0, 6), sticky="ew")

        # Controles para Logo de Imagen
        self.logo_img_controls = ctk.CTkFrame(f, fg_color=("gray90", "#27272a"), corner_radius=8)
        self.logo_img_controls.grid_columnconfigure(0, weight=1)

        self.logo_path_label = ctk.CTkLabel(
            self.logo_img_controls,
            text="Ninguna imagen seleccionada",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        self.logo_path_label.grid(row=0, column=0, columnspan=2, padx=8, pady=(6, 2), sticky="w")

        btn_box = ctk.CTkFrame(self.logo_img_controls, fg_color="transparent")
        btn_box.grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 6), sticky="ew")

        ctk.CTkButton(
            btn_box, text="Cargar Imagen Logo...",
            command=self._choose_logo_file,
            height=28
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_box, text="Quitar", width=60, height=28,
            fg_color="gray50",
            command=self._clear_logo_file
        ).pack(side="left")

        # Controles para Isotipo de Texto Simple
        self.logo_text_controls = ctk.CTkFrame(f, fg_color=("gray90", "#27272a"), corner_radius=8)
        self.logo_text_controls.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.logo_text_controls, text="Texto central:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.entry_logo_text = ctk.CTkEntry(self.logo_text_controls, placeholder_text="Ej: ID, VIP, OTN")
        self.entry_logo_text.insert(0, "VIP")
        self.entry_logo_text.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        # Opciones de escala y marco protector
        slider_frame = ctk.CTkFrame(f, fg_color="transparent")
        slider_frame.grid(row=15, column=0, columnspan=2, pady=(8, 2), sticky="ew")
        slider_frame.grid_columnconfigure(1, weight=1)

        self.slider_label = ctk.CTkLabel(slider_frame, text="Tamaño insignia/logo: 18%", font=ctk.CTkFont(size=12))
        self.slider_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.logo_slider = ctk.CTkSlider(
            slider_frame,
            from_=0.12, to=0.22,
            number_of_steps=10,
            variable=self.logo_ratio_var,
            command=self._on_slider_change
        )
        self.logo_slider.set(0.18)
        self.logo_slider.grid(row=0, column=1, sticky="ew")

        self.switch_badge = ctk.CTkSwitch(
            f, text="Marco protector de alto contraste detrás del logo",
            variable=self.logo_badge_var
        )
        self.switch_badge.select()
        self.switch_badge.grid(row=16, column=0, columnspan=2, pady=(6, 12), sticky="w")

    def _build_batch_form(self):
        """Construye los controles para procesamiento masivo de datos mediante Excel/CSV."""
        b = self.batch_container

        ctk.CTkLabel(
            b,
            text="Generación Masiva de QRs para Eventos (Excel / CSV)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(6, 2))

        # Tarjeta informativa para eventos
        tip_frame = ctk.CTkFrame(b, fg_color=("gray90", "#27272a"), corner_radius=8)
        tip_frame.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(
            tip_frame,
            text="💡 Tip para tu Evento:\n"
                 "• El logo central y colores configurados en la app se aplicarán a todos los asistentes.\n"
                 "• Reconoce columnas: Nombre, Apellido, Correo, Teléfono, Cargo, Mesa, DNI, etc.",
            font=ctk.CTkFont(size=11),
            justify="left",
            text_color=("gray30", "gray80")
        ).pack(padx=10, pady=8, anchor="w")

        # 1. Archivo Fuente
        ctk.CTkLabel(b, text="1. Archivo Excel (.xlsx, .xls) o CSV de Asistentes:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        f_box = ctk.CTkFrame(b, fg_color="transparent")
        f_box.pack(fill="x", pady=(2, 6))

        self.batch_file_entry = ctk.CTkEntry(f_box, textvariable=self.batch_file_var, placeholder_text="Seleccione archivo de lista de personas...")
        self.batch_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(f_box, text="Cargar Excel/CSV", width=120, command=self._choose_batch_file).pack(side="left")

        # Info de detección del archivo cargado
        self.file_info_label = ctk.CTkLabel(
            b,
            text="Esperando selección de archivo...",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            justify="left"
        )
        self.file_info_label.pack(anchor="w", pady=(0, 10))

        # 2. Carpeta Destino
        ctk.CTkLabel(b, text="2. Carpeta donde guardar los QRs generados:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        d_box = ctk.CTkFrame(b, fg_color="transparent")
        d_box.pack(fill="x", pady=(2, 10))

        self.batch_out_entry = ctk.CTkEntry(d_box, textvariable=self.batch_output_var, placeholder_text="Carpeta de salida para las imágenes...")
        self.batch_out_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(d_box, text="Cambiar Carpeta...", width=120, command=self._choose_batch_output).pack(side="left")

        # 3. Opciones de exportación
        ctk.CTkLabel(b, text="3. Opciones de Codificación y Nombres:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(4, 2))

        opts_frame = ctk.CTkFrame(b, fg_color=("gray95", "#1f1f23"), corner_radius=8)
        opts_frame.pack(fill="x", pady=(2, 14))

        # Formato de datos
        fmt_row = ctk.CTkFrame(opts_frame, fg_color="transparent")
        fmt_row.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(fmt_row, text="Formato de datos:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 8))
        self.batch_fmt_var = ctk.StringVar(value="quick")
        ctk.CTkRadioButton(fmt_row, text="Credencial / Asistencia (Jala datos de Firebase en Escritorio y Web)", variable=self.batch_fmt_var, value="quick").pack(side="left", padx=6)
        ctk.CTkRadioButton(fmt_row, text="vCard (Tarjeta de Contacto)", variable=self.batch_fmt_var, value="vcard").pack(side="left", padx=6)
        ctk.CTkRadioButton(fmt_row, text="Texto Completo", variable=self.batch_fmt_var, value="plain").pack(side="left", padx=6)

        # Estilo de nombre de archivo
        name_row = ctk.CTkFrame(opts_frame, fg_color="transparent")
        name_row.pack(fill="x", padx=10, pady=(4, 6))
        ctk.CTkLabel(name_row, text="Nombres de archivo:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 8))
        self.filename_style_var = ctk.StringVar(value="numbered")
        ctk.CTkRadioButton(name_row, text="001_Nombre_Apellido.png (Ordenado)", variable=self.filename_style_var, value="numbered").pack(side="left", padx=6)
        ctk.CTkRadioButton(name_row, text="Nombre_Apellido.png", variable=self.filename_style_var, value="clean").pack(side="left", padx=6)

        # Opción de Gafete en Generación Masiva
        gaf_batch_row = ctk.CTkFrame(opts_frame, fg_color="transparent")
        gaf_batch_row.pack(fill="x", padx=10, pady=(4, 8))
        ctk.CTkSwitch(
            gaf_batch_row,
            text="🪪 Generar con Gafete (Usa la posición y tamaño ajustados en Vista Previa)",
            variable=self.gafete_enabled_var,
            command=self._generate_preview
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            gaf_batch_row, text="🪪 Elegir gafete...", height=26,
            command=self._choose_gafete_image
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            gaf_batch_row, text="🎯 Auto-ajustar", height=26,
            fg_color="#0ea5e9", hover_color="#0284c7",
            command=self._auto_detect_gafete_layout
        ).pack(side="left", padx=(0, 6))
        self.batch_gafete_label = ctk.CTkLabel(
            gaf_batch_row, text="(plantilla por defecto)",
            font=ctk.CTkFont(size=11), text_color="gray60"
        )
        self.batch_gafete_label.pack(side="left")

        # Configuración de Tipografía y Tamaño de Nombre para Lote Masivo
        typo_batch_box = ctk.CTkFrame(opts_frame, fg_color=("gray90", "#27272a"), corner_radius=8)
        typo_batch_box.pack(fill="x", padx=10, pady=(4, 10))

        tb_row1 = ctk.CTkFrame(typo_batch_box, fg_color="transparent")
        tb_row1.pack(fill="x", padx=10, pady=(6, 3))
        ctk.CTkLabel(tb_row1, text="🔤 Tipo de Letra (Fuente):", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 8))
        self.combo_font_batch = ctk.CTkOptionMenu(
            tb_row1,
            values=[
                "Montserrat (Moderna y Limpia)",
                "Arial Black (Fuerte y Gruesa)",
                "Impact (Titular y Grande)",
                "Segoe UI (Corporativa y Nítida)",
                "Trebuchet MS (Geométrica)",
                "Georgia (Serif Formal y Elegante)",
                "Arial (Negrita Clásica)"
            ],
            variable=self.gafete_name_font_var,
            command=lambda _: self._on_gafete_layout_change(),
            width=240,
            height=28
        )
        self.combo_font_batch.pack(side="left")

        tb_row2 = ctk.CTkFrame(typo_batch_box, fg_color="transparent")
        tb_row2.pack(fill="x", padx=10, pady=(3, 8))
        self.lbl_batch_nm_sz = ctk.CTkLabel(
            tb_row2,
            text=f"📏 Tamaño del Nombre ({self.gafete_name_size_var.get():.0f}%):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_batch_nm_sz.pack(side="left", padx=(0, 8))
        self.slider_batch_nm_sz = ctk.CTkSlider(
            tb_row2,
            from_=40, to=180,
            variable=self.gafete_name_size_var,
            command=lambda _: self._on_gafete_layout_change(),
            width=140
        )
        self.slider_batch_nm_sz.pack(side="left", padx=(0, 6))

        # Botones directos Achicar / Agrandar y Presets
        ctk.CTkButton(tb_row2, text="➖ Achicar", width=75, height=24, fg_color="#475569", hover_color="#334155",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=lambda: self._shrink_text_size(5.0)).pack(side="left", padx=2)
        ctk.CTkButton(tb_row2, text="➕ Agrandar", width=80, height=24, fg_color="#2563eb", hover_color="#1d4ed8",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=lambda: self._grow_text_size(5.0)).pack(side="left", padx=2)

        # Botones de ajuste rápido (Normal, Grande, Extra Grande)
        ctk.CTkButton(tb_row2, text="Chico 75%", width=75, height=24, fg_color="#334155", hover_color="#1e293b",
                      command=lambda: self._set_name_size_preset(75)).pack(side="left", padx=2)
        ctk.CTkButton(tb_row2, text="Normal 100%", width=85, height=24, fg_color="#0f766e", hover_color="#115e59",
                      command=lambda: self._set_name_size_preset(100)).pack(side="left", padx=2)
        ctk.CTkButton(tb_row2, text="Grande 120%", width=85, height=24, fg_color="#0d9488", hover_color="#0f766e",
                      command=lambda: self._set_name_size_preset(120)).pack(side="left", padx=2)
        ctk.CTkButton(tb_row2, text="Extra Grande 140%", width=110, height=24, fg_color="#059669", hover_color="#047857",
                      command=lambda: self._set_name_size_preset(140)).pack(side="left", padx=2)

        tb_row3 = ctk.CTkFrame(typo_batch_box, fg_color="transparent")
        tb_row3.pack(fill="x", padx=10, pady=(0, 8))

        self.lbl_batch_line_sp = ctk.CTkLabel(
            tb_row3,
            text=f"↕ Separación Líneas ({self.gafete_name_line_spacing_var.get():.0f}%):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_batch_line_sp.pack(side="left", padx=(0, 6))
        ctk.CTkSlider(
            tb_row3,
            from_=30, to=250,
            variable=self.gafete_name_line_spacing_var,
            command=lambda _: self._on_gafete_layout_change(),
            width=120
        ).pack(side="left", padx=(0, 10))

        self.lbl_batch_trk = ctk.CTkLabel(
            tb_row3,
            text=f"↔ Espacio Letras ({self.gafete_name_spacing_var.get():.0f}%):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_batch_trk.pack(side="left", padx=(0, 6))
        ctk.CTkSlider(
            tb_row3,
            from_=0, to=250,
            variable=self.gafete_name_spacing_var,
            command=lambda _: self._on_gafete_layout_change(),
            width=120
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            tb_row3, text="↺ 100%", width=55, height=24, fg_color="#475569", hover_color="#334155",
            font=ctk.CTkFont(size=11),
            command=self._reset_typography_spacing
        ).pack(side="left", padx=2)

        # Botón de Procesar Lote
        self.btn_run_batch = ctk.CTkButton(
            b,
            text="⚡ Generar Todos los Códigos QR de la Lista",
            command=self._start_batch_thread,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_run_batch.pack(fill="x", pady=(6, 10))

        # Progreso
        self.batch_progress = ctk.CTkProgressBar(b)
        self.batch_progress.set(0)
        self.batch_progress.pack(fill="x", pady=(0, 6))

        self.batch_status_lbl = ctk.CTkLabel(b, text="Listo para procesar.", font=ctk.CTkFont(size=12), text_color="gray60")
        self.batch_status_lbl.pack(anchor="w")

        # Botón para abrir la carpeta directamente al terminar
        self.btn_open_folder = ctk.CTkButton(
            b,
            text="📂 Abrir Carpeta con los QRs Generados",
            command=self._open_output_folder,
            fg_color="#10b981",
            hover_color="#059669",
            height=36,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.btn_open_folder.pack(fill="x", pady=(10, 6))
        self.btn_open_folder.configure(state="disabled")

    def _on_mode_change(self, value):
        """Alterna entre la vista individual y la vista por lote."""
        if value == "Datos Individuales":
            self.batch_container.grid_remove()
            self.individual_container.grid()
        else:
            self.individual_container.grid_remove()
            self.batch_container.grid(row=1, column=0, padx=14, pady=(0, 14), sticky="nsew")

    def _on_style_selected(self, choice):
        """Mapea el texto seleccionado al identificador de estilo de módulo."""
        mapping = {
            "Cuadrado clásico (100% Compatible iPhone y Android)": "square",
            "Cuadrado clásico": "square",
            "Puntos / Dots (Estilo GEF Bermejo)": "dots",
            "Círculos completos": "circle",
            "Cuadrados redondeados": "rounded",
            "Barras horizontales": "horizontal_bars",
            "Barras verticales": "vertical_bars",
            "Rombos / Diamantes": "diamond",
            "Estrellas 4 puntas": "star"
        }
        self.module_style_var.set(mapping.get(choice, "square"))
        self._generate_preview()

    def _on_eye_frame_selected(self, choice):
        """Mapea la selección del marco del ojo."""
        mapping = {
            "Cuadrado clásico": "square",
            "Cuadrado redondeado": "rounded",
            "Estilo Hoja (Leaf)": "leaf",
            "Círculo concéntrico": "circle",
            "Marco punteado / Bolitas": "dots"
        }
        self.eye_frame_style_var.set(mapping.get(choice, "square"))
        self._generate_preview()

    def _on_eye_ball_selected(self, choice):
        """Mapea la selección del centro del ojo."""
        mapping = {
            "Cuadrado clásico": "square",
            "Círculo sólido": "circle",
            "Cuadrado redondeado": "rounded",
            "Estilo Hoja (Leaf)": "leaf",
            "Matriz 3x3 puntos": "dots_3x3",
            "3 Barras verticales": "bars_v",
            "3 Barras horizontales": "bars_h",
            "Huella 🐾": "paw",
            "Imagen personalizada...": "image"
        }
        if choice == "Imagen personalizada...":
            path = filedialog.askopenfilename(
                title="Imagen para el centro del ojo",
                filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"), ("Todos", "*.*")]
            )
            if not path:
                self.eye_ball_menu.set("Cuadrado clásico")
                choice = "Cuadrado clásico"
            else:
                self.eye_image_path_var.set(path)
        self.eye_ball_style_var.set(mapping.get(choice, "square"))
        self._generate_preview()

    def _choose_color(self, target: str):
        """Abre el diálogo de paleta de colores y actualiza la muestra gráfica."""
        initial = self.module_color_var.get() if target == "module" else self.bg_color_var.get()
        _, hex_code = colorchooser.askcolor(color=initial, title="Seleccione un color")
        if hex_code:
            hex_code = hex_code.upper()
            if target == "module":
                self.module_color_var.set(hex_code)
                self.btn_mod_color_sample.configure(fg_color=hex_code, hover_color=hex_code)
            else:
                self.bg_color_var.set(hex_code)
                self.btn_bg_color_sample.configure(fg_color=hex_code, hover_color=hex_code)
            self._generate_preview()

    def _update_logo_ui(self):
        """Muestra u oculta los controles específicos según el tipo de logo central seleccionado."""
        mode = self.logo_type_var.get()
        # Ocultar todos primero
        self.badge_bar_controls.grid_remove()
        self.logo_img_controls.grid_remove()
        self.logo_text_controls.grid_remove()

        if mode == "badge_bar":
            self.badge_bar_controls.grid(row=14, column=0, columnspan=2, pady=4, sticky="ew")
        elif mode == "image":
            self.logo_img_controls.grid(row=14, column=0, columnspan=2, pady=4, sticky="ew")
        elif mode == "text":
            self.logo_text_controls.grid(row=14, column=0, columnspan=2, pady=4, sticky="ew")

        self._generate_preview()

    def _choose_logo_file(self):
        """Abre el explorador de archivos para elegir una imagen de logotipo."""
        path = filedialog.askopenfilename(
            title="Seleccionar Imagen de Logotipo",
            filetypes=[
                ("Imágenes", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"),
                ("Todos los archivos", "*.*")
            ]
        )
        if path:
            self.logo_path_var.set(path)
            basename = os.path.basename(path)
            self.logo_path_label.configure(text=f"Logo: {basename}", text_color="white")
            self._generate_preview()

    def _clear_logo_file(self):
        """Limpia el archivo de logotipo seleccionado."""
        self.logo_path_var.set("")
        self.logo_path_label.configure(text="Ninguna imagen seleccionada", text_color="gray60")
        self._generate_preview()

    def _choose_bg_image(self):
        """Selecciona la imagen que se dibujará grande detrás de los puntos."""
        path = filedialog.askopenfilename(
            title="Seleccionar imagen de fondo",
            filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"), ("Todos", "*.*")]
        )
        if path:
            self.bg_image_path_var.set(path)
            self.bg_image_label.configure(text=os.path.basename(path))
            self.jaguar_bg_var.set(True)
            self._generate_preview()

    def _choose_gafete_image(self):
        """Selecciona la plantilla de gafete y auto-detecta la posición de sus recuadros."""
        path = filedialog.askopenfilename(
            title="Seleccionar imagen de plantilla de Gafete",
            filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"), ("Todos", "*.*")]
        )
        if path:
            self.gafete_path_var.set(path)
            fname = os.path.basename(path)
            self.gafete_image_label.configure(text=fname, text_color="#10b981")
            if hasattr(self, "batch_gafete_label"):
                self.batch_gafete_label.configure(text=fname, text_color="#10b981")
            self.gafete_enabled_var.set(True)
            self._auto_detect_gafete_layout()

    def _auto_detect_gafete_layout(self):
        """Detecta automáticamente los recuadros de la plantilla de gafete actual y ajusta posición/tamaño."""
        layout = detect_gafete_layout(self.gafete_path_var.get() or None)
        self.gafete_qr_x_var.set(layout["qr_x"])
        self.gafete_qr_y_var.set(layout["qr_y"])
        self.gafete_qr_size_var.set(layout["qr_size"])
        self.gafete_name_x_var.set(layout["name_x"])
        self.gafete_name_y_var.set(layout["name_y"])
        self.gafete_name_size_var.set(layout["name_size"])
        self._update_gafete_labels()
        self.gafete_enabled_var.set(True)
        self._generate_preview()

    def _shrink_text_size(self, delta: float = 5.0):
        """Disminuye el tamaño del texto del nombre en el gafete."""
        val = max(40.0, round(self.gafete_name_size_var.get() - delta, 1))
        self.gafete_name_size_var.set(val)
        self._on_gafete_layout_change()

    def _grow_text_size(self, delta: float = 5.0):
        """Aumenta el tamaño del texto del nombre en el gafete."""
        val = min(180.0, round(self.gafete_name_size_var.get() + delta, 1))
        self.gafete_name_size_var.set(val)
        self._on_gafete_layout_change()

    def _set_name_size_preset(self, val: float):
        """Ajusta un tamaño predefinido para el nombre en el gafete."""
        self.gafete_name_size_var.set(val)
        self._on_gafete_layout_change()

    def _reset_typography_spacing(self):
        """Restablece la separación vertical y el espaciado entre letras al 100% estándar."""
        self.gafete_name_spacing_var.set(100.0)
        self.gafete_name_line_spacing_var.set(100.0)
        self._on_gafete_layout_change()

    def _update_gafete_labels(self):
        """Actualiza los textos de porcentaje de los controles de Gafete."""
        if hasattr(self, "lbl_gaf_qr_x"):
            self.lbl_gaf_qr_x.configure(text=f"QR Pos X ({self.gafete_qr_x_var.get():.0f}%):")
            self.lbl_gaf_qr_y.configure(text=f"QR Pos Y ({self.gafete_qr_y_var.get():.0f}%):")
            self.lbl_gaf_qr_sz.configure(text=f"Tamaño QR ({self.gafete_qr_size_var.get():.0f}%):")
            self.lbl_gaf_nm_x.configure(text=f"Nombre X ({self.gafete_name_x_var.get():.0f}%):")
            self.lbl_gaf_nm_y.configure(text=f"Nombre Y ({self.gafete_name_y_var.get():.0f}%):")
            self.lbl_gaf_nm_sz.configure(text=f"🔤 Tamaño del Texto: {self.gafete_name_size_var.get():.0f}%")
        if hasattr(self, "lbl_quick_nm_sz"):
            self.lbl_quick_nm_sz.configure(text=f"{self.gafete_name_size_var.get():.0f}%")
        if hasattr(self, "lbl_gaf_line_sp"):
            self.lbl_gaf_line_sp.configure(text=f"↕ Interlineado ({self.gafete_name_line_spacing_var.get():.0f}%):")
        if hasattr(self, "lbl_gaf_trk"):
            self.lbl_gaf_trk.configure(text=f"↔ Esp. Letras ({self.gafete_name_spacing_var.get():.0f}%):")
        if hasattr(self, "lbl_batch_nm_sz"):
            self.lbl_batch_nm_sz.configure(text=f"📏 Tamaño del Nombre ({self.gafete_name_size_var.get():.0f}%):")
        if hasattr(self, "lbl_batch_line_sp"):
            self.lbl_batch_line_sp.configure(text=f"↕ Separación Líneas ({self.gafete_name_line_spacing_var.get():.0f}%):")
        if hasattr(self, "lbl_batch_trk"):
            self.lbl_batch_trk.configure(text=f"↔ Espacio Letras ({self.gafete_name_spacing_var.get():.0f}%):")

    def _on_gafete_layout_change(self):
        """Callback al mover cualquier slider de posición o tamaño del Gafete."""
        self._update_gafete_labels()
        if not self.gafete_enabled_var.get():
            self.gafete_enabled_var.set(True)
        self._generate_preview()

    def _on_preview_press(self, event):
        """Selecciona el elemento más cercano (QR o Nombre) al hacer clic sobre el Gafete en la Vista Previa."""
        if not self.gafete_enabled_var.get():
            return
        pw, ph = self._preview_rendered_size
        if pw <= 0 or ph <= 0:
            return
        click_x = max(0.0, min(100.0, (event.x / pw) * 100.0))
        click_y = max(0.0, min(100.0, (event.y / ph) * 100.0))
        dist_qr = ((click_x - self.gafete_qr_x_var.get()) ** 2 + (click_y - self.gafete_qr_y_var.get()) ** 2) ** 0.5
        dist_nm = ((click_x - self.gafete_name_x_var.get()) ** 2 + (click_y - self.gafete_name_y_var.get()) ** 2) ** 0.5
        self._preview_drag_target = "qr" if dist_qr <= dist_nm else "name"
        self._on_preview_drag(event)

    def _on_preview_drag(self, event):
        """Mueve en vivo el QR o el Nombre al arrastrar el mouse sobre la Vista Previa."""
        if not self.gafete_enabled_var.get() or not self._preview_drag_target:
            return
        pw, ph = self._preview_rendered_size
        if pw <= 0 or ph <= 0:
            return
        rel_x = round(max(8.0, min(92.0, (event.x / pw) * 100.0)), 1)
        rel_y = round(max(5.0, min(95.0, (event.y / ph) * 100.0)), 1)
        if self._preview_drag_target == "qr":
            self.gafete_qr_x_var.set(rel_x)
            self.gafete_qr_y_var.set(rel_y)
        else:
            self.gafete_name_x_var.set(rel_x)
            self.gafete_name_y_var.set(rel_y)
        self._update_gafete_labels()
        self._generate_preview()

    def _on_preview_wheel(self, event):
        """Cambia el tamaño del QR o del Nombre usando la rueda del mouse sobre la Vista Previa."""
        if not self.gafete_enabled_var.get():
            return
        pw, ph = self._preview_rendered_size
        if pw <= 0 or ph <= 0:
            return
        cur_x = (event.x / pw) * 100.0
        cur_y = (event.y / ph) * 100.0
        dist_qr = ((cur_x - self.gafete_qr_x_var.get()) ** 2 + (cur_y - self.gafete_qr_y_var.get()) ** 2) ** 0.5
        dist_nm = ((cur_x - self.gafete_name_x_var.get()) ** 2 + (cur_y - self.gafete_name_y_var.get()) ** 2) ** 0.5
        delta = 1.5 if event.delta > 0 else -1.5
        if dist_qr <= dist_nm:
            new_sz = round(max(15.0, min(75.0, self.gafete_qr_size_var.get() + delta)), 1)
            self.gafete_qr_size_var.set(new_sz)
        else:
            new_sz = round(max(40.0, min(180.0, self.gafete_name_size_var.get() + delta * 3.0)), 1)
            self.gafete_name_size_var.set(new_sz)
        self._update_gafete_labels()
        self._generate_preview()

    def _on_slider_change(self, value):
        """Actualiza el label del porcentaje de tamaño del logo."""
        pct = int(value * 100)
        self.slider_label.configure(text=f"Tamaño insignia/logo: {pct}%")
        self._generate_preview()

    def _get_current_qr_options(self) -> dict:
        """Recolecta todas las configuraciones visuales del QR y de la plantilla de Gafete."""
        return {
            "module_color": self.module_color_var.get(),
            "bg_color": self.bg_color_var.get(),
            "module_style": self.module_style_var.get(),
            "eye_frame_style": self.eye_frame_style_var.get(),
            "eye_ball_style": self.eye_ball_style_var.get(),
            "logo_type": self.logo_type_var.get(),
            "badge_line1": self.badge_line1_var.get().strip(),
            "badge_line2": self.badge_line2_var.get().strip(),
            "logo_path": self.logo_path_var.get(),
            "logo_text": self.entry_logo_text.get().strip() if hasattr(self, "entry_logo_text") else "",
            "logo_ratio": self.logo_ratio_var.get(),
            "logo_badge": self.logo_badge_var.get(),
            "box_size": 16,
            "border": 4,
            "jaguar_background": self.jaguar_bg_var.get(),
            "jaguar_image_path": self.bg_image_path_var.get() or None,
            "eye_ball_image": self.eye_image_path_var.get() or None,
            "use_gafete": self.gafete_enabled_var.get(),
            "gafete_path": self.gafete_path_var.get() or None,
            "gafete_qr_x": self.gafete_qr_x_var.get(),
            "gafete_qr_y": self.gafete_qr_y_var.get(),
            "gafete_qr_size": self.gafete_qr_size_var.get(),
            "gafete_name_x": self.gafete_name_x_var.get(),
            "gafete_name_y": self.gafete_name_y_var.get(),
            "gafete_name_size": self.gafete_name_size_var.get(),
            "gafete_name_font": self.gafete_name_font_var.get(),
            "gafete_name_spacing": self.gafete_name_spacing_var.get(),
            "gafete_name_line_spacing": self.gafete_name_line_spacing_var.get(),
        }

    def _generate_preview(self):
        """Genera el QR actual con los datos del formulario y actualiza la vista previa."""
        try:
            data = {
                "first_name": self.entry_first_name.get().strip(),
                "last_name": self.entry_last_name.get().strip(),
                "org": self.entry_org.get().strip(),
                "title": self.entry_title.get().strip(),
                "email": self.entry_email.get().strip(),
                "phone": self.entry_phone.get().strip(),
                "notes": self.entry_notes.get().strip()
            }

            content = format_contact_data(data, format_type=self.format_type_var.get())
            options = self._get_current_qr_options()
            use_gafete = bool(options.pop("use_gafete", False))
            gafete_path = options.pop("gafete_path", None)
            gafete_qr_x = options.pop("gafete_qr_x", None)
            gafete_qr_y = options.pop("gafete_qr_y", None)
            gafete_qr_size = options.pop("gafete_qr_size", None)
            gafete_name_x = options.pop("gafete_name_x", None)
            gafete_name_y = options.pop("gafete_name_y", None)
            gafete_name_size = options.pop("gafete_name_size", None)
            gafete_name_font = options.pop("gafete_name_font", None)
            gafete_name_spacing = options.pop("gafete_name_spacing", None)
            gafete_name_line_spacing = options.pop("gafete_name_line_spacing", None)

            # Reutilizar QR base en caché si solo se está moviendo/redimensionando en el Gafete
            cache_key = (content, tuple(sorted(options.items())))
            if self._cached_base_qr_key == cache_key and self._cached_base_qr_img is not None:
                qr_img = self._cached_base_qr_img.copy()
            else:
                qr_img = generate_qr(content=content, **options)
                self._cached_base_qr_key = cache_key
                self._cached_base_qr_img = qr_img.copy()

            full_name = f"{data['first_name']} {data['last_name']}".strip()
            if use_gafete:
                qr_img = compose_gafete_image(
                    qr_img,
                    full_name=full_name,
                    gafete_path=gafete_path,
                    text_color=hex_to_rgb(options.get("module_color", "#000000")),
                    qr_x=gafete_qr_x,
                    qr_y=gafete_qr_y,
                    qr_size=gafete_qr_size,
                    name_x=gafete_name_x,
                    name_y=gafete_name_y,
                    name_size=gafete_name_size,
                    font_family=gafete_name_font,
                    name_spacing=gafete_name_spacing,
                    name_line_spacing=gafete_name_line_spacing
                )
            elif full_name:
                qr_img = add_name_label_below_qr(
                    qr_img,
                    full_name=full_name,
                    bg_color=hex_to_rgb(options.get("bg_color", "#FFFFFF")),
                    text_color=hex_to_rgb(options.get("module_color", "#000000")),
                    font_family=gafete_name_font,
                    name_size=gafete_name_size,
                    name_spacing=gafete_name_spacing,
                    name_line_spacing=gafete_name_line_spacing
                )
            self.current_qr_img = qr_img

            # Redimensionar para la vista previa en el Canvas (tamaño ampliado para fácil lectura con celular)
            display_size = (460, 500)
            img_copy = self.current_qr_img.copy()
            img_copy.thumbnail(display_size, Image.Resampling.LANCZOS)
            self._preview_rendered_size = img_copy.size

            # Usar CTkImage para compatibilidad con soporte HiDPI / Dark / Light
            ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=img_copy.size)
            self.preview_label.configure(image=ctk_img, text="")
            self.preview_label.image = ctk_img

            w, h = self.current_qr_img.size
            self.status_label.configure(
                text=f"Resolución original: {w}x{h} px | Redundancia: Alta (H 30%) | Formato: {self.format_type_var.get().upper()}"
            )
        except Exception as e:
            messagebox.showerror("Error al generar vista previa", f"Ocurrió un error:\n{str(e)}")

    def _save_qr_image(self):
        """Guarda la imagen generada en el disco en alta resolución."""
        if self.current_qr_img is None:
            messagebox.showwarning("Atención", "Genere primero una vista previa del código QR.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Guardar Código QR",
            defaultextension=".png",
            filetypes=[
                ("Imagen PNG (*.png)", "*.png"),
                ("Imagen JPEG (*.jpg)", "*.jpg"),
                ("Imagen BMP (*.bmp)", "*.bmp")
            ]
        )
        if file_path:
            try:
                ext = os.path.splitext(file_path)[1].lower()
                save_img = self.current_qr_img
                if ext in [".jpg", ".jpeg"]:
                    save_img = save_img.convert("RGB")
                    save_img.save(file_path, "JPEG", quality=95)
                else:
                    save_img.save(file_path)
                messagebox.showinfo("Éxito", f"Código QR guardado correctamente en:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error al guardar", f"No se pudo guardar el archivo:\n{str(e)}")

    # ==========================================
    # MANEJO DE GENERACIÓN POR LOTE
    # ==========================================
    def _choose_batch_file(self):
        """Selecciona el archivo Excel o CSV para procesamiento masivo e inspecciona sus datos."""
        path = filedialog.askopenfilename(
            title="Seleccionar archivo con lista de participantes",
            filetypes=[
                ("Hojas de cálculo y datos", "*.xlsx;*.xls;*.csv"),
                ("Excel (*.xlsx, *.xls)", "*.xlsx;*.xls"),
                ("CSV delimitado por comas (*.csv)", "*.csv")
            ]
        )
        if path:
            self.batch_file_var.set(path)
            try:
                info = inspect_batch_file(path)
                col_preview = ", ".join(info["columns"][:6])
                if len(info["columns"]) > 6:
                    col_preview += f"... (+{len(info['columns']) - 6} más)"

                self.file_info_label.configure(
                    text=f"✅ {info['filename']}\n👥 {info['total_rows']} participantes detectados.\n📋 Columnas: {col_preview}",
                    text_color="#10b981"
                )

                # Sugerir automáticamente una carpeta de salida junto al archivo
                if not self.batch_output_var.get().strip():
                    parent = os.path.dirname(path)
                    base = os.path.splitext(info["filename"])[0]
                    auto_dir = os.path.join(parent, f"QRs_{base}")
                    self.batch_output_var.set(auto_dir)

            except Exception as ex:
                self.file_info_label.configure(
                    text=f"⚠️ No se pudo leer el archivo: {str(ex)}",
                    text_color="#ef4444"
                )

    def _choose_batch_output(self):
        """Selecciona el directorio donde se exportarán los archivos."""
        directory = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if directory:
            self.batch_output_var.set(directory)

    def _open_output_folder(self):
        """Abre la carpeta de salida en el explorador de Windows."""
        out_dir = self.batch_output_var.get().strip()
        if out_dir and os.path.exists(out_dir):
            try:
                os.startfile(out_dir)
            except Exception:
                try:
                    import subprocess
                    subprocess.Popen(["explorer", os.path.normpath(out_dir)])
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo abrir la carpeta: {e}")
        else:
            messagebox.showwarning("Carpeta no encontrada", "La carpeta aún no ha sido creada o no existe.")

    def _start_batch_thread(self):
        """Inicia el proceso por lote en un hilo separado para mantener la UI responsiva."""
        file_path = self.batch_file_var.get().strip()
        out_dir = self.batch_output_var.get().strip()

        if not file_path or not os.path.isfile(file_path):
            messagebox.showwarning("Falta archivo", "Por favor seleccione un archivo Excel o CSV válido con la lista de participantes.")
            return

        if not out_dir:
            messagebox.showwarning("Falta carpeta", "Por favor seleccione una carpeta de destino para guardar los QRs.")
            return

        self.btn_run_batch.configure(state="disabled", text="⏳ Generando QRs...")
        self.btn_open_folder.configure(state="disabled")
        self.batch_progress.set(0)
        self.batch_status_lbl.configure(text="Iniciando procesamiento masivo...", text_color="white")

        thread = threading.Thread(
            target=self._run_batch_worker,
            args=(file_path, out_dir, self.filename_style_var.get()),
            daemon=True
        )
        thread.start()

    def _run_batch_worker(self, file_path: str, out_dir: str, filename_style: str):
        """Worker en segundo plano para procesar la lista de personas."""
        try:
            options = self._get_current_qr_options()
            fmt_type = self.batch_fmt_var.get()

            def on_progress(current, total, msg):
                fraction = current / max(1, total)
                self.after(0, lambda: self._update_batch_progress(fraction, f"[{current}/{total}] {msg}"))

            result = process_batch(
                file_path=file_path,
                output_dir=out_dir,
                format_type=fmt_type,
                qr_options=options,
                filename_style=filename_style,
                progress_callback=on_progress
            )

            self.after(0, lambda: self._batch_completed(result, out_dir))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error en proceso masivo", str(e)))
            self.after(0, lambda: self._reset_batch_ui())

    def _update_batch_progress(self, fraction: float, text: str):
        self.batch_progress.set(fraction)
        self.batch_status_lbl.configure(text=text)

    def _batch_completed(self, result: dict, out_dir: str):
        self._reset_batch_ui()
        self.btn_open_folder.configure(state="normal")
        self.batch_status_lbl.configure(text=f"¡Listo! Se generaron {result['success']} códigos QR.", text_color="#10b981")

        msg = (
            f"¡Generación masiva completada con éxito!\n\n"
            f"• Total en la lista: {result['total']}\n"
            f"• QRs generados: {result['success']}\n"
            f"• Errores: {result['failed']}\n\n"
            f"¿Deseas abrir la carpeta con las imágenes generadas ahora?"
        )
        if messagebox.askyesno("Éxito en el Proceso", msg):
            self._open_output_folder()

    def _reset_batch_ui(self):
        self.btn_run_batch.configure(state="normal", text="⚡ Generar Todos los Códigos QR de la Lista")


if __name__ == "__main__":
    app = QRGeneratorApp()
    app.mainloop()

