"""
ISYARA - Generator & Augmenter Dataset Isyarat Kata BISINDO (Word-Level Sign Language)
Menghasilkan dataset citra berkualitas tinggi untuk 7 kata esensial BISINDO:
1. SAYA (Aku)       : Tangan terbuka/menunjuk ke dada sendiri
2. MAKAN            : Tangan menguncup menyuap makanan ke dekat mulut
3. MINUM            : Tangan membentuk cangkir/C mengarah ke bibir
4. TIDUR            : Telapak tangan dirapatkan di samping pipi/kepala miring
5. TOLONG           : Kedua telapak tangan menangkup di depan dada (memohon bantuan)
6. TERIMA_KASIH     : Ujung jari menyentuh dagu lalu bergerak maju mendatar
7. HALO             : Telapak tangan terbuka di samping pelipis melambai ramah

Format output: 224x224 RGB JPEG, tegak (upright), variasi pencahayaan & warna realistis.
Jumlah target: 170 gambar per kelas kata (seimbang dengan 26 kelas alfabet A-Z).
"""

import os
import random
import math
import numpy as np
import cv2

DATASET_ROOT = r"C:\Users\Acer Nitro 5\Documents\TUGAS SMK TELKOM\lomba\AITC UNAIR 2026\BISINDO_dataset\BISINDO_dataset"

WORD_CLASSES = [
    "SAYA",
    "MAKAN",
    "MINUM",
    "TIDUR",
    "TOLONG",
    "TERIMA_KASIH",
    "HALO"
]

SAMPLES_PER_CLASS = 170
IMG_SIZE = 224

# Palet warna kulit representatif masyarakat Indonesia (BGR)
SKIN_TONES = [
    (170, 195, 235), # Kuning langsat terang
    (150, 180, 220), # Sawo matang terang
    (125, 155, 195), # Sawo matang standar
    (110, 140, 180), # Cokelat matang
    (95, 125, 165),  # Eksotis gelap
]

# Warna pakaian umum (BGR)
SHIRT_COLORS = [
    (240, 240, 240), # Putih
    (40, 40, 40),    # Hitam
    (180, 80, 50),   # Biru navy
    (50, 120, 60),   # Hijau tua
    (60, 60, 170),   # Merah marun
    (150, 150, 150), # Abu-abu
    (120, 90, 70),   # Biru denim
]

def create_background(w, h):
    """Membuat latar belakang ruangan indoor yang realistis dengan gradien halus."""
    bg_type = random.choice(["plain", "gradient", "room"])
    if bg_type == "plain":
        val = random.randint(180, 245)
        color = (val + random.randint(-8, 8), val, val + random.randint(-8, 8))
        img = np.full((h, w, 3), color, dtype=np.uint8)
    elif bg_type == "gradient":
        top_val = random.randint(190, 240)
        bot_val = random.randint(140, 190)
        img = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            ratio = y / h
            v = int(top_val * (1 - ratio) + bot_val * ratio)
            img[y, :] = (v + random.randint(-3, 3), v, v + random.randint(-3, 3))
    else:
        # Simulasi dinding dan meja
        wall_val = random.randint(180, 230)
        img = np.full((h, w, 3), (wall_val, wall_val, wall_val), dtype=np.uint8)
        desk_y = int(h * (0.80 + random.uniform(-0.05, 0.05)))
        desk_color = (random.randint(90, 130), random.randint(110, 150), random.randint(130, 170))
        img[desk_y:, :] = desk_color
        cv2.line(img, (0, desk_y), (w, desk_y), (desk_color[0] - 25, desk_color[1] - 25, desk_color[2] - 25), 2)
    return img

def draw_person_base(canvas, skin_color, shirt_color, head_tilt=0):
    """Menggambar siluet tubuh dasar (kepala, leher, pundak, dan torso)."""
    h, w, _ = canvas.shape
    center_x = w // 2 + random.randint(-4, 4)
    head_y = int(h * 0.32) + random.randint(-3, 3)
    head_r = int(w * 0.16)

    # Torso / Pundak
    shoulder_y = int(h * 0.58)
    shoulder_w = int(w * 0.44)
    pts_shirt = np.array([
        [center_x - shoulder_w, h],
        [center_x - shoulder_w + 10, shoulder_y + 15],
        [center_x - int(shoulder_w * 0.6), shoulder_y],
        [center_x - int(w * 0.12), head_y + head_r],
        [center_x + int(w * 0.12), head_y + head_r],
        [center_x + int(shoulder_w * 0.6), shoulder_y],
        [center_x + shoulder_w - 10, shoulder_y + 15],
        [center_x + shoulder_w, h]
    ], np.int32)
    cv2.fillConvexPoly(canvas, pts_shirt, shirt_color, cv2.LINE_AA)

    # Leher
    neck_w = int(w * 0.09)
    neck_pts = np.array([
        [center_x - neck_w, head_y + int(head_r * 0.6)],
        [center_x + neck_w, head_y + int(head_r * 0.6)],
        [center_x + neck_w + 5, head_y + head_r + 15],
        [center_x - neck_w - 5, head_y + head_r + 15]
    ], np.int32)
    cv2.fillConvexPoly(canvas, neck_pts, skin_color, cv2.LINE_AA)

    # Kepala (Oval dengan rotasi kemiringan jika ada)
    head_center = (center_x + int(math.sin(math.radians(head_tilt)) * 8), head_y)
    axes = (head_r - 4, int(head_r * 1.15))
    cv2.ellipse(canvas, head_center, axes, head_tilt, 0, 360, skin_color, -1, cv2.LINE_AA)

    # Rambut
    hair_color = (random.randint(15, 30), random.randint(15, 30), random.randint(15, 30))
    cv2.ellipse(canvas, head_center, (axes[0] + 3, axes[1] + 3), head_tilt, 180, 360, hair_color, -1, cv2.LINE_AA)

    return center_x, head_y, head_r, shoulder_y

def draw_gesture_saya(canvas, skin_color, cx, hy, hr, sy):
    """SAYA (Aku): Tangan kanan diletakkan atau menunjuk ke tengah dada."""
    hand_x = cx + random.randint(-5, 10)
    hand_y = sy + int(hr * 0.6) + random.randint(-4, 4)

    # Lengan dari kanan bawah ke dada
    cv2.line(canvas, (cx + int(cx * 0.7), int(sy * 1.35)), (hand_x + 12, hand_y + 15), skin_color, 24, cv2.LINE_AA)
    # Telapak tangan di dada
    cv2.ellipse(canvas, (hand_x, hand_y), (14, 18), -20, 0, 360, skin_color, -1, cv2.LINE_AA)
    # Jari telunjuk mengarah ke dada
    cv2.line(canvas, (hand_x, hand_y), (hand_x - 12, hand_y - 8), skin_color, 7, cv2.LINE_AA)
    # Jari-jari lain dilipat
    cv2.circle(canvas, (hand_x + 6, hand_y + 4), 6, (skin_color[0] - 15, skin_color[1] - 15, skin_color[2] - 15), -1, cv2.LINE_AA)

def draw_gesture_makan(canvas, skin_color, cx, hy, hr, sy):
    """MAKAN: Tangan menguncup menyuap makanan ke arah bibir/mulut."""
    mouth_x = cx + random.randint(-3, 3)
    mouth_y = hy + int(hr * 0.55)

    hand_x = mouth_x + random.randint(12, 22)
    hand_y = mouth_y + random.randint(4, 12)

    # Lengan menuju mulut
    cv2.line(canvas, (cx + int(cx * 0.65), int(sy * 1.35)), (hand_x + 8, hand_y + 20), skin_color, 22, cv2.LINE_AA)
    # Tangan menguncup (jari menyatu seperti mencubit nasi/makanan)
    cv2.ellipse(canvas, (hand_x, hand_y), (12, 16), 40, 0, 360, skin_color, -1, cv2.LINE_AA)
    # Ujung jari menguncup mengarah ke mulut
    pts_pinch = np.array([
        [hand_x - 10, hand_y - 2],
        [hand_x + 4, hand_y - 12],
        [hand_x + 10, hand_y + 5]
    ], np.int32)
    cv2.fillConvexPoly(canvas, pts_pinch, skin_color, cv2.LINE_AA)

def draw_gesture_minum(canvas, skin_color, cx, hy, hr, sy):
    """MINUM: Tangan membentuk huruf C (cangkir) di dekat bibir/mulut."""
    mouth_x = cx + random.randint(-2, 2)
    mouth_y = hy + int(hr * 0.5)

    hand_x = mouth_x + random.randint(10, 18)
    hand_y = mouth_y + random.randint(-2, 6)

    # Lengan naik ke mulut
    cv2.line(canvas, (cx + int(cx * 0.65), int(sy * 1.35)), (hand_x + 10, hand_y + 22), skin_color, 22, cv2.LINE_AA)
    # Bentuk tangan C (cangkir)
    cv2.ellipse(canvas, (hand_x, hand_y), (14, 17), 25, 0, 360, skin_color, -1, cv2.LINE_AA)
    # Ibu jari ke atas, jari melengkung ke bibir
    cv2.ellipse(canvas, (hand_x - 6, hand_y - 2), (8, 12), -15, 200, 380, (skin_color[0] - 25, skin_color[1] - 25, skin_color[2] - 25), 4, cv2.LINE_AA)

def draw_gesture_tidur(canvas, skin_color, cx, hy, hr, sy):
    """TIDUR: Telapak tangan dirapatkan di samping pipi dengan kepala miring."""
    cheek_x = cx + int(hr * 0.8) + random.randint(-3, 3)
    cheek_y = hy + int(hr * 0.25) + random.randint(-3, 3)

    # Lengan menyilang ke pipi
    cv2.line(canvas, (cx + int(cx * 0.6), int(sy * 1.35)), (cheek_x + 10, cheek_y + 25), skin_color, 22, cv2.LINE_AA)
    # Telapak tangan miring menopang pipi
    cv2.ellipse(canvas, (cheek_x, cheek_y), (11, 22), -35, 0, 360, skin_color, -1, cv2.LINE_AA)
    # 4 jari rapat memanjang
    cv2.line(canvas, (cheek_x - 3, cheek_y - 15), (cheek_x + 12, cheek_y - 28), skin_color, 7, cv2.LINE_AA)

def draw_gesture_tolong(canvas, skin_color, cx, hy, hr, sy):
    """TOLONG: Kedua telapak tangan menangkup di depan dada (isyarat memohon/bantu)."""
    center_hand_y = sy + int(hr * 0.25) + random.randint(-4, 4)

    # Lengan kiri & kanan ke tengah
    cv2.line(canvas, (cx - int(cx * 0.55), int(sy * 1.35)), (cx - 10, center_hand_y + 20), skin_color, 20, cv2.LINE_AA)
    cv2.line(canvas, (cx + int(cx * 0.55), int(sy * 1.35)), (cx + 10, center_hand_y + 20), skin_color, 20, cv2.LINE_AA)

    # Dua tangan menangkup rapat
    cv2.ellipse(canvas, (cx - 6, center_hand_y), (9, 20), 12, 0, 360, skin_color, -1, cv2.LINE_AA)
    cv2.ellipse(canvas, (cx + 6, center_hand_y), (9, 20), -12, 0, 360, skin_color, -1, cv2.LINE_AA)
    # Jari-jari mengarah ke atas
    cv2.line(canvas, (cx - 4, center_hand_y - 12), (cx - 2, center_hand_y - 28), skin_color, 6, cv2.LINE_AA)
    cv2.line(canvas, (cx + 4, center_hand_y - 12), (cx + 2, center_hand_y - 28), skin_color, 6, cv2.LINE_AA)

def draw_gesture_terima_kasih(canvas, skin_color, cx, hy, hr, sy):
    """TERIMA KASIH: Tangan terbuka menyentuh dagu lalu bergerak mendatar ke depan."""
    chin_x = cx + random.randint(-2, 2)
    chin_y = hy + int(hr * 0.8)

    hand_x = chin_x + random.randint(10, 24)
    hand_y = chin_y + random.randint(0, 10)

    # Lengan naik ke bawah dagu
    cv2.line(canvas, (cx + int(cx * 0.65), int(sy * 1.35)), (hand_x + 12, hand_y + 20), skin_color, 22, cv2.LINE_AA)
    # Telapak tangan mendatar
    cv2.ellipse(canvas, (hand_x, hand_y), (18, 11), -15, 0, 360, skin_color, -1, cv2.LINE_AA)
    # Jari-jari lurus mengarah ke depan
    cv2.line(canvas, (hand_x - 8, hand_y), (hand_x - 22, hand_y - 3), skin_color, 7, cv2.LINE_AA)

def draw_gesture_halo(canvas, skin_color, cx, hy, hr, sy):
    """HALO: Telapak tangan terbuka di samping pelipis/telinga melambai ramah."""
    hand_x = cx + int(hr * 1.25) + random.randint(-4, 6)
    hand_y = hy + random.randint(-10, 8)

    # Lengan naik ke samping kepala
    cv2.line(canvas, (cx + int(cx * 0.65), int(sy * 1.35)), (hand_x - 4, hand_y + 35), skin_color, 22, cv2.LINE_AA)
    # Telapak tangan terbuka tegak
    cv2.circle(canvas, (hand_x, hand_y), 13, skin_color, -1, cv2.LINE_AA)
    # 5 jari terbuka tegak (melambai)
    finger_angles = [-25, -10, 5, 20, 35]
    for angle in finger_angles:
        rad = math.radians(angle - 90)
        f_len = random.randint(18, 23)
        fx = int(hand_x + math.cos(rad) * f_len)
        fy = int(hand_y + math.sin(rad) * f_len)
        cv2.line(canvas, (hand_x, hand_y), (fx, fy), skin_color, 5, cv2.LINE_AA)

def apply_realistic_augmentation(img):
    """Augmentasi realistis: variasi rotasi kecil, skala, pencahayaan, dan blur."""
    h, w, _ = img.shape

    # 1. Rotasi acak (-8 s.d. +8 derajat)
    angle = random.uniform(-8.0, 8.0)
    scale = random.uniform(0.92, 1.08)
    dx = random.randint(-8, 8)
    dy = random.randint(-8, 8)

    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, scale)
    M[0, 2] += dx
    M[1, 2] += dy
    aug = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)

    # 2. Penyesuaian pencahayaan & kontras (0.85x - 1.20x)
    alpha = random.uniform(0.85, 1.20)
    beta = random.randint(-15, 20)
    aug = np.clip(alpha * aug + beta, 0, 255).astype(np.uint8)

    # 3. Efek blur gerakan halus (simulasi kamera OV3660)
    if random.random() < 0.35:
        k = random.choice([3, 5])
        aug = cv2.GaussianBlur(aug, (k, k), 0)

    return aug

def generate_word_class(word_label, count=SAMPLES_PER_CLASS):
    target_dir = os.path.join(DATASET_ROOT, word_label)
    os.makedirs(target_dir, exist_ok=True)

    print(f"\n[GENERASI] Membuat {count} citra untuk kelas kata: '{word_label}'...")

    for i in range(1, count + 1):
        canvas = create_background(IMG_SIZE, IMG_SIZE)
        skin = random.choice(SKIN_TONES)
        shirt = random.choice(SHIRT_COLORS)

        # Kemiringan kepala khusus untuk isyarat TIDUR
        head_tilt = random.randint(-22, -14) if word_label == "TIDUR" else random.randint(-4, 4)

        cx, hy, hr, sy = draw_person_base(canvas, skin, shirt, head_tilt)

        # Gambar pose isyarat spesifik
        if word_label == "SAYA":
            draw_gesture_saya(canvas, skin, cx, hy, hr, sy)
        elif word_label == "MAKAN":
            draw_gesture_makan(canvas, skin, cx, hy, hr, sy)
        elif word_label == "MINUM":
            draw_gesture_minum(canvas, skin, cx, hy, hr, sy)
        elif word_label == "TIDUR":
            draw_gesture_tidur(canvas, skin, cx, hy, hr, sy)
        elif word_label == "TOLONG":
            draw_gesture_tolong(canvas, skin, cx, hy, hr, sy)
        elif word_label == "TERIMA_KASIH":
            draw_gesture_terima_kasih(canvas, skin, cx, hy, hr, sy)
        elif word_label == "HALO":
            draw_gesture_halo(canvas, skin, cx, hy, hr, sy)

        # Terapkan augmentasi realistis
        final_img = apply_realistic_augmentation(canvas)

        filename = f"{word_label}_{i:04d}.jpg"
        filepath = os.path.join(target_dir, filename)
        cv2.imwrite(filepath, final_img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

        if i % 35 == 0 or i == count:
            print(f"  [{word_label}] Progress: {i}/{count} citra dibuat...")

    print(f"[OK] Selesai kelas '{word_label}': {count} citra tersimpan di {target_dir}")

def main():
    print("=" * 65)
    print("  ISYARA - BISINDO WORD-LEVEL DATASET GENERATOR")
    print("=" * 65)
    print(f"Target Direktori : {DATASET_ROOT}")
    print(f"Daftar Kata      : {', '.join(WORD_CLASSES)}")
    print(f"Jumlah per Kelas : {SAMPLES_PER_CLASS} citra (Total: {len(WORD_CLASSES) * SAMPLES_PER_CLASS} citra)")
    print("=" * 65)

    total_created = 0
    for word in WORD_CLASSES:
        generate_word_class(word, SAMPLES_PER_CLASS)
        total_created += SAMPLES_PER_CLASS

    print("\n" + "=" * 65)
    print(f"SELESAI! Berhasil menghasilkan total {total_created} citra isyarat kata.")
    print("Dataset kata telah siap diintegrasikan dengan Edge Impulse & firmware ESP32-S3!")
    print("=" * 65)

if __name__ == "__main__":
    main()
