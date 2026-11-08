"""
Módulo de lógica para la generación de Códigos QR personalizados.
Soporta texto plano estructurado (formato recomendado) y vCard,
inserción de logos/isotipos centrales, estilos de módulos visuales
y procesamiento por lote (Excel/CSV).
"""

import os
import re
import csv
from typing import Dict, Any, Optional, Tuple, Callable
from PIL import Image, ImageDraw, ImageFont, ImageOps
import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_Q, ERROR_CORRECT_M
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import (
    SquareModuleDrawer,
    CircleModuleDrawer,
    RoundedModuleDrawer,
    GappedSquareModuleDrawer
)
from qrcode.image.styles.colormasks import SolidFillColorMask


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convierte un color en formato hexadecimal '#RRGGBB' a una tupla (R, G, B)."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    if len(hex_color) != 6:
        return (0, 0, 0)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def format_contact_data(data: Dict[str, str], format_type: str = "plain") -> str:
    """
    Formatea los datos personales para su inclusión en el QR.

    Formatos soportados:
    - 'plain': Texto plano estructurado y legible (PREDETERMINADO Y RECOMENDADO).
               Al escanear con la cámara del celular, se despliega inmediatamente
               toda la información de la persona en pantalla.
    - 'vcard': Estándar vCard 3.0 para importación en la libreta de contactos.
    """
    first_name = data.get("first_name", "").strip()
    last_name  = data.get("last_name",  "").strip()
    org        = data.get("org",        "").strip()
    title      = data.get("title",      "").strip()
    email      = data.get("email",      "").strip()
    phone      = data.get("phone",      "").strip()
    location   = data.get("location",   "").strip()
    notes      = data.get("notes",      "").strip()

    full_name = f"{first_name} {last_name}".strip()

    # Extraer ID numérico si está presente en notas o en el diccionario
    num_str = re.search(r"\d+", notes) if notes else None
    id_val = num_str.group(0) if num_str else str(data.get("numero") or data.get("num") or data.get("id") or "").strip()

    if format_type.lower() in ("url", "enlace", "link", "web"):
        # Formato de enlace web directo: el estándar universal para eventos.
        # Al apuntar con la cámara normal de iPhone, iOS muestra de inmediato el botón amarillo de Safari.
        # Al apuntar con Android, abre el navegador al instante.
        # Al apuntar con el escáner del sistema (celular.html / index.html), detecta el ID en milisegundos.
        base_url = "https://simaotnpb-boop.github.io/Proyecto-gefBermejo/celular.html"
        return f"{base_url}?id={id_val}" if id_val else base_url

    if format_type.lower() == "vcard":
        if first_name and not last_name and " " in first_name:
            parts_n = first_name.split()
            vcard_fn = " ".join(parts_n[:-1]) if len(parts_n) > 1 else first_name
            vcard_ln = parts_n[-1] if len(parts_n) > 1 else ""
        else:
            vcard_fn = first_name
            vcard_ln = last_name

        lines = [
            "BEGIN:VCARD",
            "VERSION:3.0"
        ]
        lines.append(f"N:{vcard_ln};{vcard_fn};;;")
        lines.append(f"FN:{full_name if full_name else 'Contacto'}")
        if org:
            lines.append(f"ORG:{org}")
        if title:
            lines.append(f"TITLE:{title}")
        if phone:
            clean_phone = re.sub(r"[^\d+ -]", "", phone)
            lines.append(f"TEL;TYPE=CELL,VOICE:{clean_phone}")
        else:
            # En iPhone, si una vCard no tiene ni teléfono ni URL, la cámara de iOS
            # muestra "No se encontraron datos utilizables". Añadimos el canal oficial del evento:
            lines.append("TEL;TYPE=WORK,VOICE:+591 4 6644040")
        if email:
            lines.append(f"EMAIL;TYPE=PREF,INTERNET:{email}")
        else:
            lines.append("EMAIL;TYPE=WORK,INTERNET:contacto@otnpb.gob.bo")
        if location:
            lines.append(f"ADR:;;{location};;;;")
        if notes:
            clean_notes = notes.replace("\r\n", " - ").replace("\n", " - ")
            lines.append(f"NOTE:{clean_notes}")
        # Enlace oficial al sistema de asistencia para compatibilidad total con Safari en iPhone
        base_url = "https://simaotnpb-boop.github.io/Proyecto-gefBermejo/celular.html"
        lines.append(f"URL:{base_url}?id={id_val}" if id_val else f"URL:{base_url}")
        lines.append("END:VCARD")
        return "\r\n".join(lines)

    elif format_type.lower() in ("quick", "asistencia", "rapido", "credencial"):
        # Formato optimizado para credenciales y control de asistencia:
        # Genera un QR de baja densidad (módulos 2x más grandes) que cualquier celular
        # (iPhone o Android antiguo/económico) lee en milisegundos desde cualquier distancia.
        parts = []
        if full_name:
            parts.append(f"Nombre: {full_name}")
        if org:
            clean_org = org if len(org) <= 55 else org[:52] + "..."
            parts.append(f"Institución: {clean_org}")
        if notes:
            parts.append(f"Notas: {notes}")
        return "\n".join(parts) if parts else "Sin información"

    else:  # 'plain' — texto completo estructurado
        parts = []
        if full_name:
            parts.append(f"Nombre: {full_name}")
        if org:
            parts.append(f"Institución: {org}")
        if title:
            parts.append(f"Cargo: {title}")
        if email:
            parts.append(f"Correo: {email}")
        if phone:
            parts.append(f"Teléfono: {phone}")
        if location:
            parts.append(f"Lugar o Sede: {location}")
        if notes:
            parts.append(f"Notas: {notes}")

        return "\n".join(parts) if parts else "Sin información"


def _get_module_drawer(drawer_type: str):
    """Retorna la clase de dibujo de módulos según la selección."""
    drawers = {
        "square":  SquareModuleDrawer(),
        "rounded": RoundedModuleDrawer(),
        "circle":  CircleModuleDrawer(),
        "gapped":  GappedSquareModuleDrawer(),
    }
    return drawers.get(drawer_type.lower(), SquareModuleDrawer())


def _get_alignment_centers(n: int) -> list:
    """
    Devuelve las coordenadas (fila/columna) de los centros de los patrones
    de alineación 5x5 según el tamaño de matriz QR (ISO/IEC 18004).
    """
    version = (n - 17) // 4
    if version < 2:
        return []
    try:
        from qrcode.util import pattern_position
        pos = pattern_position(version)
        if pos:
            return list(pos)
    except Exception:
        pass
    num_ap = version // 7 + 2
    first = 6
    last = n - 7
    if num_ap == 2:
        return [first, last]
    step = (last - first) / (num_ap - 1)
    # Redondeo par hacia abajo según estándar QR
    step = int((last - first + num_ap - 2) // (num_ap - 1))
    if step % 2 == 1:
        step += 1
    coords = [first]
    for i in range(num_ap - 2, 0, -1):
        coords.append(last - i * step)
    coords.append(last)
    return coords


def _is_alignment_module(r: int, c: int, n: int, centers: list) -> bool:
    """Retorna True si (r, c) pertenece a un patrón de alineación 5x5 válido."""
    for ar in centers:
        for ac in centers:
            # Omitir si se solapa con alguno de los 3 ojos buscadores
            if (ar < 8 and ac < 8) or (ar < 8 and ac >= n - 8) or (ar >= n - 8 and ac < 8):
                continue
            if abs(r - ar) <= 2 and abs(c - ac) <= 2:
                return True
    return False


def _is_functional_module(r: int, c: int, n: int, centers: list) -> bool:
    """
    Retorna True si el módulo (r, c) es estructural para el lector óptico:
    - Líneas de sincronización (timing patterns: r == 6 o c == 6)
    - Patrones de alineación 5x5 (indispensables en QRs densos / generación masiva)
    - Información de formato (fila/columna 8 junto a los 3 ojos)
    - Información de versión (bloques 3x6 en versión >= 7, es decir n >= 45)
    """
    if r == 6 or c == 6:
        return True
    if (r == 8 and (c <= 8 or c >= n - 8)) or (c == 8 and (r <= 8 or r >= n - 8)):
        return True
    if n >= 45:
        if (r < 6 and n - 11 <= c < n - 8) or (c < 6 and n - 11 <= r < n - 8):
            return True
    if centers and _is_alignment_module(r, c, n, centers):
        return True
    return False


def _load_font(font_candidates: list, size: int) -> ImageFont.FreeTypeFont:
    """
    Carga la primera fuente disponible de la lista de candidatos (buscando también
    en C:\\Windows\\Fonts) para lograr una tipografía moderna y elegante.
    """
    win_fonts = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    for name in font_candidates:
        for path in (name, os.path.join(win_fonts, name)):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _measure_tracked_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, tracking: float = 0.0) -> Tuple[int, int]:
    """Mide el ancho y la altura de mayúscula (cap-height) de un texto con tracking."""
    if not text:
        return 0, 0
    cap_bbox = draw.textbbox((0, 0), "H", font=font)
    cap_h = cap_bbox[3] - cap_bbox[1]
    if tracking <= 0:
        ref_bbox = draw.textbbox((0, 0), text, font=font)
        return ref_bbox[2] - ref_bbox[0], cap_h
    total_w = 0.0
    for i, ch in enumerate(text):
        cb = draw.textbbox((0, 0), ch, font=font)
        adv = draw.textlength(ch, font=font) if hasattr(draw, "textlength") else (cb[2] - cb[0])
        total_w += adv
        if i < len(text) - 1:
            total_w += tracking
    return int(round(total_w)), cap_h


def _draw_tracked_text(
    draw: ImageDraw.ImageDraw,
    pos: Tuple[float, float],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, ...],
    tracking: float = 0.0
) -> None:
    """Dibuja texto alineando exactamente la altura de mayúscula ('H') en pos[1]."""
    if not text:
        return
    cap_bbox = draw.textbbox((0, 0), "H", font=font)
    base_y = float(pos[1]) - cap_bbox[1]
    if tracking <= 0:
        ref_bbox = draw.textbbox((0, 0), text, font=font)
        draw.text((pos[0] - ref_bbox[0], base_y), text, font=font, fill=fill)
        return
    curr_x = float(pos[0])
    for ch in text:
        draw.text((curr_x, base_y), ch, font=font, fill=fill)
        adv = draw.textlength(ch, font=font) if hasattr(draw, "textlength") else (draw.textbbox((0, 0), ch, font=font)[2])
        curr_x += adv + tracking


def _apply_image_logo(qr_img: Image.Image, logo_path: str, max_ratio: float = 0.18,
                      draw_badge: bool = True, badge_bg: Tuple[int, int, int] = (255, 255, 255),
                      margin_px: int = 0) -> Image.Image:
    """Incrusta un logotipo sobre el centro de la imagen QR con marco suave y antialiasing."""
    if not os.path.isfile(logo_path):
        return qr_img

    try:
        logo = Image.open(logo_path).convert("RGBA")
    except Exception:
        return qr_img

    qr_w, qr_h = qr_img.size
    active_w = max(100, qr_w - margin_px * 2)
    active_h = max(100, qr_h - margin_px * 2)
    ratio = max(0.11, min(max_ratio, 0.15))
    max_logo_w = int(active_w * ratio * 1.15)
    max_logo_h = int(active_h * ratio * 1.15)

    logo.thumbnail((max_logo_w, max_logo_h), Image.Resampling.LANCZOS)
    logo_w, logo_h = logo.size

    combined = qr_img.convert("RGBA")
    pos_x = (qr_w - logo_w) // 2
    pos_y = (qr_h - logo_h) // 2

    if draw_badge:
        pad = max(6, int(min(logo_w, logo_h) * 0.12))
        badge_w = logo_w + pad * 2
        badge_h = logo_h + pad * 2
        badge_x = (qr_w - badge_w) // 2
        badge_y = (qr_h - badge_h) // 2

        ss = 2
        badge_hi = Image.new("RGBA", (badge_w * ss, badge_h * ss), (0, 0, 0, 0))
        draw = ImageDraw.Draw(badge_hi)
        radius = max(8, int(min(badge_w, badge_h) * 0.20)) * ss
        draw.rounded_rectangle(
            [(0, 0), (badge_w * ss - 1, badge_h * ss - 1)],
            radius=radius,
            fill=badge_bg + (255,)
        )
        badge = badge_hi.resize((badge_w, badge_h), Image.Resampling.LANCZOS)
        combined.paste(badge, (badge_x, badge_y), badge)

    combined.paste(logo, (pos_x, pos_y), logo)
    return combined.convert("RGB")


def _apply_text_badge(qr_img: Image.Image, text: str, max_ratio: float = 0.18,
                      text_color: Tuple[int, int, int] = (20, 20, 20),
                      badge_bg: Tuple[int, int, int] = (255, 255, 255),
                      margin_px: int = 0) -> Image.Image:
    """Incrusta un isotipo / etiqueta de texto central con tipografía moderna y bordes suaves."""
    text = text.strip()
    if not text:
        return qr_img

    qr_w, qr_h = qr_img.size
    active_w = max(100, qr_w - margin_px * 2)
    active_h = max(100, qr_h - margin_px * 2)
    ratio = max(0.12, min(max_ratio, 0.18))
    max_badge_w = int(active_w * ratio * 1.25)
    max_badge_h = int(active_h * ratio * 0.85)

    ss = 2
    font_size = max(16, int(max_badge_h * 0.45)) * ss
    font = _load_font(
        ["Montserrat-Bold.ttf", "segoeuib.ttf", "calibrib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"],
        font_size
    )

    dummy = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy)
    bbox = dummy_draw.textbbox((0, 0), text, font=font)
    t_w = bbox[2] - bbox[0]
    t_h = bbox[3] - bbox[1]

    pad_x = 16 * ss
    pad_y = 10 * ss
    badge_w_hi = t_w + pad_x * 2
    badge_h_hi = t_h + pad_y * 2

    badge_hi = Image.new("RGBA", (badge_w_hi, badge_h_hi), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge_hi)
    radius = max(12, int(badge_h_hi * 0.28))
    draw.rounded_rectangle(
        [(0, 0), (badge_w_hi - 1, badge_h_hi - 1)],
        radius=radius,
        fill=badge_bg + (255,)
    )
    tx = (badge_w_hi - t_w) // 2 - bbox[0]
    ty = (badge_h_hi - t_h) // 2 - bbox[1]
    draw.text((tx, ty), text, font=font, fill=text_color + (255,))

    target_w = badge_w_hi // ss
    target_h = badge_h_hi // ss
    scale = 1.0
    if target_w > max_badge_w:
        scale = min(scale, max_badge_w / target_w)
    if target_h > max_badge_h:
        scale = min(scale, max_badge_h / target_h)
    final_w = max(10, int(target_w * scale))
    final_h = max(10, int(target_h * scale))
    badge = badge_hi.resize((final_w, final_h), Image.Resampling.LANCZOS)

    combined = qr_img.convert("RGBA")
    bx = (qr_w - final_w) // 2
    by = (qr_h - final_h) // 2
    combined.paste(badge, (bx, by), badge)
    return combined.convert("RGB")


def _compute_sidebar_badge_size(
    qr_w: int,
    qr_h: int,
    line1: str,
    line2: str,
    max_ratio: float,
    margin_px: int
) -> Tuple[int, int]:
    """Calcula las dimensiones finales del badge central para despejar módulos enteros debajo."""
    line1 = line1.strip()
    line2 = line2.strip()
    if not line1 and not line2:
        return 0, 0

    active_w = max(120, qr_w - margin_px * 2)
    active_h = max(120, qr_h - margin_px * 2)
    safe_ratio = max(0.11, min(max_ratio, 0.15))
    max_w = int(active_w * safe_ratio * 1.25)
    max_h = int(active_h * safe_ratio * 0.65)

    font1 = _load_font(["Montserrat-Medium.ttf", "segoeui.ttf", "calibri.ttf", "arial.ttf"], 25)
    font2 = _load_font(["Montserrat-Bold.ttf", "segoeuib.ttf", "calibrib.ttf", "arialbd.ttf"], 31)

    dummy = Image.new("RGBA", (1, 1))
    d_draw = ImageDraw.Draw(dummy)
    bbox1 = d_draw.textbbox((0, 0), line1, font=font1) if line1 else (0, 0, 0, 0)
    w1, h1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]
    bbox2 = d_draw.textbbox((0, 0), line2, font=font2) if line2 else (0, 0, 0, 0)
    w2, h2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]

    text_w = max(w1, w2)
    spacing = 7
    text_h = h1 + (spacing if line1 and line2 else 0) + h2
    bar_w, bar_pad, pad_x, pad_y = 8, 13, 18, 12

    badge_w = bar_w + bar_pad + text_w + pad_x * 2
    badge_h = text_h + pad_y * 2

    scale = 1.0
    if badge_w > max_w:
        scale = min(scale, max_w / badge_w)
    if badge_h > max_h:
        scale = min(scale, max_h / badge_h)

    return max(10, int(badge_w * scale)), max(10, int(badge_h * scale))


def _apply_sidebar_badge(
    qr_img: Image.Image,
    line1: str = "Proyecto",
    line2: str = "GEF Bermejo",
    text_color: Tuple[int, int, int] = (0, 0, 0),
    badge_bg: Tuple[int, int, int] = (255, 255, 255),
    max_ratio: float = 0.18,
    margin_px: int = 0
) -> Image.Image:
    """
    Incrusta el badge central estilo 'Proyecto GEF Bermejo' renderizado en alta definición
    (2x supersampling) con tipografía moderna (Montserrat / Segoe UI) y barra lateral estilizada.
    """
    line1 = line1.strip()
    line2 = line2.strip()
    if not line1 and not line2:
        return qr_img

    qr_w, qr_h = qr_img.size
    active_w = max(120, qr_w - margin_px * 2)
    active_h = max(120, qr_h - margin_px * 2)
    safe_ratio = max(0.11, min(max_ratio, 0.15))
    max_w = int(active_w * safe_ratio * 1.25)
    max_h = int(active_h * safe_ratio * 0.65)

    ss = 2  # Supersampling 2x para texto ultra nítido
    font1 = _load_font(["Montserrat-Medium.ttf", "segoeui.ttf", "calibri.ttf", "arial.ttf"], 25 * ss)
    font2 = _load_font(["Montserrat-Bold.ttf", "segoeuib.ttf", "calibrib.ttf", "arialbd.ttf"], 31 * ss)

    dummy = Image.new("RGBA", (1, 1))
    d_draw = ImageDraw.Draw(dummy)

    bbox1 = d_draw.textbbox((0, 0), line1, font=font1) if line1 else (0, 0, 0, 0)
    w1 = bbox1[2] - bbox1[0]
    h1 = bbox1[3] - bbox1[1]

    bbox2 = d_draw.textbbox((0, 0), line2, font=font2) if line2 else (0, 0, 0, 0)
    w2 = bbox2[2] - bbox2[0]
    h2 = bbox2[3] - bbox2[1]

    text_w = max(w1, w2)
    spacing = 7 * ss
    text_h = h1 + (spacing if line1 and line2 else 0) + h2

    bar_w   = 8 * ss
    bar_pad = 13 * ss
    pad_x   = 18 * ss
    pad_y   = 12 * ss

    badge_w_hi = bar_w + bar_pad + text_w + pad_x * 2
    badge_h_hi = text_h + pad_y * 2

    badge_hi = Image.new("RGBA", (badge_w_hi, badge_h_hi), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(badge_hi)
    card_radius = int(10 * ss)
    b_draw.rounded_rectangle(
        [(0, 0), (badge_w_hi - 1, badge_h_hi - 1)],
        radius=card_radius,
        fill=badge_bg + (255,)
    )

    bar_x = pad_x
    bar_y = pad_y
    bar_h = text_h
    b_draw.rounded_rectangle(
        [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
        radius=bar_w // 2,
        fill=text_color + (255,)
    )

    tx = bar_x + bar_w + bar_pad
    curr_y = bar_y
    if line1:
        b_draw.text((tx - bbox1[0], curr_y - bbox1[1]), line1, font=font1, fill=text_color + (255,))
        curr_y += h1 + spacing
    if line2:
        b_draw.text((tx - bbox2[0], curr_y - bbox2[1]), line2, font=font2, fill=text_color + (255,))

    target_w = badge_w_hi // ss
    target_h = badge_h_hi // ss
    scale = 1.0
    if target_w > max_w:
        scale = min(scale, max_w / target_w)
    if target_h > max_h:
        scale = min(scale, max_h / target_h)

    final_w = max(10, int(target_w * scale))
    final_h = max(10, int(target_h * scale))
    badge = badge_hi.resize((final_w, final_h), Image.Resampling.LANCZOS)

    combined = qr_img.convert("RGBA")
    bx = (qr_w - final_w) // 2
    by = (qr_h - final_h) // 2
    combined.paste(badge, (bx, by), badge)
    return combined.convert("RGB")


_JAGUAR_CACHE: Dict[int, Image.Image] = {}


def _jaguar_art_mask(size: int, image_path: Optional[str] = None) -> Image.Image:
    """
    Máscara 'L' detallada del jaguar (blanco = trazo) para usar como fondo.
    Usa la imagen elegida por el usuario, o 'jaguar.png' de la carpeta del
    proyecto si existe; si no, un dibujo procedimental de respaldo.
    """
    custom = image_path if image_path and os.path.isfile(image_path) else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "jaguar.png")
    art = None
    if os.path.isfile(custom):
        try:
            src = Image.open(custom).convert("RGBA")
            bg = Image.new("RGBA", src.size, (255, 255, 255, 255))
            gray = Image.alpha_composite(bg, src).convert("L")
            inv = ImageOps.invert(gray).point(lambda p: 255 if p > 60 else 0)
            bbox = inv.getbbox()
            if bbox:
                art = inv.crop(bbox)
        except Exception:
            art = None

    if art is None:
        big = 512
        art = Image.new("L", (big, big), 0)
        d = ImageDraw.Draw(art)
        w = 255
        # Orejas
        d.chord([30, 20, 170, 200], 180, 300, fill=w)
        d.chord([342, 20, 482, 200], 240, 360, fill=w)
        # Cejas
        d.chord([130, 90, 250, 170], 190, 330, fill=w)
        d.chord([262, 90, 382, 170], 210, 350, fill=w)
        # Manchas de la frente
        d.ellipse([226, 110, 286, 170], fill=w)
        for box in ([180, 160, 215, 210], [297, 160, 332, 210],
                    [120, 190, 155, 250], [357, 190, 392, 250],
                    [222, 190, 250, 245], [262, 190, 290, 245]):
            d.ellipse(box, fill=w)
        # Ojos (contorno con hueco)
        d.polygon([(140, 280), (240, 300), (220, 345), (165, 320)], fill=w)
        d.polygon([(372, 280), (272, 300), (292, 345), (347, 320)], fill=w)
        d.ellipse([180, 300, 215, 322], fill=0)
        d.ellipse([297, 300, 332, 322], fill=0)
        # Mejillas
        d.chord([60, 230, 160, 450], 100, 260, fill=w)
        d.chord([352, 230, 452, 450], 280, 80, fill=w)
        d.ellipse([110, 330, 140, 380], fill=w)
        d.ellipse([372, 330, 402, 380], fill=w)
        # Hocico
        d.chord([150, 380, 250, 520], 110, 250, fill=w)
        d.chord([262, 380, 362, 520], 290, 70, fill=w)
        # Nariz
        d.polygon([(205, 420), (307, 420), (256, 470)], fill=w)
        d.line([(256, 470), (256, 500)], fill=w, width=10)
        # Boca / mentón
        d.chord([200, 470, 312, 540], 0, 180, fill=w)
        art = art.crop(art.getbbox())

    art.thumbnail((size, size), Image.Resampling.LANCZOS)
    out = Image.new("L", (size, size), 0)
    out.paste(art, ((size - art.width) // 2, (size - art.height) // 2))
    return out


def _apply_jaguar_background(
    qr_img: Image.Image,
    module_rgb: Tuple[int, int, int],
    bg_rgb: Tuple[int, int, int],
    margin: int,
    opacity: float = 0.28,
    image_path: Optional[str] = None,
    n_modules: int = 0,
    matrix: Optional[list] = None
) -> Image.Image:
    """
    Dibuja la imagen elegida (o la figura del jaguar) DETRÁS de los puntos del QR
    de forma 100% íntegra, continua y sin deformar ni recortar sus bordes/orejas,
    manteniendo limpios únicamente los 3 ojos buscadores 7x7 para lectura instantánea.
    """
    opacity = max(0.18, min(opacity, 0.30))
    w, h = qr_img.size
    area = min(w, h) - margin * 2

    custom = image_path if image_path and os.path.isfile(image_path) else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "jaguar.png")

    bg_base = Image.new("RGB", (w, h), bg_rgb)

    def clear_finder_boxes(mask_img: Image.Image):
        if not n_modules:
            return
        md = ImageDraw.Draw(mask_img)
        cell = area / float(n_modules)
        # Limpiar únicamente el interior exacto 7x7 de los 3 ojos buscadores (sin cortar orejas ni esquinas del fondo)
        e = int(cell * 7.0)
        md.rectangle([margin, margin, margin + e, margin + e], fill=0)
        md.rectangle([margin + area - e, margin, margin + area, margin + e], fill=0)
        md.rectangle([margin, margin + area - e, margin + e, margin + area], fill=0)

    if os.path.isfile(custom):
        try:
            src = Image.open(custom).convert("RGBA")
            src.thumbnail((area, area), Image.Resampling.LANCZOS)
            canvas_rgba = Image.new("RGBA", (w, h), bg_rgb + (255,))
            px = (w - src.width) // 2
            py = (h - src.height) // 2
            canvas_rgba.paste(src, (px, py), src)
            img_rgb = canvas_rgba.convert("RGB")

            alpha_mask = Image.new("L", (w, h), 0)
            alpha_draw = ImageDraw.Draw(alpha_mask)
            alpha_draw.rectangle([px, py, px + src.width, py + src.height], fill=int(255 * opacity))
            clear_finder_boxes(alpha_mask)
            bg_layer = Image.composite(img_rgb, bg_base, alpha_mask)
        except Exception:
            art = _jaguar_art_mask(int(area * 1.0), None)
            art_full = Image.new("L", (w, h), 0)
            art_full.paste(art, ((w - art.width) // 2, (h - art.height) // 2))
            art_full = art_full.point(lambda p: int(p * opacity))
            clear_finder_boxes(art_full)
            tint = Image.new("RGB", (w, h), module_rgb)
            bg_layer = Image.composite(tint, bg_base, art_full)
    else:
        art = _jaguar_art_mask(int(area * 1.0), None)
        art_full = Image.new("L", (w, h), 0)
        art_full.paste(art, ((w - art.width) // 2, (h - art.height) // 2))
        art_full = art_full.point(lambda p: int(p * opacity))
        clear_finder_boxes(art_full)
        tint = Image.new("RGB", (w, h), module_rgb)
        bg_layer = Image.composite(tint, bg_base, art_full)

    # Superponer los puntos del QR directamente sobre la imagen de fondo continua (sin perforar huecos blancos)
    from PIL import ImageChops
    diff = ImageChops.difference(qr_img.convert("RGB"), bg_base)
    module_mask = diff.convert("L").point(lambda p: 255 if p > 20 else 0)
    return Image.composite(qr_img.convert("RGB"), bg_layer, module_mask)


def _jaguar_mask(size: int) -> Image.Image:
    """
    Devuelve una máscara 'L' (blanco = relleno) con forma de cabeza de jaguar.
    Mantiene el núcleo central sólido para que el muestreo óptico sea fiable.
    """
    if size in _JAGUAR_CACHE:
        return _JAGUAR_CACHE[size]

    big = 256
    custom = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jaguar.png")
    mask = None
    if os.path.isfile(custom):
        try:
            src = Image.open(custom).convert("RGBA")
            bg = Image.new("RGBA", src.size, (255, 255, 255, 255))
            gray = Image.alpha_composite(bg, src).convert("L")
            inv = ImageOps.invert(gray).point(lambda p: 255 if p > 40 else 0)
            bbox = inv.getbbox()
            if bbox:
                inv = inv.crop(bbox)
                from PIL import ImageFilter
                inv = inv.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.MinFilter(5))
                inv.thumbnail((big, big), Image.Resampling.LANCZOS)
                mask = Image.new("L", (big, big), 0)
                mask.paste(inv, ((big - inv.width) // 2, (big - inv.height) // 2))
        except Exception:
            mask = None

    if mask is None:
        mask = Image.new("L", (big, big), 0)
        d = ImageDraw.Draw(mask)
        # Orejas
        d.polygon([(30, 110), (55, 10), (115, 60)], fill=255)
        d.polygon([(226, 110), (201, 10), (141, 60)], fill=255)
        # Cabeza sólida de alto relleno para garantizar lectura
        d.ellipse([18, 36, 238, 236], fill=255)
        d.polygon([(36, 145), (220, 145), (176, 248), (80, 248)], fill=255)

    small = mask.resize((size, size), Image.Resampling.LANCZOS)
    _JAGUAR_CACHE[size] = small
    return small


def _paw_mask(size: int) -> Image.Image:
    """
    Máscara 'L' de una huella de felino con sus 4 dedos completamente separados
    y su almohadilla natural sin ninguna deformación geométrica.
    """
    big = 512
    m = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(m)
    # 4 dedos ovalados bien separados en arco superior (proporción natural sin deformar)
    d.ellipse([28, 128, 138, 268], fill=255)
    d.ellipse([136, 28, 246, 184], fill=255)
    d.ellipse([266, 28, 376, 184], fill=255)
    d.ellipse([374, 128, 484, 268], fill=255)
    # Almohadilla trilobulada natural abajo, separada de los dedos
    d.ellipse([146, 224, 366, 440], fill=255)
    d.ellipse([76, 276, 266, 476], fill=255)
    d.ellipse([246, 276, 436, 476], fill=255)
    return m.resize((size, size), Image.Resampling.LANCZOS)


def _image_eye_mask(path: str, size: int) -> Optional[Image.Image]:
    """
    Prepara la imagen personalizada para el centro del ojo conservando al 100%
    su relación de aspecto y su forma original sin estirarla ni deformarla.
    Elimina fondos blancos para integrarla limpiamente en el cojín óptico 3x3.
    """
    try:
        src = Image.open(path).convert("RGBA")
        alpha = src.getchannel("A")
        if alpha.getextrema()[0] < 245:
            # Imagen con transparencia real: recortar al contenido visible
            bbox = alpha.point(lambda p: 255 if p > 20 else 0).getbbox()
            if bbox:
                src = src.crop(bbox)
            bg = Image.new("RGBA", src.size, (255, 255, 255, 255))
            gray = Image.alpha_composite(bg, src).convert("L")
            inv = ImageOps.invert(gray)
            mask = Image.composite(inv, Image.new("L", src.size, 0), alpha.point(lambda p: 255 if p > 20 else 0))
            mask = mask.point(lambda p: 255 if p > 35 else 0)
        else:
            # Imagen con fondo blanco/claro: extraer la silueta oscura sin deformar
            bg = Image.new("RGBA", src.size, (255, 255, 255, 255))
            gray = Image.alpha_composite(bg, src).convert("L")
            mask = ImageOps.invert(gray).point(lambda p: 255 if p > 40 else 0)
            bbox = mask.getbbox()
            if bbox:
                mask = mask.crop(bbox)

        target_box = max(8, int(size * 0.88))
        mask.thumbnail((target_box, target_box), Image.Resampling.LANCZOS)
        out = Image.new("L", (size, size), 0)
        out.paste(mask, ((size - mask.width) // 2, (size - mask.height) // 2))
        return out
    except Exception:
        return None


def render_custom_matrix_qr(
    matrix: list,
    box_size: int = 16,
    border: int = 4,
    body_style: str = "dots",
    eye_frame_style: str = "square",
    eye_ball_style: str = "square",
    module_color: Tuple[int, int, int] = (0, 0, 0),
    bg_color: Tuple[int, int, int] = (255, 255, 255),
    eye_ball_image: Optional[str] = None,
    clear_rect: Optional[Tuple[int, int, int, int]] = None
) -> Image.Image:
    """
    Renderiza el código QR con antialiasing de alta definición (2x supersampling),
    combinando estética moderna con lectura instantánea garantizada en celulares:
    - Ojos buscadores calibrados para mantener la proporción 1:1:3:1:1 y esquinas homográficas exactas.
    - Módulos estructurales (timing, alineación y formato) con alta continuidad óptica.
    """
    n = len(matrix)
    total_size = (n + border * 2) * box_size

    ss = 2  # Supersampling 2x para bordes suaves y aspecto vectorial
    b = box_size * ss
    hi_size = total_size * ss

    img_hi = Image.new("RGB", (hi_size, hi_size), bg_color)
    draw = ImageDraw.Draw(img_hi)

    alignment_centers = _get_alignment_centers(n)

    def is_finder_area(rr: int, cc: int) -> bool:
        return (rr < 8 and cc < 8) or (rr < 8 and cc >= n - 8) or (rr >= n - 8 and cc < 8)

    def is_cleared_by_badge(rr: int, cc: int) -> bool:
        if not clear_rect:
            return False
        cx0, cy0, cx1, cy1 = clear_rect
        # Margen de seguridad para no cortar módulos a la mitad ni permitir módulos rotos
        pad = max(2, int(box_size * 0.45))
        mx0 = (cc + border) * box_size
        my0 = (rr + border) * box_size
        mx1 = mx0 + box_size
        my1 = my0 + box_size
        return not (mx1 <= (cx0 - pad) or mx0 >= (cx1 + pad) or my1 <= (cy0 - pad) or my0 >= (cy1 + pad))

    def is_active_body(rr: int, cc: int) -> bool:
        if rr < 0 or rr >= n or cc < 0 or cc >= n:
            return False
        if not matrix[rr][cc]:
            return False
        if is_finder_area(rr, cc) or is_cleared_by_badge(rr, cc):
            return False
        return True

    # 1. DIBUJAR CUERPO (BODY MODULES) DE FORMA UNIFORME, SUAVE Y DE LECTURA INSTANTÁNEA
    for r in range(n):
        for c in range(n):
            if not is_active_body(r, c):
                continue

            x0 = (c + border) * b
            y0 = (r + border) * b
            x1 = x0 + b - 1
            y1 = y0 + b - 1
            cx = x0 + (b - 1) / 2.0
            cy = y0 + (b - 1) / 2.0

            is_struct = _is_functional_module(r, c, n, alignment_centers)

            # Para máxima compatibilidad con lectores de iPhone y Android:
            # Los módulos estructurales (líneas de timing en fila/col 6, alineación y formato)
            # SIEMPRE deben ser cuadrados sólidos exactos para sincronizar el reloj de lectura óptico.
            if is_struct or body_style == "square":
                draw.rectangle([x0, y0, x1, y1], fill=module_color)
            elif body_style == "jaguar":
                jm = _jaguar_mask(b)
                img_hi.paste(module_color, (x0, y0, x0 + b, y0 + b), jm)
            elif body_style == "dots":
                rad = b * 0.49
                draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=module_color)
            elif body_style == "circle":
                rad = b * 0.495
                draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=module_color)
            elif body_style == "rounded":
                pad = 0 if is_struct else max(1, int(b * 0.03))
                rad = max(3, int(b * 0.32))
                draw.rounded_rectangle([x0 + pad, y0 + pad, x1 - pad, y1 - pad], radius=rad, fill=module_color)
            elif body_style == "diamond":
                pad = b * 0.01
                draw.polygon([(cx, y0 + pad), (x1 - pad, cy), (cx, y1 - pad), (x0 + pad, cy)], fill=module_color)
                cr = b * (0.49 if is_struct else 0.45)
                draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=module_color)
            elif body_style == "star":
                w_in = b * 0.39
                pad = b * 0.01
                draw.polygon([
                    (cx, y0 + pad), (cx + w_in, cy - w_in),
                    (x1 - pad, cy), (cx + w_in, cy + w_in),
                    (cx, y1 - pad), (cx - w_in, cy + w_in),
                    (x0 + pad, cy), (cx - w_in, cy - w_in)
                ], fill=module_color)
                cr = b * (0.49 if is_struct else 0.435)
                draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=module_color)
            elif body_style == "horizontal_bars":
                has_left = is_active_body(r, c - 1)
                has_right = is_active_body(r, c + 1)
                v_pad = max(1, int(b * 0.04))
                h_pad = max(1, int(b * 0.04))
                bx0 = x0 if has_left else x0 + h_pad
                bx1 = x1 if has_right else x1 - h_pad
                by0 = y0 + v_pad
                by1 = y1 - v_pad
                rad = max(2, (by1 - by0 - 2) // 2)
                draw.rounded_rectangle(
                    [bx0, by0, bx1, by1],
                    radius=rad,
                    corners=(not has_left, not has_right, not has_right, not has_left),
                    fill=module_color
                )
            elif body_style == "vertical_bars":
                has_top = is_active_body(r - 1, c)
                has_bottom = is_active_body(r + 1, c)
                h_pad = max(1, int(b * 0.04))
                v_pad = max(1, int(b * 0.04))
                bx0 = x0 + h_pad
                bx1 = x1 - h_pad
                by0 = y0 if has_top else y0 + v_pad
                by1 = y1 if has_bottom else y1 - v_pad
                rad = max(2, (bx1 - bx0 - 2) // 2)
                draw.rounded_rectangle(
                    [bx0, by0, bx1, by1],
                    radius=rad,
                    corners=(not has_top, not has_top, not has_bottom, not has_bottom),
                    fill=module_color
                )
            else:  # square clásico
                draw.rectangle([x0, y0, x1, y1], fill=module_color)

    # 2. DIBUJAR LOS 3 OJOS BUSCADORES (FINDER PATTERNS) EN ALTA DEFINICIÓN
    # Se preserva el vértice exterior de cada ojo para que la proyección homográfica de las 4 esquinas sea 100% exacta
    def draw_eye(top_r, left_c):
        ox = (left_c + border) * b
        oy = (top_r + border) * b
        outer_w = 7 * b
        thick = b

        # Máscara de esquinas que preserva intacto el vértice más externo del QR en cada uno de los 3 ojos
        if top_r == 0 and left_c == 0:
            c_round = (False, True, True, True)
            c_leaf  = (False, True, False, True)
        elif top_r == 0 and left_c > 0:
            c_round = (True, False, True, True)
            c_leaf  = (True, False, True, False)
        else:
            c_round = (True, True, True, False)
            c_leaf  = (True, False, True, False)

        if eye_frame_style == "circle":
            rad = int(b * 0.70)
            rad_in = max(2, int(rad * 0.50))
            draw.rounded_rectangle([ox, oy, ox + outer_w - 1, oy + outer_w - 1], radius=rad, corners=c_round, fill=module_color)
            draw.rounded_rectangle([ox + thick, oy + thick, ox + outer_w - thick - 1, oy + outer_w - thick - 1], radius=rad_in, corners=c_round, fill=bg_color)
        elif eye_frame_style == "rounded":
            rad = int(b * 0.65)
            rad_in = max(2, int(rad * 0.50))
            draw.rounded_rectangle([ox, oy, ox + outer_w - 1, oy + outer_w - 1], radius=rad, corners=c_round, fill=module_color)
            draw.rounded_rectangle([ox + thick, oy + thick, ox + outer_w - thick - 1, oy + outer_w - thick - 1], radius=rad_in, corners=c_round, fill=bg_color)
        elif eye_frame_style == "leaf":
            rad = int(b * 0.85)
            rad_in = max(2, int(rad * 0.55))
            draw.rounded_rectangle([ox, oy, ox + outer_w - 1, oy + outer_w - 1], radius=rad, corners=c_leaf, fill=module_color)
            draw.rounded_rectangle([ox + thick, oy + thick, ox + outer_w - thick - 1, oy + outer_w - thick - 1], radius=rad_in, corners=c_leaf, fill=bg_color)
        elif eye_frame_style == "dots":
            rad_frame = int(b * 0.65)
            draw.rounded_rectangle([ox, oy, ox + outer_w - 1, oy + outer_w - 1], radius=rad_frame, corners=c_round, fill=module_color)
            draw.rectangle([ox + thick, oy + thick, ox + outer_w - thick - 1, oy + outer_w - thick - 1], fill=bg_color)
            for dr in range(7):
                for dc in range(7):
                    if dr == 0 or dr == 6 or dc == 0 or dc == 6:
                        px = ox + dc * b + (b - 1) / 2.0
                        py = oy + dr * b + (b - 1) / 2.0
                        rad = b * 0.50
                        draw.ellipse([px - rad, py - rad, px + rad, py + rad], fill=module_color)
            draw.rectangle([ox + thick, oy + thick, ox + outer_w - thick - 1, oy + outer_w - thick - 1], fill=bg_color)
        else:  # square clásico
            draw.rectangle([ox, oy, ox + outer_w - 1, oy + outer_w - 1], fill=module_color)
            draw.rectangle([ox + thick, oy + thick, ox + outer_w - thick - 1, oy + outer_w - thick - 1], fill=bg_color)

        cx0 = ox + 2 * thick
        cy0 = oy + 2 * thick
        cx1 = ox + 5 * thick - 1
        cy1 = oy + 5 * thick - 1

        eye_size = cx1 - cx0 + 1
        # Cojín óptico sub-umbral (< 128) para que el escáner del celular vea el bloque 3x3 100% sólido
        # mientras el ojo humano ve la huella o imagen personalizada 100% nítida y sin ninguna deformación
        cushion_rgb = tuple(int(module_color[i] * 0.64 + bg_color[i] * 0.36) for i in range(3))
        c_inner = c_leaf if eye_frame_style == "leaf" else c_round
        if eye_ball_style == "paw":
            draw.rounded_rectangle([cx0, cy0, cx1, cy1], radius=int(thick * 0.55), corners=c_inner, fill=cushion_rgb)
            paw_m = _paw_mask(eye_size)
            img_hi.paste(module_color, (cx0, cy0, cx0 + paw_m.width, cy0 + paw_m.height), paw_m)
        elif eye_ball_style == "image" and eye_ball_image and os.path.isfile(eye_ball_image):
            draw.rounded_rectangle([cx0, cy0, cx1, cy1], radius=int(thick * 0.55), corners=c_inner, fill=cushion_rgb)
            eye_m = _image_eye_mask(eye_ball_image, eye_size)
            if eye_m is not None:
                img_hi.paste(module_color, (cx0, cy0, cx0 + eye_m.width, cy0 + eye_m.height), eye_m)
            else:
                draw.rectangle([cx0, cy0, cx1, cy1], fill=module_color)
        elif eye_ball_style == "circle":
            draw.rounded_rectangle([cx0 + 2, cy0 + 2, cx1 - 2, cy1 - 2], radius=int(thick * 0.90), fill=module_color)
        elif eye_ball_style == "rounded":
            draw.rounded_rectangle([cx0, cy0, cx1, cy1], radius=int(thick * 0.65), fill=module_color)
        elif eye_ball_style == "leaf":
            draw.rounded_rectangle([cx0, cy0, cx1, cy1], radius=int(thick * 0.75), corners=c_leaf, fill=module_color)
        elif eye_ball_style == "dots_3x3":
            draw.rounded_rectangle([cx0 + 4, cy0 + 4, cx1 - 4, cy1 - 4], radius=int(thick * 0.5), fill=module_color)
            for dr in range(3):
                for dc in range(3):
                    px = cx0 + dc * b + (b - 1) / 2.0
                    py = cy0 + dr * b + (b - 1) / 2.0
                    rad = b * 0.48
                    draw.ellipse([px - rad, py - rad, px + rad, py + rad], fill=module_color)
        elif eye_ball_style == "bars_v":
            mid_y0 = cy0 + b
            mid_y1 = cy0 + 2 * b - 1
            draw.rectangle([cx0, mid_y0, cx1, mid_y1], fill=module_color)
            for dc in range(3):
                bx0 = cx0 + dc * b + 2
                bx1 = cx0 + (dc + 1) * b - 3
                draw.rounded_rectangle([bx0, cy0, bx1, cy1], radius=4, fill=module_color)
        elif eye_ball_style == "bars_h":
            mid_x0 = cx0 + b
            mid_x1 = cx0 + 2 * b - 1
            draw.rectangle([mid_x0, cy0, mid_x1, cy1], fill=module_color)
            for dr in range(3):
                by0 = cy0 + dr * b + 2
                by1 = cy0 + (dr + 1) * b - 3
                draw.rounded_rectangle([cx0, by0, cx1, by1], radius=4, fill=module_color)
        else:  # square clásico
            draw.rectangle([cx0, cy0, cx1, cy1], fill=module_color)

    draw_eye(0, 0)
    draw_eye(0, n - 7)
    draw_eye(n - 7, 0)

    return img_hi.resize((total_size, total_size), Image.Resampling.LANCZOS)


def add_name_label_below_qr(
    qr_img: Image.Image,
    full_name: str,
    bg_color: Tuple[int, int, int] = (255, 255, 255),
    text_color: Tuple[int, int, int] = (0, 0, 0)
) -> Image.Image:
    """
    Añade el nombre completo de la persona debajo del código QR con un diseño
    tipográfico elegante y moderno (fuente geométrica Montserrat/Segoe UI en alta
    definición 2x, espaciado entre letras, línea divisoria estilizada y márgenes amplios).
    """
    if not full_name or not full_name.strip():
        return qr_img

    qr_w, qr_h = qr_img.size
    name_upper = re.sub(r"\s+", " ", full_name.strip()).upper()

    ss = 2  # Supersampling 2x para texto ultra nítido
    font_candidates = [
        "Montserrat-Bold.ttf",
        "Montserrat-SemiBold.ttf",
        "segoeuib.ttf",
        "calibrib.ttf",
        "trebucbd.ttf",
        "arialbd.ttf",
        "DejaVuSans-Bold.ttf"
    ]

    # Respetar márgenes laterales amplios (alineado con el ancho de la matriz del QR)
    max_text_w_hi = int(qr_w * 0.82) * ss
    font_size_hi = max(24, int(qr_w * 0.048)) * ss
    min_font_size_hi = max(18, int(qr_w * 0.032)) * ss
    tracking_hi = max(1.5, qr_w * 0.0028) * ss

    dummy = Image.new("RGB", (1, 1))
    d_draw = ImageDraw.Draw(dummy)

    font = _load_font(font_candidates, font_size_hi)
    while font_size_hi > min_font_size_hi:
        tw, _ = _measure_tracked_text(d_draw, name_upper, font, tracking_hi)
        if tw <= max_text_w_hi:
            break
        font_size_hi -= 2
        tracking_hi = max(1.0 * ss, font_size_hi * 0.055)
        font = _load_font(font_candidates, font_size_hi)

    # Si el nombre es muy largo, dividir equilibradamente en 2 líneas
    lines = [name_upper]
    tw, th = _measure_tracked_text(d_draw, name_upper, font, tracking_hi)
    if tw > max_text_w_hi and " " in name_upper:
        words = name_upper.split(" ")
        best_split = 1
        best_diff = 10**9
        for i in range(1, len(words)):
            l1 = " ".join(words[:i])
            l2 = " ".join(words[i:])
            diff = abs(len(l1) - len(l2))
            if diff < best_diff:
                best_diff = diff
                best_split = i
        lines = [" ".join(words[:best_split]), " ".join(words[best_split:])]
        # Ajustar si alguna línea aún supera el margen
        while font_size_hi > int(15 * ss):
            w_max = max(_measure_tracked_text(d_draw, ln, font, tracking_hi)[0] for ln in lines)
            if w_max <= max_text_w_hi:
                break
            font_size_hi -= 2
            font = _load_font(font_candidates, font_size_hi)

    line_metrics = [_measure_tracked_text(d_draw, ln, font, tracking_hi) for ln in lines]
    line_gap_hi = int(font_size_hi * 0.34)
    total_text_h_hi = sum(m[1] for m in line_metrics) + line_gap_hi * (len(lines) - 1)
    max_line_w_hi = max(m[0] for m in line_metrics)

    top_pad_hi = int(qr_w * 0.055) * ss
    sep_to_text_hi = int(qr_w * 0.040) * ss
    bottom_pad_hi = int(qr_w * 0.065) * ss
    strip_h_hi = top_pad_hi + sep_to_text_hi + total_text_h_hi + bottom_pad_hi
    strip_w_hi = qr_w * ss

    strip_hi = Image.new("RGB", (strip_w_hi, strip_h_hi), bg_color)
    s_draw = ImageDraw.Draw(strip_hi)

    # Color muy suave para la línea decorativa asegurando que no interfiera con los buscadores QR
    def blend_rgb(c1, c2, alpha: float) -> Tuple[int, int, int]:
        return tuple(int(c1[i] * (1.0 - alpha) + c2[i] * alpha) for i in range(3))

    accent_line_col = blend_rgb(bg_color, text_color, 0.10)
    accent_dot_col  = blend_rgb(bg_color, text_color, 0.25)
    pill_bg_col     = blend_rgb(bg_color, text_color, 0.035)
    pill_border_col = blend_rgb(bg_color, text_color, 0.14)

    # 1. Línea divisoria sutil con rombo central elegante
    sep_y = top_pad_hi
    line_half_w = min(int(qr_w * 0.34) * ss, max(int(qr_w * 0.18) * ss, max_line_w_hi // 2))
    cx_hi = strip_w_hi // 2
    gap_center = int(14 * ss)

    s_draw.line([(cx_hi - line_half_w, sep_y), (cx_hi - gap_center, sep_y)], fill=accent_line_col, width=max(2, ss))
    s_draw.line([(cx_hi + gap_center, sep_y), (cx_hi + line_half_w, sep_y)], fill=accent_line_col, width=max(2, ss))

    # Pequeño rombo central decorativo
    d_rad = int(4.5 * ss)
    s_draw.polygon(
        [(cx_hi, sep_y - d_rad), (cx_hi + d_rad, sep_y), (cx_hi, sep_y + d_rad), (cx_hi - d_rad, sep_y)],
        fill=accent_dot_col
    )

    # 2. Pastilla / tarjeta sutil alrededor del nombre para darle acabado de credencial
    pill_pad_x = int(24 * ss)
    pill_pad_y = int(13 * ss)
    text_top_y = sep_y + sep_to_text_hi
    pill_x0 = max(int(qr_w * 0.06) * ss, cx_hi - max_line_w_hi // 2 - pill_pad_x)
    pill_x1 = min(strip_w_hi - int(qr_w * 0.06) * ss, cx_hi + max_line_w_hi // 2 + pill_pad_x)
    pill_y0 = text_top_y - pill_pad_y
    pill_y1 = text_top_y + total_text_h_hi + pill_pad_y
    pill_radius = min(int(16 * ss), (pill_y1 - pill_y0) // 2)

    s_draw.rounded_rectangle(
        [pill_x0, pill_y0, pill_x1, pill_y1],
        radius=pill_radius,
        fill=pill_bg_col,
        outline=pill_border_col,
        width=max(2, ss)
    )

    # 3. Dibujar el nombre centrado con tracking
    curr_y = text_top_y
    for idx, ln in enumerate(lines):
        lw, lh = line_metrics[idx]
        lx = (strip_w_hi - lw) / 2.0
        _draw_tracked_text(s_draw, (lx, curr_y), ln, font, text_color, tracking_hi)
        curr_y += lh + line_gap_hi

    strip_final_h = strip_h_hi // ss
    strip_img = strip_hi.resize((qr_w, strip_final_h), Image.Resampling.LANCZOS)

    new_img = Image.new("RGB", (qr_w, qr_h + strip_final_h), bg_color)
    new_img.paste(qr_img, (0, 0))
    new_img.paste(strip_img, (0, qr_h))
    return new_img


def _detect_gafete_boxes(gafete_img: Image.Image) -> Tuple[Tuple[int, int, int, int], Tuple[int, int, int, int]]:
    """
    Detecta automáticamente las coordenadas (x, y, w, h) de los dos recuadros claros
    del gafete en cualquier estilo o disposición (Nombre arriba / QR abajo, o QR arriba / Nombre abajo):
    - Recuadro rectangular ancho (para el NOMBRE)
    - Recuadro casi cuadrado (para el QR)
    Si se usa un diseño sin recuadros claros detectables, aplica las proporciones estándar.
    """
    im_l = gafete_img.convert("L")
    w, h = im_l.size
    pix = im_l.load()
    step_x = max(1, w // 320)

    def find_blocks_at_thresh(thresh: int):
        rows = []
        for y in range(int(h * 0.15), int(h * 0.95)):
            runs = []
            cur_start = None
            for x in range(int(w * 0.02), int(w * 0.98), step_x):
                if pix[x, y] >= thresh:
                    if cur_start is None:
                        cur_start = x
                else:
                    if cur_start is not None:
                        runs.append((cur_start, x - step_x))
                        cur_start = None
            if cur_start is not None:
                runs.append((cur_start, int(w * 0.98) - step_x))
            if not runs:
                continue
            best_run = max(runs, key=lambda r: r[1] - r[0])
            span = best_run[1] - best_run[0]
            if w * 0.22 <= span <= w * 0.94:
                rows.append((y, best_run[0], best_run[1], span))

        blocks = []
        cur = []
        for r in rows:
            if not cur:
                cur = [r]
            else:
                prev = cur[-1]
                if r[0] - prev[0] <= max(4, int(h * 0.008)) and abs(r[3] - prev[3]) <= w * 0.12:
                    cur.append(r)
                else:
                    blocks.append(cur)
                    cur = [r]
        if cur:
            blocks.append(cur)

        valid_blocks = []
        for b in blocks:
            y0, y1 = b[0][0], b[-1][0]
            bh = y1 - y0
            if bh < h * 0.045:
                continue
            mid = b[len(b) // 2]
            bx0, bx1, bw = mid[1], mid[2], mid[3]
            mid_y = (y0 + y1) // 2
            out_left = max(2, bx0 - int(w * 0.03))
            if pix[out_left, mid_y] >= thresh:
                continue
            valid_blocks.append((bx0, y0, bw, bh))
        return valid_blocks

    name_box = None
    qr_box = None

    for t in range(244, 224, -2):
        blocks = find_blocks_at_thresh(t)
        cand_name = None
        cand_qr = None
        for bx, by, bw, bh in blocks:
            aspect = bw / max(1, bh)
            if 2.5 <= aspect <= 14.0 and bw > w * 0.55:
                if cand_name is None or bw > cand_name[2]:
                    cand_name = (bx, by, bw, bh)
            elif 0.72 <= aspect <= 1.38 and w * 0.24 <= bw <= w * 0.65 and bh >= h * 0.16:
                if cand_qr is None or abs(aspect - 1.0) < abs((cand_qr[2] / max(1, cand_qr[3])) - 1.0):
                    cand_qr = (bx, by, bw, bh)
        if cand_name and cand_qr:
            name_box = cand_name
            qr_box = cand_qr
            break
        if cand_name and not name_box:
            name_box = cand_name
        if cand_qr and not qr_box:
            qr_box = cand_qr

    if not name_box:
        name_box = (int(w * 0.050), int(h * 0.331), int(w * 0.900), int(h * 0.142))
    if not qr_box:
        qr_box = (int(w * 0.315), int(h * 0.510), int(w * 0.370), int(h * 0.242))

    return name_box, qr_box


def detect_gafete_layout(gafete_path: Optional[str] = None) -> dict:
    """
    Detecta la disposición de una plantilla de gafete y devuelve valores porcentuales
    listos para los controles de posición y tamaño en la interfaz:
    - qr_x, qr_y: centro del QR en % del ancho y alto del gafete (0..100)
    - qr_size: lado del QR en % del ancho del gafete (10..90)
    - name_x, name_y: centro del Nombre en % del ancho y alto del gafete (0..100)
    - name_size: escala del texto del Nombre en % (100 = tamaño óptimo automático)
    """
    default_gafete = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gafete_plantilla.jpg")
    path = gafete_path if (gafete_path and os.path.isfile(gafete_path)) else default_gafete
    if not os.path.isfile(path):
        return {
            "qr_x": 50.0,
            "qr_y": 64.0,
            "qr_size": 34.5,
            "name_x": 50.0,
            "name_y": 40.0,
            "name_size": 100.0,
        }

    gafete = Image.open(path).convert("RGB")
    w, h = gafete.size
    name_box, qr_box = _detect_gafete_boxes(gafete)
    nx, ny, nw, nh = name_box
    qx, qy, qw, qh = qr_box

    inset = max(4, int(min(qw, qh) * 0.038))
    target_side = max(20, min(qw - inset * 2, qh - inset * 2))

    return {
        "qr_x": round(((qx + qw / 2.0) / w) * 100.0, 1),
        "qr_y": round(((qy + qh / 2.0) / h) * 100.0, 1),
        "qr_size": round((target_side / w) * 100.0, 1),
        "name_x": round(((nx + nw / 2.0) / w) * 100.0, 1),
        "name_y": round(((ny + nh / 2.0) / h) * 100.0, 1),
        "name_size": 100.0,
        "name_box_rel": (nx / w, ny / h, nw / w, nh / h),
        "qr_box_rel": (qx / w, qy / h, qw / w, qh / h),
    }


def compose_gafete_image(
    qr_img: Image.Image,
    full_name: str,
    gafete_path: Optional[str] = None,
    text_color: Tuple[int, int, int] = (30, 41, 35),
    qr_x: Optional[float] = None,
    qr_y: Optional[float] = None,
    qr_size: Optional[float] = None,
    name_x: Optional[float] = None,
    name_y: Optional[float] = None,
    name_size: Optional[float] = None,
) -> Image.Image:
    """
    Compone una imagen de Gafete en alta resolución adaptándose a cualquier estilo de plantilla
    y permitiendo ajustar libremente la posición (X, Y) y el tamaño tanto del Nombre como del QR.
    """
    default_gafete = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gafete_plantilla.jpg")
    path = gafete_path if (gafete_path and os.path.isfile(gafete_path)) else default_gafete
    if not os.path.isfile(path):
        return add_name_label_below_qr(qr_img, full_name=full_name)

    gafete = Image.open(path).convert("RGB")
    # Escalar a alta resolución (>= 1360px de ancho) para que el QR dentro del gafete
    # tenga ~500x500 px y se escanee al instante en cualquier celular e impresión.
    if gafete.width < 1200:
        scale_up = 2
        gafete = gafete.resize((gafete.width * scale_up, gafete.height * scale_up), Image.Resampling.LANCZOS)

    gw, gh = gafete.size
    name_box, qr_box = _detect_gafete_boxes(gafete)
    nx, ny, nw, nh = name_box
    qx, qy, qw, qh = qr_box

    # --- 1. COLOCAR EL QR ---
    from PIL import ImageChops
    qr_rgb = qr_img.convert("RGB")
    bg_corner = qr_rgb.getpixel((0, 0))
    diff = ImageChops.difference(qr_rgb, Image.new("RGB", qr_rgb.size, bg_corner)).convert("L")
    bbox = diff.point(lambda p: 255 if p > 15 else 0).getbbox()
    if bbox:
        # Dejar un margen blanco limpio alrededor de los módulos del QR (~4.5% del tamaño activo)
        act_w = bbox[2] - bbox[0]
        pad_qr = max(12, int(act_w * 0.045))
        cx0 = max(0, bbox[0] - pad_qr)
        cy0 = max(0, bbox[1] - pad_qr)
        cx1 = min(qr_rgb.width, bbox[2] + pad_qr)
        cy1 = min(qr_rgb.height, bbox[3] + pad_qr)
        qr_cropped = qr_rgb.crop((cx0, cy0, cx1, cy1))
    else:
        qr_cropped = qr_rgb

    if qr_size is not None and qr_size > 0:
        target_side = max(60, int(gw * (float(qr_size) / 100.0)))
    else:
        inset = max(8, int(min(qw, qh) * 0.038))
        target_qw = max(50, qw - inset * 2)
        target_qh = max(50, qh - inset * 2)
        target_side = min(target_qw, target_qh)

    qr_resized = qr_cropped.resize((target_side, target_side), Image.Resampling.LANCZOS)

    if qr_x is not None:
        paste_qx = int(gw * (float(qr_x) / 100.0) - target_side / 2.0)
    else:
        paste_qx = qx + (qw - target_side) // 2

    if qr_y is not None:
        paste_qy = int(gh * (float(qr_y) / 100.0) - target_side / 2.0)
    else:
        paste_qy = qy + (qh - target_side) // 2

    # Máscara suave en las esquinas exteriores del margen blanco para adaptarse a recuadros redondeados
    corner_r = max(4, int(target_side * 0.055))
    qr_mask = Image.new("L", (target_side, target_side), 0)
    ImageDraw.Draw(qr_mask).rounded_rectangle([0, 0, target_side - 1, target_side - 1], radius=corner_r, fill=255)
    gafete.paste(qr_resized, (paste_qx, paste_qy), qr_mask)

    # --- 2. DIBUJAR EL NOMBRE DE LA PERSONA ---
    clean_name = " ".join(full_name.strip().split()).upper()
    if clean_name:
        draw = ImageDraw.Draw(gafete)
        font_candidates = [
            "Montserrat-Bold.ttf",
            "Montserrat-SemiBold.ttf",
            "segoeuib.ttf",
            "calibrib.ttf",
            "arialbd.ttf",
            "DejaVuSans-Bold.ttf"
        ]
        words = clean_name.split()
        # Si el recuadro es muy estilizado/bajo (como en gafetes con franja inferior) mantener 1 línea salvo nombres muy largos
        is_slim_box = (nh / max(1, gw)) < 0.095
        min_chars_wrap = 26 if is_slim_box else 18
        if len(words) >= 3 and len(clean_name) >= min_chars_wrap:
            best_split = 1
            best_diff = 9999
            for i in range(1, len(words)):
                l1 = " ".join(words[:i])
                l2 = " ".join(words[i:])
                diff_len = abs(len(l1) - len(l2))
                if diff_len < best_diff:
                    best_diff = diff_len
                    best_split = i
            lines = [" ".join(words[:best_split]), " ".join(words[best_split:])]
        else:
            lines = [clean_name]

        max_text_w = int(nw * 0.90)
        max_text_h = int(nh * 0.78)
        start_fs = int(nh * (0.36 if len(lines) == 2 else 0.48))
        min_fs = 16

        optimal_fs = start_fs
        for fs in range(start_fs, min_fs - 1, -2):
            f_try = _load_font(font_candidates, fs)
            trk = max(1.0, fs * 0.045)
            line_widths = [_measure_tracked_text(draw, ln, f_try, trk)[0] for ln in lines]
            cap_h = draw.textbbox((0, 0), "H", font=f_try)[3] - draw.textbbox((0, 0), "H", font=f_try)[1]
            line_gap = int(cap_h * 0.34) if len(lines) > 1 else 0
            tot_h = cap_h * len(lines) + line_gap * (len(lines) - 1)
            if max(line_widths) <= max_text_w and tot_h <= max_text_h:
                optimal_fs = fs
                break

        scale_mult = (float(name_size) / 100.0) if (name_size is not None and name_size > 0) else 1.0
        final_fs = max(12, int(optimal_fs * scale_mult))
        font = _load_font(font_candidates, final_fs)
        tracking = max(1.0, final_fs * 0.045)

        line_metrics = [_measure_tracked_text(draw, ln, font, tracking) for ln in lines]
        line_gap = int(line_metrics[0][1] * 0.34) if len(lines) > 1 else 0
        total_h = sum(m[1] for m in line_metrics) + line_gap * (len(lines) - 1)

        center_nx = (gw * (float(name_x) / 100.0)) if name_x is not None else (nx + nw / 2.0)
        center_ny = (gh * (float(name_y) / 100.0)) if name_y is not None else (ny + nh / 2.0)

        curr_y = center_ny - total_h / 2.0
        for idx, ln in enumerate(lines):
            lw, lh = line_metrics[idx]
            lx = center_nx - lw / 2.0
            _draw_tracked_text(draw, (lx, curr_y), ln, font, text_color, tracking)
            curr_y += lh + line_gap

    return gafete


def generate_qr(
    content: str,
    module_color: str = "#000000",
    bg_color: str = "#FFFFFF",
    module_style: str = "dots",
    eye_frame_style: str = "square",
    eye_ball_style: str = "square",
    logo_type: str = "badge_bar",
    logo_path: Optional[str] = None,
    logo_text: str = "",
    badge_line1: str = "Proyecto",
    badge_line2: str = "GEF Bermejo",
    logo_ratio: float = 0.18,
    logo_badge: bool = True,
    box_size: int = 16,
    border: int = 4,
    jaguar_background: bool = False,
    jaguar_opacity: float = 0.28,
    jaguar_image_path: Optional[str] = None,
    eye_ball_image: Optional[str] = None
) -> Image.Image:
    """
    Genera un código QR de alta resolución con estilo personalizado avanzado
    (módulos punteados, ojos estilizados y badge central con barra lateral).
    """
    if not content:
        content = " "

    border = max(4, int(border))
    box_size = max(12, int(box_size))

    # Con logo o insignia central, usamos ERROR_CORRECT_H (30% de recuperación)
    # para garantizar que ningún celular (iPhone o Android) tenga problemas al leer el código.
    # Si no hay logo, usamos ERROR_CORRECT_M para maximizar el tamaño de los módulos.
    has_active_logo = (
        (logo_type == "badge_bar" and (badge_line1.strip() or badge_line2.strip()))
        or (logo_type == "image" and logo_path and os.path.isfile(logo_path))
        or (logo_type == "text" and logo_text.strip())
    )
    if not has_active_logo:
        ec_level = ERROR_CORRECT_M
    else:
        ec_level = ERROR_CORRECT_H

    qr = qrcode.QRCode(
        version=None,
        error_correction=ec_level,
        box_size=box_size,
        border=border
    )
    qr.add_data(content)
    qr.make(fit=True)

    front_rgb = hex_to_rgb(module_color)
    back_rgb  = hex_to_rgb(bg_color)
    if hasattr(qr, "modules") and qr.modules:
        mat = [list(row) for row in qr.modules]
    else:
        mat = qr.get_matrix()
        if border > 0:
            mat = [row[border:-border] for row in mat[border:-border]]

    n = len(mat)
    total_px = (n + border * 2) * box_size
    margin_px = border * box_size
    active_size = max(100, total_px - 2 * margin_px)

    # Calcular área central del logo/insignia para omitir solo módulos cuyo centro cae debajo
    clear_rect = None
    if logo_type == "badge_bar" and (badge_line1.strip() or badge_line2.strip()):
        bw, bh = _compute_sidebar_badge_size(total_px, total_px, badge_line1, badge_line2, logo_ratio, margin_px)
        if bw > 0 and bh > 0:
            bx = (total_px - bw) // 2
            by = (total_px - bh) // 2
            clear_rect = (bx, by, bx + bw, by + bh)
    elif logo_type == "image" and logo_path and os.path.isfile(logo_path):
        try:
            with Image.open(logo_path) as l_img:
                ratio = max(0.11, min(float(logo_ratio), 0.15))
                max_logo_w = int(active_size * ratio * 1.15)
                max_logo_h = int(active_size * ratio * 1.15)
                l_copy = l_img.copy()
                l_copy.thumbnail((max_logo_w, max_logo_h), Image.Resampling.LANCZOS)
                logo_w, logo_h = l_copy.size
                pad = max(6, int(min(logo_w, logo_h) * 0.12)) if logo_badge else 2
                bw, bh = logo_w + pad * 2, logo_h + pad * 2
                bx = (total_px - bw) // 2
                by = (total_px - bh) // 2
                clear_rect = (bx, by, bx + bw, by + bh)
        except Exception:
            pass
    elif logo_type == "text" and logo_text.strip():
        safe_ratio = min(float(logo_ratio), 0.15)
        bw = int(active_size * safe_ratio * 1.15)
        bh = int(active_size * safe_ratio * 0.55)
        bx = (total_px - bw) // 2
        by = (total_px - bh) // 2
        clear_rect = (bx, by, bx + bw, by + bh)

    base_img = render_custom_matrix_qr(
        matrix=mat,
        box_size=box_size,
        border=border,
        body_style=module_style,
        eye_frame_style=eye_frame_style,
        eye_ball_style=eye_ball_style,
        module_color=front_rgb,
        bg_color=back_rgb,
        eye_ball_image=eye_ball_image,
        clear_rect=clear_rect
    )

    if jaguar_background:
        base_img = _apply_jaguar_background(
            base_img, front_rgb, back_rgb, margin_px, jaguar_opacity,
            jaguar_image_path, len(mat), matrix=mat
        )

    if logo_type == "badge_bar":
        base_img = _apply_sidebar_badge(
            base_img,
            line1=badge_line1,
            line2=badge_line2,
            text_color=front_rgb,
            badge_bg=back_rgb,
            max_ratio=logo_ratio,
            margin_px=margin_px
        )
    elif logo_type == "image" and logo_path and os.path.isfile(logo_path):
        base_img = _apply_image_logo(
            base_img,
            logo_path=logo_path,
            max_ratio=logo_ratio,
            draw_badge=logo_badge,
            badge_bg=back_rgb,
            margin_px=margin_px
        )
    elif logo_type == "text" and logo_text.strip():
        base_img = _apply_text_badge(
            base_img,
            text=logo_text.strip(),
            max_ratio=logo_ratio,
            text_color=front_rgb,
            badge_bg=back_rgb,
            margin_px=margin_px
        )

    return base_img


def _normalize_col_key(k: str) -> str:
    """Quita tildes, espacios y caracteres especiales para comparación de columnas."""
    k = str(k).lower().strip()
    for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n"), ("°", ""), ("º", ""), (" ", "")]:
        k = k.replace(a, b)
    return re.sub(r"[^a-z0-9]", "", k)


def _load_batch_rows(file_path: str) -> Tuple[list, list]:
    """
    Lee un archivo Excel (.xlsx, .xls) o CSV (.csv) detectando automáticamente
    la fila de encabezados real (incluso si hay títulos o filas vacías arriba)
    y filtra filas completamente vacías.
    Retorna (columns, rows).
    """
    ext = os.path.splitext(file_path)[1].lower()
    known_headers = {
        "nombre", "nombres", "nombrecompleto", "participante", "asistente",
        "apellido", "apellidos", "institucion", "organizacion", "empresa",
        "cargo", "puesto", "rol", "correo", "email", "telefono", "celular",
        "lugar", "sede", "lugarosede", "notas", "dni", "ci", "cedula"
    }

    if ext in [".xlsx", ".xls"]:
        try:
            import pandas as pd
        except ImportError:
            raise RuntimeError("Se requiere 'pandas' y 'openpyxl' para procesar archivos Excel.")

        raw_df = pd.read_excel(file_path, header=None, dtype=str).fillna("")
        if raw_df.empty:
            return [], []

        header_idx = 0
        best_score = -1
        for r_idx in range(min(10, len(raw_df))):
            row_vals = [str(v).strip() for v in raw_df.iloc[r_idx].tolist()]
            non_empty = [v for v in row_vals if v and v.lower() not in ["nan", "none"]]
            if not non_empty:
                continue
            score = sum(
                1 for v in non_empty
                if _normalize_col_key(v) in known_headers
                or any(kh in _normalize_col_key(v) for kh in ("nombre", "institucion", "cargo", "correo", "telefono"))
            )
            if score > best_score:
                best_score = score
                header_idx = r_idx
            if score >= 2:
                break

        headers = []
        for c_idx, val in enumerate(raw_df.iloc[header_idx].tolist()):
            h_str = str(val).strip()
            if not h_str or h_str.lower() in ["nan", "none"]:
                h_str = f"unnamed_{c_idx}"
            headers.append(h_str)

        data_df = raw_df.iloc[header_idx + 1:].copy()
        data_df.columns = headers
        columns = [c for c in headers if not c.lower().startswith("unnamed")]

        rows = []
        for _, s_row in data_df.iterrows():
            row_dict = {str(k): str(v).strip() for k, v in s_row.items()}
            if any(v and v.lower() not in ["nan", "none"] for k, v in row_dict.items() if not k.lower().startswith("unnamed")):
                rows.append(row_dict)
        return columns, rows

    elif ext == ".csv":
        content_text = None
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                with open(file_path, mode="r", encoding=enc) as f:
                    content_text = f.read()
                break
            except UnicodeDecodeError:
                continue
        if content_text is None:
            with open(file_path, mode="r", encoding="utf-8", errors="replace") as f:
                content_text = f.read()

        import io
        sample = content_text[:4096]
        delimiter = ","
        try:
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample, delimiters=",;\t|").delimiter
        except Exception:
            if sample.count(";") > sample.count(","):
                delimiter = ";"

        all_rows = list(csv.reader(io.StringIO(content_text), delimiter=delimiter))
        if not all_rows:
            return [], []

        header_idx = 0
        for r_idx in range(min(10, len(all_rows))):
            row_vals = [str(v).strip() for v in all_rows[r_idx]]
            score = sum(
                1 for v in row_vals
                if _normalize_col_key(v) in known_headers
                or any(kh in _normalize_col_key(v) for kh in ("nombre", "institucion", "cargo", "correo", "telefono"))
            )
            if score >= 2:
                header_idx = r_idx
                break

        raw_headers = all_rows[header_idx]
        headers = [
            str(h).strip() if str(h).strip() else f"unnamed_{i}"
            for i, h in enumerate(raw_headers)
        ]
        columns = [c for c in headers if not c.lower().startswith("unnamed")]

        rows = []
        for r_vals in all_rows[header_idx + 1:]:
            if not any(str(v).strip() for v in r_vals):
                continue
            row_dict = {}
            for i, h in enumerate(headers):
                row_dict[h] = str(r_vals[i]).strip() if i < len(r_vals) else ""
            if any(v for k, v in row_dict.items() if not k.lower().startswith("unnamed")):
                rows.append(row_dict)
        return columns, rows

    else:
        raise ValueError("Formato no soportado. Debe ser archivo .xlsx, .xls o .csv")


def inspect_batch_file(file_path: str) -> Dict[str, Any]:
    """
    Inspecciona previamente un archivo Excel o CSV para mostrar estadísticas
    y columnas detectadas antes de generar los códigos QR.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"No se encontró el archivo: {file_path}")

    columns, rows = _load_batch_rows(file_path)

    return {
        "total_rows": len(rows),
        "columns": columns,
        "filename": os.path.basename(file_path)
    }


def process_batch(
    file_path: str,
    output_dir: str,
    format_type: str = "plain",           # 'plain' por defecto (texto legible)
    qr_options: Optional[Dict[str, Any]] = None,
    filename_style: str = "clean",        # "clean" = nombre de persona.png
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Dict[str, Any]:
    """
    Lee un archivo Excel (.xlsx, .xls) o CSV (.csv) y genera los códigos QR por lote.

    Detecta automáticamente columnas comunes de eventos:
    - Nombre / Nombres / Participante / Nombre Completo
    - Apellidos (opcional, si hay columna separada)
    - Institución / Empresa / Organización
    - Cargo / Rol / Mesa / Categoría
    - Correo / Email
    - Teléfono / Celular / WhatsApp
    - Lugar o Sede / Sede / Lugar
    - Notas / DNI / CI / N° adicionales
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"No se encontró el archivo: {file_path}")

    os.makedirs(output_dir, exist_ok=True)
    qr_options = dict(qr_options or {})

    _, rows = _load_batch_rows(file_path)

    total   = len(rows)
    success = 0
    errors  = []
    used_filenames = set()

    # --- Listas de candidatos para detección automática de columnas ---
    candidates_first_name = [
        "nombrecompleto", "nombreyapellido", "nombreapellidos", "nombresyapellidos",
        "nombreapellido", "participante", "asistente", "invitado", "persona",
        "nombres", "nombre", "firstname", "fullname", "name"
    ]
    candidates_last_name = ["apellidos", "apellido", "lastname", "surname"]
    candidates_org = [
        "institucion", "organizacion", "empresa", "entidad",
        "compania", "company", "dependencia", "unidad", "org"
    ]
    candidates_title = [
        "cargo", "puesto", "funcion", "profesion", "ocupacion",
        "categoria", "title", "job", "mesa", "sector", "rol"
    ]
    candidates_email = ["correoelectronico", "correo", "email", "mail", "emailaddress"]
    candidates_phone = ["telefono", "celular", "whatsapp", "movil", "phone", "tel", "contacto"]
    candidates_location = [
        "lugarosede", "lugarsede", "lugar", "sede", "municipio",
        "ciudad", "region", "departamento", "ubicacion", "direccion", "location"
    ]
    candidates_notes = [
        "notas", "nota", "detalles", "notes", "observaciones",
        "dni", "ci", "cedula", "carnet", "ticket", "id", "nro", "numero", "num", "n"
    ]

    # Columnas que siempre se ignoran (no aportan datos de contacto)
    SKIP_COLUMNS_KEYWORDS = ["unnamed", "qr"]

    def should_skip_col(col_name: str) -> bool:
        """Retorna True si la columna debe ignorarse completamente."""
        cl = col_name.lower().strip()
        if cl.startswith("unnamed"):
            return True
        norm = _normalize_col_key(cl)
        if norm in SKIP_COLUMNS_KEYWORDS or "codigoqr" in norm:
            return True
        return False

    def find_val(row_dict: Dict[str, Any], candidates: list, used_cols: set) -> Tuple[str, Optional[str]]:
        """
        Busca en el diccionario de fila el primer campo no usado que coincida
        con alguno de los candidatos (primero coincidencia exacta, luego subcadena segura).
        """
        # Paso 1: Coincidencia exacta normalizada
        for c in candidates:
            c_norm = _normalize_col_key(c)
            for k, v in row_dict.items():
                if not k or str(k) in used_cols or should_skip_col(str(k)):
                    continue
                if _normalize_col_key(str(k)) == c_norm:
                    val = str(v).strip()
                    if val and val.lower() not in ["nan", "none", ""]:
                        return val, str(k)

        # Paso 2: Coincidencia parcial solo para palabras clave de longitud >= 4
        # (evita falsos positivos como 'ci' dentro de 'institucion' o 'id' en 'apellido')
        for c in candidates:
            c_norm = _normalize_col_key(c)
            if len(c_norm) < 4:
                continue
            for k, v in row_dict.items():
                if not k or str(k) in used_cols or should_skip_col(str(k)):
                    continue
                clean_k = _normalize_col_key(str(k))
                if c_norm in clean_k:
                    val = str(v).strip()
                    if val and val.lower() not in ["nan", "none", ""]:
                        return val, str(k)

        return "", None

    for idx, row in enumerate(rows, start=1):
        try:
            used_keys = set()

            fn, k_fn = find_val(row, candidates_first_name, used_keys)
            if k_fn:
                used_keys.add(k_fn)

            ln, k_ln = find_val(row, candidates_last_name, used_keys)
            if k_ln:
                used_keys.add(k_ln)

            org, k_org = find_val(row, candidates_org, used_keys)
            if k_org:
                used_keys.add(k_org)

            title, k_title = find_val(row, candidates_title, used_keys)
            if k_title:
                used_keys.add(k_title)

            email, k_email = find_val(row, candidates_email, used_keys)
            if k_email:
                used_keys.add(k_email)

            phone, k_phone = find_val(row, candidates_phone, used_keys)
            if k_phone:
                used_keys.add(k_phone)

            location, k_loc = find_val(row, candidates_location, used_keys)
            if k_loc:
                used_keys.add(k_loc)

            notes, k_notes = find_val(row, candidates_notes, used_keys)
            if k_notes:
                used_keys.add(k_notes)
                if _normalize_col_key(k_notes) in ("n", "nro", "num", "numero"):
                    notes = f"N° {notes}"

            # Recoger cualquier otra columna con datos que no haya coincidido
            extra_parts = []
            for k, v in row.items():
                if not k or str(k) in used_keys or should_skip_col(str(k)):
                    continue
                val = str(v).strip()
                if val and val.lower() not in ["nan", "none", ""]:
                    if not fn:
                        fn = val
                        used_keys.add(str(k))
                    else:
                        extra_parts.append(f"{str(k).strip()}: {val}")

            if extra_parts:
                extra_str = " | ".join(extra_parts)
                notes = f"{notes} | {extra_str}" if notes else extra_str

            # Si el nombre viene completo (sin columna de apellido separada),
            # NO dividir — usarlo tal cual para conservar el nombre completo real.
            full_name_combined = f"{fn} {ln}".strip()

            data = {
                "first_name": fn,
                "last_name":  ln,
                "org":        org,
                "title":      title,
                "email":      email,
                "phone":      phone,
                "location":   location,
                "notes":      notes,
            }

            content = format_contact_data(data, format_type=format_type)

            # --- Nombre del archivo: persona completa ---
            safe_name = re.sub(r"[^\w\s-]", "", full_name_combined).strip()
            safe_name = re.sub(r"\s+", "_", safe_name)
            if not safe_name:
                safe_name = f"asistente_{idx:03d}"

            if filename_style == "numbered":
                base_file_name = f"{idx:03d}_{safe_name}"
            else:
                base_file_name = safe_name

            file_name = f"{base_file_name}.png"
            if file_name.lower() in used_filenames:
                file_name = f"{base_file_name}_{idx:03d}.png"
            used_filenames.add(file_name.lower())

            dest_path = os.path.join(output_dir, file_name)

            # Generar QR
            gen_opts = dict(qr_options)
            use_gafete = bool(gen_opts.pop("use_gafete", False))
            gafete_path = gen_opts.pop("gafete_path", None)
            gafete_qr_x = gen_opts.pop("gafete_qr_x", None)
            gafete_qr_y = gen_opts.pop("gafete_qr_y", None)
            gafete_qr_size = gen_opts.pop("gafete_qr_size", None)
            gafete_name_x = gen_opts.pop("gafete_name_x", None)
            gafete_name_y = gen_opts.pop("gafete_name_y", None)
            gafete_name_size = gen_opts.pop("gafete_name_size", None)
            img = generate_qr(content, **gen_opts)

            bg_rgb = hex_to_rgb(qr_options.get("bg_color", "#FFFFFF"))
            fg_rgb = hex_to_rgb(qr_options.get("module_color", "#000000"))
            if use_gafete:
                img = compose_gafete_image(
                    img,
                    full_name=full_name_combined,
                    gafete_path=gafete_path,
                    text_color=fg_rgb,
                    qr_x=gafete_qr_x,
                    qr_y=gafete_qr_y,
                    qr_size=gafete_qr_size,
                    name_x=gafete_name_x,
                    name_y=gafete_name_y,
                    name_size=gafete_name_size,
                )
            else:
                # Añadir el nombre DEBAJO del QR en letras grandes y mayúsculas
                img = add_name_label_below_qr(
                    img,
                    full_name=full_name_combined,
                    bg_color=bg_rgb,
                    text_color=fg_rgb
                )

            img.save(dest_path, "PNG")
            success += 1

            if progress_callback:
                progress_callback(idx, total, f"Generado: {file_name}")

        except Exception as ex:
            errors.append(f"Fila {idx}: {str(ex)}")
            if progress_callback:
                progress_callback(idx, total, f"Error en fila {idx}")

    return {
        "total":   total,
        "success": success,
        "failed":  len(errors),
        "errors":  errors
    }
