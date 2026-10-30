"""
ISYARA - Presentation Materials Generator (X-Banner & Folded Poster)
Lomba: AITC UNAIR 2026 (Airlangga Information Technology Competition)
Tim: SMK Telkom

Outputs:
1. x_banner_isyara.png (1701 x 4535 px, standard 60x160cm X-Banner ratio)
2. poster_lipat_luar.png (3508 x 2480 px, standard A4 Landscape Trifold Outside)
3. poster_lipat_dalam.png (3508 x 2480 px, standard A4 Landscape Trifold Inside)
4. poster_lipat_isyara_printable.pdf (Two-page printable PDF)
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DESIGN_3D_DIR = os.path.join(BASE_DIR, "docs", "3d_design")
OUT_DIR = os.path.join(BASE_DIR, "docs", "presentation")
os.makedirs(OUT_DIR, exist_ok=True)

# Fonts
FONTS_DIR = r"C:\Windows\Fonts"
FONT_BOLD = os.path.join(FONTS_DIR, "segoeuib.ttf")
FONT_REGULAR = os.path.join(FONTS_DIR, "segoeui.ttf")
FONT_SEMIBOLD = os.path.join(FONTS_DIR, "segoeui.ttf")
if not os.path.exists(FONT_BOLD):
    FONT_BOLD = os.path.join(FONTS_DIR, "arialbd.ttf")
    FONT_REGULAR = os.path.join(FONTS_DIR, "arial.ttf")

def get_font(size, bold=False):
    path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

# Color Palette
BG_DARK = (10, 15, 26)          # #0a0f1a Deep navy dark
BG_CARD = (19, 28, 48, 220)      # Translucent card fill
BORDER_CYAN = (56, 189, 248, 180) # #38bdf8 Glow cyan
BORDER_DIM = (148, 163, 184, 50) # Subtle slate
TEXT_WHITE = (248, 250, 252)     # #f8fafc Pure white
TEXT_MUTED = (148, 163, 184)     # #94a3b8 Slate text
TEXT_CYAN = (56, 189, 248)       # #38bdf8 Cyan
TEXT_EMERALD = (52, 211, 153)    # #34d399 Emerald
TEXT_AMBER = (251, 191, 36)      # #fbbf24 Amber
BADGE_BG_BLUE = (3, 105, 161)    # Deep cyan
BADGE_BG_EMERALD = (6, 95, 70)   # Deep green
BADGE_BG_PURPLE = (88, 28, 135)  # Deep purple

def draw_gradient_background(w, h, top_color, bottom_color, glow_points=None):
    """Draws vertical gradient with optional glowing accent orbs."""
    base = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    draw = ImageDraw.Draw(base)
    
    # Linear gradient interpolation
    for y in range(h):
        factor = y / float(h)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * factor)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * factor)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * factor)
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))
        
    if glow_points:
        glow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glow_layer)
        for gx, gy, radius, color in glow_points:
            bbox = [gx - radius, gy - radius, gx + radius, gy + radius]
            g_draw.ellipse(bbox, fill=color)
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=int(radius * 0.45)))
        base = Image.alpha_composite(base, glow_layer)
        
    return base

def draw_pill_badge(draw, x, y, text, font, bg_color, text_color, pad_x=24, pad_y=10):
    """Draw a pill-shaped badge and return bounding box."""
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    w = tw + pad_x * 2
    h = th + pad_y * 2
    r = h // 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=bg_color, outline=BORDER_CYAN, width=1)
    # text vertical centering adjustment
    ty = y + (h - th) // 2 - bbox[1]
    draw.text((x + pad_x, ty), text, font=font, fill=text_color)
    return x + w, y + h

def draw_card(img, bbox, fill_color, border_color=(56, 189, 248, 100), radius=24, border_width=2):
    """Draws a glassmorphism card on an RGBA image."""
    card_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(card_layer)
    d.rounded_rectangle(bbox, radius=radius, fill=fill_color, outline=border_color, width=border_width)
    return Image.alpha_composite(img, card_layer)

def place_rounded_image(base_img, img_path, target_bbox, radius=20, border_color=BORDER_CYAN, border_width=2):
    """Crop, resize, round corners, and paste an image into target bounding box."""
    if not os.path.exists(img_path):
        return base_img
    
    with Image.open(img_path) as src:
        src = src.convert("RGBA")
        bw = target_bbox[2] - target_bbox[0]
        bh = target_bbox[3] - target_bbox[1]
        
        # Fit image maintaining aspect ratio (fit within bbox)
        src_fitted = ImageOps.fit(src, (bw, bh), Image.Resampling.LANCZOS)
        
        # Mask with rounded rectangle
        mask = Image.new("L", (bw, bh), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, bw, bh], radius=radius, fill=255)
        
        # Paste with mask
        base_img.paste(src_fitted, (target_bbox[0], target_bbox[1]), mask)
        
        # Draw border
        draw = ImageDraw.Draw(base_img)
        draw.rounded_rectangle(target_bbox, radius=radius, outline=border_color, width=border_width)
        
    return base_img

def wrap_text(text, font, max_width):
    """Splits text into lines that fit within max_width."""
    words = text.split(" ")
    lines = []
    current_line = []
    for w in words:
        test_line = " ".join(current_line + [w])
        bbox = font.getbbox(test_line)
        if (bbox[2] - bbox[0]) <= max_width:
            current_line.append(w)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [w]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

# ==============================================================================
# 1. X-BANNER DESIGN (1701 x 4535 px)
# ==============================================================================
def generate_x_banner():
    print("\n--- Generating X-Banner (1701 x 4535 px) ---")
    W, H = 1701, 4535
    
    # 1. Background gradient with glowing cyan/sapphire orbs
    glows = [
        (300, 400, 350, (6, 182, 212, 60)),     # Top-left cyan glow
        (1400, 1100, 450, (59, 130, 246, 70)),  # Hero right blue glow
        (350, 2200, 400, (16, 185, 129, 45)),   # Feature emerald glow
        (1350, 3400, 400, (139, 92, 246, 50)),  # Tech purple glow
        (850, 4300, 350, (6, 182, 212, 50))     # Footer cyan glow
    ]
    banner = draw_gradient_background(W, H, (10, 16, 30), (5, 8, 16), glows)
    draw = ImageDraw.Draw(banner)
    
    # Top Margin & Header
    # Competition & School Tags
    draw_pill_badge(draw, 100, 120, "🏆 AITC UNAIR 2026", get_font(34, True), (30, 58, 138, 220), TEXT_WHITE, 30, 12)
    draw_pill_badge(draw, 570, 120, "🏫 SMK TELKOM", get_font(34, True), (15, 23, 42, 220), (56, 189, 248), 30, 12)
    draw_pill_badge(draw, 1000, 120, "💡 INOVASI IoT & AI", get_font(34, True), (6, 78, 59, 220), (52, 211, 153), 30, 12)
    
    # Title: ISYARA
    font_title = get_font(180, True)
    draw.text((100, 210), "ISYARA", font=font_title, fill=TEXT_WHITE)
    
    # Subtitle / Tagline
    font_sub = get_font(46, True)
    draw.text((100, 420), "Smart Assistive Device 2-in-1", font=font_sub, fill=TEXT_CYAN)
    
    font_desc = get_font(36, False)
    tagline_lines = [
        "Inovasi Asisten Komunikasi Inklusif Terpadu 2-Arah",
        "Menghubungkan Teman Tuli (BISINDO) & Teman Netra (Braille)"
    ]
    draw.text((100, 490), tagline_lines[0], font=font_desc, fill=TEXT_WHITE)
    draw.text((100, 545), tagline_lines[1], font=font_desc, fill=TEXT_MUTED)
    
    # Divider line
    draw.line([(100, 630), (W - 100, 630)], fill=(56, 189, 248, 120), width=3)
    
    # -------------------------------------------------------------------------
    # HERO SECTION: 3D Product Showcase (Y: 670 - 1650)
    # -------------------------------------------------------------------------
    hero_card_bbox = [100, 670, W - 100, 1620]
    banner = draw_card(banner, hero_card_bbox, (15, 23, 42, 180), BORDER_CYAN, radius=32, border_width=3)
    draw = ImageDraw.Draw(banner)
    
    # Hero Title
    draw.text((150, 710), "✨ PROTOTYPE REVOLUSIONER BERBASIS ON-DEVICE TINYML", font=get_font(32, True), fill=TEXT_EMERALD)
    
    # Paste Hero Image (Dual Shot / Assembled)
    hero_img_path = os.path.join(DESIGN_3D_DIR, "03_hero_shot_dual.jpg")
    banner = place_rounded_image(banner, hero_img_path, [150, 770, W - 150, 1450], radius=24, border_color=(56, 189, 248, 180), border_width=2)
    draw = ImageDraw.Draw(banner)
    
    # Hero Callouts / Badges under image
    callouts = [
        ("📷 Vision AI", "Kamera ESP32-CAM OV3660"),
        ("⚡ 100% Offline", "Nol Latensi & Tanpa Internet"),
        ("⌨️ 16-Button Braille", "Layout Sel 2x3 Ergonomis"),
        ("🔊 Natural Voice", "Azure Neural Speech TTS")
    ]
    card_w = (W - 300 - 30 * 3) // 4
    for i, (head, desc) in enumerate(callouts):
        cx = 150 + i * (card_w + 30)
        cy = 1475
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + 115], radius=16, fill=(30, 41, 59, 200), outline=BORDER_DIM, width=1)
        draw.text((cx + 18, cy + 16), head, font=get_font(26, True), fill=TEXT_CYAN)
        draw.text((cx + 18, cy + 62), desc, font=get_font(20, False), fill=TEXT_WHITE)
        
    # -------------------------------------------------------------------------
    # PROBLEM & SOLUTION SECTION (Y: 1670 - 2220)
    # -------------------------------------------------------------------------
    prob_bbox = [100, 1670, W - 100, 2220]
    banner = draw_card(banner, prob_bbox, (15, 23, 42, 180), BORDER_DIM, radius=30, border_width=2)
    draw = ImageDraw.Draw(banner)
    
    draw.text((150, 1715), "🎯 LATAR BELAKANG & MASALAH SOSIAL", font=get_font(42, True), fill=TEXT_AMBER)
    draw.text((150, 1775), "Menjawab tantangan nyata komunikasi inklusif di Indonesia", font=get_font(30, False), fill=TEXT_MUTED)
    
    # 2 Comparison Columns: Tantangan vs Solusi ISYARA
    col_w = (W - 300 - 40) // 2
    # Left: Tantangan
    draw.rounded_rectangle([150, 1835, 150 + col_w, 2175], radius=20, fill=(239, 68, 68, 25), outline=(239, 68, 68, 120), width=2)
    draw.text((180, 1865), "❌ Hambatan Komunikasi Konvensional", font=get_font(32, True), fill=(248, 113, 113))
    issues = [
        "• Masyarakat umum kesulitan memahami Bahasa Isyarat (BISINDO).",
        "• Teman Netra kesulitan membaca teks visual tanpa huruf Braille.",
        "• Komunikasi langsung Tuli ⟷ Netra selama ini mustahil tanpa perantara.",
        "• Aplikasi HP membutuhkan internet stabil & rawan gangguan privasi."
    ]
    for idx, iss in enumerate(issues):
        lines = wrap_text(iss, get_font(26, False), col_w - 60)
        draw.text((180, 1925 + idx * 60), lines[0], font=get_font(26, False), fill=TEXT_WHITE)
        if len(lines) > 1:
            draw.text((200, 1955 + idx * 60), lines[1], font=get_font(26, False), fill=TEXT_WHITE)

    # Right: Solusi ISYARA
    rx = 150 + col_w + 40
    draw.rounded_rectangle([rx, 1835, rx + col_w, 2175], radius=20, fill=(16, 185, 129, 25), outline=(16, 185, 129, 120), width=2)
    draw.text((rx + 30, 1865), "✅ Solusi Cerdas Perangkat ISYARA", font=get_font(32, True), fill=(52, 211, 153))
    solutions = [
        "• Deteksi Bahasa Isyarat otomatis via AI Kamera ➔ Teks & Suara instan.",
        "• Keyboard Braille taktil 16-tombol ➔ Output teks visual & suara.",
        "• Komunikasi 2-Arah langsung antar sesama difabel & masyarakat umum.",
        "• 100% On-Device TinyML: portabel, hemat daya, dan bebas internet."
    ]
    for idx, sol in enumerate(solutions):
        lines = wrap_text(sol, get_font(26, False), col_w - 60)
        draw.text((rx + 30, 1925 + idx * 60), lines[0], font=get_font(26, False), fill=TEXT_WHITE)
        if len(lines) > 1:
            draw.text((rx + 50, 1955 + idx * 60), lines[1], font=get_font(26, False), fill=TEXT_WHITE)

    # -------------------------------------------------------------------------
    # DUAL-MODE CORE FEATURES (Y: 2270 - 3220)
    # -------------------------------------------------------------------------
    draw.text((100, 2270), "⚡ DUA MODE UTAMA: KOMUNIKASI TANPA BATAS", font=get_font(46, True), fill=TEXT_WHITE)
    draw.text((100, 2335), "Dua antarmuka fisik yang dirancang khusus untuk kenyamanan setiap pengguna", font=get_font(30, False), fill=TEXT_CYAN)
    
    mode_box_h = 800
    m_w = (W - 200 - 40) // 2
    
    # Mode 1 Card (Vision AI)
    m1_bbox = [100, 2390, 100 + m_w, 2390 + mode_box_h]
    banner = draw_card(banner, m1_bbox, (15, 23, 42, 200), (6, 182, 212, 140), radius=28, border_width=2)
    # Put Front Camera image
    img_front_path = os.path.join(DESIGN_3D_DIR, "02_sisi_depan_kamera_speaker.jpg")
    banner = place_rounded_image(banner, img_front_path, [130, 2420, 100 + m_w - 30, 2800], radius=20, border_color=BORDER_CYAN)
    draw = ImageDraw.Draw(banner)
    
    draw.text((140, 2830), "MODE 1: PENERJEMAH ISYARAT BISINDO", font=get_font(34, True), fill=TEXT_CYAN)
    draw.text((140, 2875), "Ditujukan untuk Teman Tuli berbicara ke Lawan Bicara", font=get_font(26, True), fill=TEXT_MUTED)
    m1_points = [
        "1. Kamera Depan (ESP32-CAM) menangkap pose tangan 96x96 Grayscale.",
        "2. AI TinyML di ESP32-S3 memprediksi huruf A-Z & kata penuh.",
        "3. Anti False-Positive: Filter kontras dinamis & hold-to-type 1.2s.",
        "4. Speaker internal membacakan kata dengan suara jernih alami."
    ]
    for idx, pt in enumerate(m1_points):
        draw.text((140, 2930 + idx * 55), pt, font=get_font(24, False), fill=TEXT_WHITE)

    # Mode 2 Card (Braille Keypad)
    m2_bbox = [100 + m_w + 40, 2390, W - 100, 2390 + mode_box_h]
    banner = draw_card(banner, m2_bbox, (15, 23, 42, 200), (16, 185, 129, 140), radius=28, border_width=2)
    # Put Back Shell / User image
    img_back_path = os.path.join(DESIGN_3D_DIR, "01_sisi_user_belakang.jpg")
    banner = place_rounded_image(banner, img_back_path, [100 + m_w + 70, 2420, W - 130, 2800], radius=20, border_color=(52, 211, 153))
    draw = ImageDraw.Draw(banner)
    
    draw.text((100 + m_w + 70, 2830), "MODE 2: KEYBOARD BRAILLE 16-TOMBOL", font=get_font(34, True), fill=TEXT_EMERALD)
    draw.text((100 + m_w + 70, 2875), "Ditujukan untuk Teman Netra mengetik pesan mandiri", font=get_font(26, True), fill=TEXT_MUTED)
    m2_points = [
        "1. Grid 4x4 Taktil: 6 tombol tengah membentuk 1 Sel Braille (Titik 1-6).",
        "2. Standar Braille Grade 1: Mendukung huruf alfabet, angka, dan spasi.",
        "3. Dual Display: Layar OLED menampilkan teks kalimat & titik Braille.",
        "4. Tombol TTS Instan (S16) untuk membacakan seluruh kalimat tersusun."
    ]
    for idx, pt in enumerate(m2_points):
        draw.text((100 + m_w + 70, 2930 + idx * 55), pt, font=get_font(24, False), fill=TEXT_WHITE)

    # -------------------------------------------------------------------------
    # HARDWARE & SYSTEM ARCHITECTURE (Y: 3260 - 4020)
    # -------------------------------------------------------------------------
    arch_bbox = [100, 3260, W - 100, 4020]
    banner = draw_card(banner, arch_bbox, (15, 23, 42, 200), BORDER_DIM, radius=30, border_width=2)
    
    # Internal Exploded View Image placed on the right
    exp_img_path = os.path.join(DESIGN_3D_DIR, "04_exploded_internal_view.jpg")
    banner = place_rounded_image(banner, exp_img_path, [W - 680, 3300, W - 140, 3980], radius=20, border_color=BORDER_CYAN)
    draw = ImageDraw.Draw(banner)
    
    draw.text((150, 3300), "⚙️ ARSITEKTUR SISTEM & SPESIFIKASI TEKNIS", font=get_font(42, True), fill=TEXT_WHITE)
    draw.text((150, 3360), "Efisiensi tinggi dengan skema Master-Slave Microcontroller", font=get_font(28, False), fill=TEXT_CYAN)
    
    specs = [
        ("Otak Utama (Master)", "ESP32-S3 Dual-Core 240MHz, 16MB Flash, 8MB PSRAM"),
        ("Sensor Kamera (Slave)", "ESP32-CAM OV3660 3MP Grayscale via UART 460800 baud"),
        ("Framework AI", "Edge Impulse TinyML / TensorFlow Lite Micro (96x96 MobileNet)"),
        ("Layar Ganda (Dual Display)", "OLED 0.96\" I2C (Teks) + TFT LCD 1.77\" SPI (Live Viewfinder)"),
        ("Input Keyboard", "16-Button Tactile Matrix (Debounce Independen Hardware)"),
        ("Output Audio", "DFPlayer Mini + 3W High Clarity Speaker (Azure Neural Voice)"),
        ("Dimensi & Casing", "76 x 150 x 22.4 mm, 3D Print PLA Matte Ergonomis (~85g)"),
        ("Manajemen Daya", "LiPo 3.7V Rechargeable via USB-C + Switch Hard Cut 0mA")
    ]
    
    for i, (k, v) in enumerate(specs):
        sy = 3430 + i * 68
        draw.text((150, sy), f"• {k}:", font=get_font(26, True), fill=TEXT_CYAN)
        draw.text((500, sy), v, font=get_font(24, False), fill=TEXT_WHITE)
        
    # -------------------------------------------------------------------------
    # FOOTER: Competition & Team Info (Y: 4070 - 4450)
    # -------------------------------------------------------------------------
    footer_bbox = [100, 4070, W - 100, 4450]
    banner = draw_card(banner, footer_bbox, (30, 41, 59, 220), BORDER_CYAN, radius=24, border_width=2)
    draw = ImageDraw.Draw(banner)
    
    draw.text((160, 4110), "🏆 AIRLANGGA INFORMATION TECHNOLOGY COMPETITION (AITC) 2026", font=get_font(34, True), fill=TEXT_AMBER)
    draw.text((160, 4165), "Universitas Airlangga — Kategori: Inovasi Perangkat Keras / IoT & AI Inklusif", font=get_font(28, False), fill=TEXT_WHITE)
    
    draw.line([(160, 4230), (W - 160, 4230)], fill=BORDER_DIM, width=2)
    
    draw.text((160, 4260), "👥 KARYA TIM SISWA SMK TELKOM", font=get_font(32, True), fill=TEXT_CYAN)
    draw.text((160, 4315), "Alat Bantu Mandiri Ramah Difabel: 'Menembus Batas Sunyi, Menghubungkan Cahaya'", font=get_font(26, False), fill=TEXT_MUTED)
    draw.text((160, 4365), "Project Repository: github.com/Diocta/ISYARA | 100% Open Source Innovation", font=get_font(24, True), fill=TEXT_EMERALD)
    
    # Save Image
    out_file = os.path.join(OUT_DIR, "x_banner_isyara.png")
    banner = banner.convert("RGB")
    banner.save(out_file, "PNG", quality=95)
    print(f"Saved X-Banner: {out_file} ({os.path.getsize(out_file):,} bytes)")
    return out_file

# ==============================================================================
# 2. POSTER LIPAT (TRIFOLD BROCHURE) (A4 Landscape 3508 x 2480 px)
# ==============================================================================
def generate_folded_poster():
    print("\n--- Generating Folded Poster (Trifold A4 Landscape: 3508 x 2480 px) ---")
    W, H = 3508, 2480
    panel_w = W // 3  # ~1169 px per panel
    
    # -------------------------------------------------------------------------
    # SIDE 1: HALAMAN LUAR (Cover, Back, Flap)
    # Panel 0: Inside Flap (Lipatan Dalam)
    # Panel 1: Back Cover (Halaman Belakang / Kontak & Tim)
    # Panel 2: Front Cover (Cover Depan Utama)
    # -------------------------------------------------------------------------
    glows_out = [
        (panel_w // 2, H // 2, 400, (6, 182, 212, 50)),
        (panel_w + panel_w // 2, H // 2, 400, (59, 130, 246, 50)),
        (panel_w * 2 + panel_w // 2, H // 2, 450, (16, 185, 129, 60))
    ]
    outside = draw_gradient_background(W, H, (10, 16, 28), (6, 10, 18), glows_out)
    draw_out = ImageDraw.Draw(outside)
    
    # Fold Guide Lines (Dotted subtle line to indicate folding)
    for fx in [panel_w, panel_w * 2]:
        for y in range(0, H, 30):
            draw_out.line([(fx, y), (fx, y + 15)], fill=(148, 163, 184, 80), width=2)
            
    # --- PANEL 0 (LEFT): INSIDE FLAP (Mengapa ISYARA?) ---
    p0_x = 60
    draw_pill_badge(draw_out, p0_x, 80, "💡 TENTANG ISYARA", get_font(26, True), (30, 58, 138, 200), TEXT_WHITE, 24, 8)
    draw_out.text((p0_x, 150), "Mengapa Inovasi Ini\nSangat Dibutuhkan?", font=get_font(48, True), fill=TEXT_WHITE)
    
    card_flap_bbox = [p0_x, 300, panel_w - 60, H - 100]
    outside = draw_card(outside, card_flap_bbox, (15, 23, 42, 200), BORDER_DIM, radius=24, border_width=2)
    draw_out = ImageDraw.Draw(outside)
    
    flap_texts = [
        ("🌍 Tantangan Inklusi Nyata", 
         "Lebih dari 30 juta penyandang disabilitas di Indonesia masih menghadapi kesenjangan komunikasi mendasar di ruang publik, layanan kesehatan, dan pendidikan."),
        ("🤝 Menjembatani Tuli & Netra",
         "Selama ini, tidak ada teknologi portabel yang memungkinkan Teman Tuli dan Teman Netra saling berkomunikasi langsung tanpa bantuan pihak ketiga."),
        ("🛡️ Privasi & Kedaulatan Data",
         "ISYARA memproses seluruh data penglihatan dan suara secara on-device (100% offline). Bebas biaya langganan, tanpa kuota, dan privasi pengguna terlindungi."),
        ("🎯 Kesesuaian SDGs 2030",
         "Mendukung Tujuan Pembangunan Berkelanjutan (SDG 10: Mengurangi Ketimpangan & SDG 4: Pendidikan Inklusif Berkualitas untuk Semua).")
    ]
    for idx, (title, desc) in enumerate(flap_texts):
        ty = 340 + idx * 250
        draw_out.text((p0_x + 30, ty), title, font=get_font(30, True), fill=TEXT_CYAN)
        lines = wrap_text(desc, get_font(24, False), panel_w - 180)
        for li, line in enumerate(lines):
            draw_out.text((p0_x + 30, ty + 48 + li * 34), line, font=get_font(24, False), fill=TEXT_WHITE)

    # 3D Dimensions graphic in bottom of flap
    dim_img_path = os.path.join(DESIGN_3D_DIR, "05_side_view_dimensi.jpg")
    outside = place_rounded_image(outside, dim_img_path, [p0_x + 30, 1420, panel_w - 90, 2300], radius=18, border_color=BORDER_DIM)
    draw_out = ImageDraw.Draw(outside)

    # --- PANEL 1 (CENTER): BACK COVER (Tim, Spesifikasi, & Kontak) ---
    p1_x = panel_w + 60
    draw_pill_badge(draw_out, p1_x, 80, "🏫 INFORMASI PROYEK", get_font(26, True), (15, 23, 42, 200), TEXT_CYAN, 24, 8)
    draw_out.text((p1_x, 150), "Spesifikasi & Tim\nPengembang", font=get_font(48, True), fill=TEXT_WHITE)
    
    card_back_bbox = [p1_x, 300, panel_w * 2 - 60, H - 100]
    outside = draw_card(outside, card_back_bbox, (15, 23, 42, 200), BORDER_DIM, radius=24, border_width=2)
    draw_out = ImageDraw.Draw(outside)
    
    # Quick Specs table
    draw_out.text((p1_x + 30, 340), "📋 Ringkasan Spesifikasi Alat", font=get_font(30, True), fill=TEXT_EMERALD)
    spec_items = [
        ("Dimensi Fisik", "76 × 150 × 22.4 mm (Handheld)"),
        ("Berat Total", "~85 gram (Ringan dibawa)"),
        ("Konsumsi Daya", "3.7V LiPo 1200mAh (USB-C Rechargeable)"),
        ("Daya Tahan", "Hingga 6–8 jam penggunaan aktif"),
        ("Komputasi", "ESP32-S3 Dual Core + ESP32-CAM OV3660"),
        ("Input", "Kamera Vision AI + 16 Tombol Braille"),
        ("Output", "Dual Display (OLED + TFT) & Speaker")
    ]
    for idx, (k, v) in enumerate(spec_items):
        sy = 405 + idx * 62
        draw_out.text((p1_x + 30, sy), f"• {k}:", font=get_font(24, True), fill=TEXT_CYAN)
        draw_out.text((p1_x + 30, sy + 28), v, font=get_font(22, False), fill=TEXT_WHITE)
        
    draw_out.line([(p1_x + 30, 870), (panel_w * 2 - 90, 870)], fill=BORDER_DIM, width=2)
    
    # Team Info & Event
    draw_out.text((p1_x + 30, 910), "🏆 Lomba AITC UNAIR 2026", font=get_font(30, True), fill=TEXT_AMBER)
    draw_out.text((p1_x + 30, 960), "Airlangga Information Technology Competition\nUniversitas Airlangga, Surabaya", font=get_font(24, False), fill=TEXT_WHITE)
    
    draw_out.text((p1_x + 30, 1070), "👥 Tim Inovator — SMK Telkom", font=get_font(30, True), fill=TEXT_CYAN)
    draw_out.text((p1_x + 30, 1120), "Karya Inovasi Teknologi Tepat Guna untuk Disabilitas.\nDibangun dengan standar rekayasa perangkat keras & AI modern.", font=get_font(23, False), fill=TEXT_MUTED)
    
    # QR Code placeholder box
    qr_bbox = [p1_x + 30, 1260, p1_x + 330, 1560]
    draw_out.rounded_rectangle(qr_bbox, radius=16, fill=(255, 255, 255), outline=BORDER_CYAN, width=2)
    draw_out.text((p1_x + 55, 1380), "[ SCAN QR ]\nDemo & Repo", font=get_font(28, True), fill=(10, 15, 26))
    
    draw_out.text((p1_x + 360, 1330), "📱 Akses Informasi Digital:", font=get_font(26, True), fill=TEXT_WHITE)
    draw_out.text((p1_x + 360, 1375), "• GitHub: github.com/Diocta/ISYARA", font=get_font(22, False), fill=TEXT_CYAN)
    draw_out.text((p1_x + 360, 1420), "• Model 3D: Interaktif STL & CAD", font=get_font(22, False), fill=TEXT_MUTED)
    draw_out.text((p1_x + 360, 1465), "• Firmware: PlatformIO ESP-IDF", font=get_font(22, False), fill=TEXT_MUTED)
    
    # Assembled CAD preview in bottom of center panel
    asm_cad_path = os.path.join(DESIGN_3D_DIR, "preview_assembled_enclosure.png")
    outside = place_rounded_image(outside, asm_cad_path, [p1_x + 30, 1620, panel_w * 2 - 90, 2300], radius=18, border_color=BORDER_DIM)
    draw_out = ImageDraw.Draw(outside)

    # --- PANEL 2 (RIGHT): FRONT COVER (Halaman Depan Utama) ---
    p2_x = panel_w * 2 + 60
    draw_pill_badge(draw_out, p2_x, 80, "✨ PRODUK UNGGULAN AITC 2026", get_font(26, True), (6, 95, 70, 220), (52, 211, 153), 26, 8)
    
    # Big Title
    draw_out.text((p2_x, 150), "ISYARA", font=get_font(130, True), fill=TEXT_WHITE)
    draw_out.text((p2_x, 310), "Inovasi Asisten Komunikasi 2-in-1", font=get_font(36, True), fill=TEXT_CYAN)
    draw_out.text((p2_x, 365), "Penerjemah Bahasa Isyarat BISINDO & Keyboard Braille Terpadu", font=get_font(26, False), fill=TEXT_MUTED)
    
    # Hero Product Image in Front Cover
    hero_img_path = os.path.join(DESIGN_3D_DIR, "03_hero_shot_dual.jpg")
    outside = place_rounded_image(outside, hero_img_path, [p2_x, 440, W - 60, 1400], radius=24, border_color=BORDER_CYAN, border_width=3)
    draw_out = ImageDraw.Draw(outside)
    
    # Front Cover Key Highlights Box
    feat_card_bbox = [p2_x, 1450, W - 60, H - 100]
    outside = draw_card(outside, feat_card_bbox, (15, 23, 42, 220), BORDER_CYAN, radius=24, border_width=2)
    draw_out = ImageDraw.Draw(outside)
    
    draw_out.text((p2_x + 35, 1490), "🌟 Keunggulan Utama Perangkat:", font=get_font(32, True), fill=TEXT_AMBER)
    cover_bullets = [
        ("⚡ 100% On-Device AI", "Pemrosesan citra tanpa ketergantungan koneksi internet."),
        ("👁️ Dual Screen Viewfinder", "Layar TFT untuk preview kamera & OLED untuk teks."),
        ("⌨️ Keyboard Braille Standar", "6 titik sel 2x3 Grade 1 + tombol fungsi pintas."),
        ("🔊 Suara Jernih Alami", "Pembacaan teks menggunakan Microsoft Azure Neural Voice.")
    ]
    for idx, (b_title, b_desc) in enumerate(cover_bullets):
        by = 1560 + idx * 170
        draw_out.text((p2_x + 35, by), b_title, font=get_font(28, True), fill=TEXT_WHITE)
        draw_out.text((p2_x + 35, by + 40), b_desc, font=get_font(23, False), fill=TEXT_MUTED)
        
    draw_out.text((p2_x + 35, 2280), "SMK TELKOM • AIRLANGGA IT COMPETITION 2026", font=get_font(24, True), fill=TEXT_CYAN)

    out_side1_file = os.path.join(OUT_DIR, "poster_lipat_luar.png")
    outside = outside.convert("RGB")
    outside.save(out_side1_file, "PNG", quality=95)
    print(f"Saved Poster Lipat (Luar): {out_side1_file} ({os.path.getsize(out_side1_file):,} bytes)")

    # -------------------------------------------------------------------------
    # SIDE 2: HALAMAN DALAM (Full Inside Opened Spread: 3 Panels)
    # Panel 0: Mode 1 - Penerjemah Isyarat Vision AI (Teman Tuli)
    # Panel 1: Mode 2 - Keyboard Braille 16-Tombol (Teman Netra)
    # Panel 2: Rekayasa Sistem, Alur Komunikasi 2-Arah & Dampak
    # -------------------------------------------------------------------------
    glows_in = [
        (panel_w // 2, H // 2, 450, (6, 182, 212, 60)),
        (panel_w + panel_w // 2, H // 2, 450, (16, 185, 129, 60)),
        (panel_w * 2 + panel_w // 2, H // 2, 450, (139, 92, 246, 60))
    ]
    inside = draw_gradient_background(W, H, (10, 16, 30), (5, 8, 16), glows_in)
    draw_in = ImageDraw.Draw(inside)
    
    # Fold Guide Lines
    for fx in [panel_w, panel_w * 2]:
        for y in range(0, H, 30):
            draw_in.line([(fx, y), (fx, y + 15)], fill=(148, 163, 184, 80), width=2)

    # --- INSIDE PANEL 0: MODE 1 VISION AI BISINDO ---
    ip0_x = 60
    draw_pill_badge(draw_in, ip0_x, 80, "📷 SISI DEPAN • MODE ISYARAT", get_font(26, True), (3, 105, 161, 220), TEXT_WHITE, 24, 8)
    draw_in.text((ip0_x, 150), "Penerjemah Bahasa\nIsyarat Real-Time", font=get_font(46, True), fill=TEXT_CYAN)
    
    # Image: Front Camera side
    front_img_path = os.path.join(DESIGN_3D_DIR, "02_sisi_depan_kamera_speaker.jpg")
    inside = place_rounded_image(inside, front_img_path, [ip0_x, 290, panel_w - 60, 1020], radius=20, border_color=BORDER_CYAN)
    draw_in = ImageDraw.Draw(inside)
    
    card_m1_bbox = [ip0_x, 1060, panel_w - 60, H - 100]
    inside = draw_card(inside, card_m1_bbox, (15, 23, 42, 220), (6, 182, 212, 140), radius=24, border_width=2)
    draw_in = ImageDraw.Draw(inside)
    
    draw_in.text((ip0_x + 35, 1100), "🔍 Cara Kerja Mode Isyarat:", font=get_font(30, True), fill=TEXT_WHITE)
    m1_steps = [
        ("1. Pengambilan Citra Cerdas", 
         "Kamera OV3660 mengambil frame 96x96 Grayscale yang telah dioptimasi kontras & ketajamannya."),
        ("2. Pemrosesan Edge Impulse TinyML", 
         "Model MobileNetV2 mengklasifikasikan pose tangan menjadi alfabet atau kata penuh dalam <100ms."),
        ("3. Anti-False-Positive Filter",
         "Menyaring noise frame kosong & jeda stabilisasi boot-up 3.5 detik untuk akurasi maksimal."),
        ("4. Output Teks & Suara Terpadu",
         "Hasil terjemahan tampil di layar OLED dan dibunyikan lantang lewat speaker mini 3W.")
    ]
    for idx, (st, sd) in enumerate(m1_steps):
        sy = 1170 + idx * 280
        draw_in.text((ip0_x + 35, sy), st, font=get_font(26, True), fill=TEXT_CYAN)
        lines = wrap_text(sd, get_font(23, False), panel_w - 180)
        for li, line in enumerate(lines):
            draw_in.text((ip0_x + 35, sy + 42 + li * 32), line, font=get_font(23, False), fill=TEXT_MUTED)

    # --- INSIDE PANEL 1: MODE 2 BRAILLE KEYBOARD ---
    ip1_x = panel_w + 60
    draw_pill_badge(draw_in, ip1_x, 80, "⌨️ SISI BELAKANG • MODE BRAILLE", get_font(26, True), (6, 95, 70, 220), (52, 211, 153), 24, 8)
    draw_in.text((ip1_x, 150), "Keyboard Braille 16-Tombol\n& Dual Display", font=get_font(46, True), fill=TEXT_EMERALD)
    
    # Image: User side with Braille Keypad
    back_img_path = os.path.join(DESIGN_3D_DIR, "01_sisi_user_belakang.jpg")
    inside = place_rounded_image(inside, back_img_path, [ip1_x, 290, panel_w * 2 - 60, 1020], radius=20, border_color=(52, 211, 153))
    draw_in = ImageDraw.Draw(inside)
    
    card_m2_bbox = [ip1_x, 1060, panel_w * 2 - 60, H - 100]
    inside = draw_card(inside, card_m2_bbox, (15, 23, 42, 220), (16, 185, 129, 140), radius=24, border_width=2)
    draw_in = ImageDraw.Draw(inside)
    
    draw_in.text((ip1_x + 35, 1100), "🖐️ Fitur Keyboard Taktil Braille:", font=get_font(30, True), fill=TEXT_WHITE)
    m2_steps = [
        ("1. Sel Braille 2x3 Ergonomis",
         "Tombol S2, S3, S6, S7, S10, S11 diposisikan pas dengan jangkauan jari untuk input Titik 1 s/d 6."),
        ("2. Standar Grade 1 Braille",
         "Mendukung penulisan huruf alfabet lengkap (A-Z), angka numerik (0-9), serta tanda baca."),
        ("3. Tombol Pintas Fungsional",
         "Tombol Spasi, Backspace, Clear All, Switch Mode, dan tombol TTS instan untuk kenyamanan penuh."),
        ("4. Jendela Tinjau OLED & TFT",
         "OLED menampilkan visualisasi titik Braille aktif, sedangkan TFT 1.77\" menjadi jendela bidik kamera.")
    ]
    for idx, (st, sd) in enumerate(m2_steps):
        sy = 1170 + idx * 280
        draw_in.text((ip1_x + 35, sy), st, font=get_font(26, True), fill=TEXT_EMERALD)
        lines = wrap_text(sd, get_font(23, False), panel_w - 180)
        for li, line in enumerate(lines):
            draw_in.text((ip1_x + 35, sy + 42 + li * 32), line, font=get_font(23, False), fill=TEXT_MUTED)

    # --- INSIDE PANEL 2: REKAYASA INTERNAL & ALUR KOMUNIKASI ---
    ip2_x = panel_w * 2 + 60
    draw_pill_badge(draw_in, ip2_x, 80, "⚙️ REKAYASA PERANGKAT KERAS", get_font(26, True), (88, 28, 135, 220), (216, 180, 254), 24, 8)
    draw_in.text((ip2_x, 150), "Arsitektur Master-Slave\n& Alur Komunikasi", font=get_font(46, True), fill=TEXT_WHITE)
    
    # Image: Exploded view inside panel 2
    exp_img_path = os.path.join(DESIGN_3D_DIR, "04_exploded_internal_view.jpg")
    inside = place_rounded_image(inside, exp_img_path, [ip2_x, 290, W - 60, 1020], radius=20, border_color=(192, 132, 252))
    draw_in = ImageDraw.Draw(inside)
    
    card_m3_bbox = [ip2_x, 1060, W - 60, H - 100]
    inside = draw_card(inside, card_m3_bbox, (15, 23, 42, 220), (139, 92, 246, 140), radius=24, border_width=2)
    draw_in = ImageDraw.Draw(inside)
    
    draw_in.text((ip2_x + 35, 1100), "🔄 Alur Komunikasi 2-Arah:", font=get_font(30, True), fill=TEXT_AMBER)
    arch_steps = [
        ("A. Teman Tuli ➔ Lawan Bicara",
         "Berisyarat di depan kamera ➔ AI membaca ➔ Suara terdengar dari speaker + teks tampil di OLED."),
        ("B. Teman Netra ➔ Lawan Bicara",
         "Mengetik via tombol Braille ➔ Teks tampil di layar untuk dibaca lawan bicara + suara terdengar."),
        ("C. Komunikasi Langsung Tuli ⟷ Netra",
         "Tuli berisyarat ➔ Suara didengar Netra. Netra mengetik Braille ➔ Teks dibaca Tuli di layar OLED!"),
        ("D. Efisiensi Master-Slave UART",
         "Beban kamera ditangani ESP32-CAM, sementara beban komputasi AI & display dikelola ESP32-S3.")
    ]
    for idx, (st, sd) in enumerate(arch_steps):
        sy = 1170 + idx * 280
        draw_in.text((ip2_x + 35, sy), st, font=get_font(26, True), fill=(216, 180, 254))
        lines = wrap_text(sd, get_font(23, False), panel_w - 180)
        for li, line in enumerate(lines):
            draw_in.text((ip2_x + 35, sy + 42 + li * 32), line, font=get_font(23, False), fill=TEXT_MUTED)

    out_side2_file = os.path.join(OUT_DIR, "poster_lipat_dalam.png")
    inside = inside.convert("RGB")
    inside.save(out_side2_file, "PNG", quality=95)
    print(f"Saved Poster Lipat (Dalam): {out_side2_file} ({os.path.getsize(out_side2_file):,} bytes)")

    # -------------------------------------------------------------------------
    # GENERATE TWO-PAGE PRINTABLE PDF
    # -------------------------------------------------------------------------
    pdf_file = os.path.join(OUT_DIR, "poster_lipat_isyara_printable.pdf")
    outside.save(pdf_file, "PDF", resolution=300.0, save_all=True, append_images=[inside])
    print(f"Saved Printable Multi-Page PDF: {pdf_file} ({os.path.getsize(pdf_file):,} bytes)")
    
    return out_side1_file, out_side2_file, pdf_file

# ==============================================================================
# 3. INTERACTIVE WEB PREVIEW HTML
# ==============================================================================
def generate_web_preview():
    html_content = """<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ISYARA — Preview Media Presentasi (X-Banner & Poster Lipat)</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
        }
        body {
            background: #090d16;
            color: #f8fafc;
            padding: 24px;
        }
        .header {
            max-width: 1400px;
            margin: 0 auto 30px auto;
            background: rgba(19, 28, 48, 0.8);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 16px;
            padding: 24px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }
        .header h1 {
            font-size: 26px;
            color: #38bdf8;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .header p {
            color: #94a3b8;
            font-size: 14px;
            margin-top: 4px;
        }
        .nav-tabs {
            display: flex;
            gap: 12px;
        }
        .tab-btn {
            background: #1e293b;
            color: #cbd5e1;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .tab-btn:hover {
            background: #334155;
            color: #fff;
            border-color: #38bdf8;
        }
        .tab-btn.active {
            background: #0284c7;
            color: #fff;
            border-color: #38bdf8;
            box-shadow: 0 0 16px rgba(2, 132, 199, 0.4);
        }
        .main-container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .preview-card {
            background: rgba(19, 28, 48, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 30px;
        }
        .preview-card h2 {
            font-size: 20px;
            color: #34d399;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .preview-card .meta {
            font-size: 13px;
            color: #94a3b8;
            margin-bottom: 20px;
        }
        .img-wrapper {
            background: #050810;
            border-radius: 12px;
            padding: 12px;
            display: flex;
            justify-content: center;
            align-items: center;
            border: 1px solid rgba(56, 189, 248, 0.2);
            overflow: auto;
        }
        .img-wrapper img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
        }
        .download-bar {
            margin-top: 16px;
            display: flex;
            gap: 12px;
            justify-content: flex-end;
        }
        .action-btn {
            background: #0f766e;
            color: #fff;
            text-decoration: none;
            padding: 8px 18px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: 0.2s;
        }
        .action-btn:hover {
            background: #14b8a6;
        }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>🎨 ISYARA — Presentation Materials (AITC UNAIR 2026)</h1>
            <p>Desain Resmi Siap Cetak: Standing X-Banner (60x160cm) & Poster Lipat Brosur A4 Trifold</p>
        </div>
        <div class="nav-tabs">
            <button class="tab-btn active" onclick="showSection('banner')">🚩 X-Banner (1701×4535)</button>
            <button class="tab-btn" onclick="showSection('poster-luar')">📄 Poster Lipat Luar</button>
            <button class="tab-btn" onclick="showSection('poster-dalam')">📖 Poster Lipat Dalam</button>
        </div>
    </div>

    <div class="main-container">
        <!-- SECTION 1: X BANNER -->
        <div id="sec-banner" class="preview-card">
            <h2>🚩 Standing X-Banner (1701 × 4535 px)</h2>
            <div class="meta">Ukuran Rasio Standar 60 × 160 cm (Standing Banner Lomba) • Resolusi Tinggi Siap Cetak Digital Printing</div>
            <div class="img-wrapper" style="max-height: 850px;">
                <img src="x_banner_isyara.png" alt="X-Banner ISYARA" style="max-height: 800px;">
            </div>
            <div class="download-bar">
                <a href="x_banner_isyara.png" download class="action-btn">📥 Unduh X-Banner PNG (1701x4535)</a>
            </div>
        </div>

        <!-- SECTION 2: POSTER LIPAT LUAR -->
        <div id="sec-poster-luar" class="preview-card" style="display: none;">
            <h2>📄 Poster Lipat / Brosur Trifold — Halaman Luar (3508 × 2480 px)</h2>
            <div class="meta">Format Standar A4 Landscape (3 Lipatan: Flap Masuk, Back Cover & Tim, Front Cover Utama) • Resolusi 300 DPI</div>
            <div class="img-wrapper">
                <img src="poster_lipat_luar.png" alt="Poster Lipat Luar">
            </div>
            <div class="download-bar">
                <a href="poster_lipat_luar.png" download class="action-btn">📥 Unduh Halaman Luar PNG</a>
                <a href="poster_lipat_isyara_printable.pdf" target="_blank" class="action-btn" style="background: #be185d;">🖨️ Buka / Cetak PDF (2 Halaman)</a>
            </div>
        </div>

        <!-- SECTION 3: POSTER LIPAT DALAM -->
        <div id="sec-poster-dalam" class="preview-card" style="display: none;">
            <h2>📖 Poster Lipat / Brosur Trifold — Halaman Dalam (3508 × 2480 px)</h2>
            <div class="meta">Tampilan Saat Brosur Dibuka Penuh (Mode 1 Vision AI BISINDO, Mode 2 Keyboard Braille, Arsitektur 2-Arah) • Resolusi 300 DPI</div>
            <div class="img-wrapper">
                <img src="poster_lipat_dalam.png" alt="Poster Lipat Dalam">
            </div>
            <div class="download-bar">
                <a href="poster_lipat_dalam.png" download class="action-btn">📥 Unduh Halaman Dalam PNG</a>
                <a href="poster_lipat_isyara_printable.pdf" target="_blank" class="action-btn" style="background: #be185d;">🖨️ Buka / Cetak PDF (2 Halaman)</a>
            </div>
        </div>
    </div>

    <script>
        function showSection(id) {
            document.getElementById('sec-banner').style.display = (id === 'banner') ? 'block' : 'none';
            document.getElementById('sec-poster-luar').style.display = (id === 'poster-luar') ? 'block' : 'none';
            document.getElementById('sec-poster-dalam').style.display = (id === 'poster-dalam') ? 'block' : 'none';

            const buttons = document.querySelectorAll('.tab-btn');
            buttons.forEach(btn => btn.classList.remove('active'));
            if (id === 'banner') buttons[0].classList.add('active');
            if (id === 'poster-luar') buttons[1].classList.add('active');
            if (id === 'poster-dalam') buttons[2].classList.add('active');
        }
    </script>
</body>
</html>
"""
    out_html = os.path.join(OUT_DIR, "preview_presentation_materials.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Saved Interactive Preview HTML: {out_html}")
    return out_html

if __name__ == '__main__':
    print("=" * 65)
    print("  ISYARA — PRESENTATION MATERIALS GENERATION")
    print(f"  Target Directory: {OUT_DIR}")
    print("=" * 65)
    
    generate_x_banner()
    generate_folded_poster()
    generate_web_preview()
    
    print("\n" + "=" * 65)
    print("All presentation materials generated successfully!")
    print("=" * 65)
