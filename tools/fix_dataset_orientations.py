"""
ISYARA - Dataset Orientation & Normalization Script
Memperbaiki seluruh rotasi gambar agar semua gestur berdiri tegak (upright)
dan menghadap ke arah yang konsisten di semua 27 kelas (A-Z + idle).
"""

import os
import glob
from PIL import Image, ImageOps, ExifTags

DATASET_ROOT = r"C:\Users\Acer Nitro 5\Documents\TUGAS SMK TELKOM\lomba\AITC UNAIR 2026\BISINDO_dataset\BISINDO_dataset"

def get_template(filename, letter):
    fl = filename
    if fl.lower().startswith(letter.lower()):
        return fl[len(letter):].lstrip(' _-').lower()
    return fl.lower()

def apply_exif_orientation_manual(im, orient):
    if orient == 1:
        return im
    elif orient == 2:
        return im.transpose(Image.FLIP_LEFT_RIGHT)
    elif orient == 3:
        return im.rotate(180, expand=True)
    elif orient == 4:
        return im.transpose(Image.FLIP_TOP_BOTTOM)
    elif orient == 5:
        return im.transpose(Image.FLIP_LEFT_RIGHT).rotate(90, expand=True)
    elif orient == 6:
        return im.rotate(270, expand=True)  # 90 deg Clockwise
    elif orient == 7:
        return im.transpose(Image.FLIP_LEFT_RIGHT).rotate(270, expand=True)
    elif orient == 8:
        return im.rotate(90, expand=True)   # 90 deg Counter-Clockwise
    return im

def main():
    print("=" * 65)
    print("   ISYARA - STANDARISASI ORIENTASI DATASET BISINDO")
    print("=" * 65)

    # 1. Bangun kamus orientasi dari huruf A-I yang memiliki metadata EXIF asli
    template_orient_map = {}
    print("1. Menganalisis metadata orientasi dari huruf A - I...")
    for letter in "ABCDEFGHI":
        folder = os.path.join(DATASET_ROOT, letter)
        if not os.path.isdir(folder):
            continue
        for f in os.listdir(folder):
            if not f.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            p = os.path.join(folder, f)
            try:
                im = Image.open(p)
                ex = im._getexif()
                if ex and ex.get(274):
                    orient = ex.get(274)
                    tmpl = get_template(f, letter)
                    if tmpl not in template_orient_map or orient != 1:
                        template_orient_map[tmpl] = orient
            except Exception:
                pass

    print(f"   Ditemukan {len(template_orient_map)} pola template dengan orientasi kamera khusus.")

    # 2. Proses normalisasi untuk semua kelas (A-Z + idle)
    print("\n2. Melakukan rotasi dan normalisasi piksel untuk seluruh kelas...")
    total_processed = 0
    total_rotated = 0

    subfolders = sorted(os.listdir(DATASET_ROOT))
    for letter in subfolders:
        folder = os.path.join(DATASET_ROOT, letter)
        if not os.path.isdir(folder) or letter.startswith('.'):
            continue

        files = sorted(os.listdir(folder))
        letter_rotated = 0

        for f in files:
            if not f.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            p = os.path.join(folder, f)

            try:
                with Image.open(p) as orig_im:
                    orig_exif = orig_im._getexif() if hasattr(orig_im, '_getexif') else None
                    has_exif_orient = orig_exif and orig_exif.get(274) and orig_exif.get(274) != 1

                    was_rotated = False
                    # Kasus A: File memiliki tag EXIF orientation asli (kebanyakan di A-I)
                    if has_exif_orient:
                        im = ImageOps.exif_transpose(orig_im)
                        was_rotated = True
                    # Kasus B: File di J-Z yang EXIF-nya terhapus tapi berasal dari sesi kamera yang sama
                    else:
                        im = orig_im.copy()
                        tmpl = get_template(f, letter)
                        if f.startswith('20240509'):
                            # Sesi kamera 20240509 di J-Z terbalik 180 derajat
                            im = im.rotate(180, expand=True)
                            was_rotated = True
                        elif 'samsung_a53' in f.lower() and 'garis' in f.lower() and letter in 'JKLMNOPZ':
                            # Sesi baju garis Samsung A53 di J-O dan Z terpotret horizontal
                            im = im.rotate(270, expand=True)  # rotasi 90 CW agar garis tegak
                            was_rotated = True
                        elif tmpl in template_orient_map and template_orient_map[tmpl] != 1:
                            # Terapkan orientasi yang sama seperti pasangannya di A-I
                            im = apply_exif_orientation_manual(im, template_orient_map[tmpl])
                            was_rotated = True

                    im = im.convert('RGB')

                    # Pastikan ukuran seragam 224x224 (ukuran asli dataset)
                    if im.size != (224, 224) and 'idle' not in letter:
                        im = im.resize((224, 224), Image.Resampling.LANCZOS)

                    # Simpan kembali tanpa tag EXIF yang usang
                    im.save(p, "JPEG", quality=95)
                    total_processed += 1
                    if was_rotated:
                        letter_rotated += 1
                        total_rotated += 1

            except Exception as e:
                print(f"   [Error] {letter}/{f}: {e}")

        print(f"   Kelas [{letter}]: {len(files)} foto diproses ({letter_rotated} diperbaiki orientasinya)")

    print("\n" + "=" * 65)
    print(f"SELESAI! Total foto diproses: {total_processed}")
    print(f"Total foto yang orientasinya diperbaiki (tegak): {total_rotated}")
    print("Semua gambar kini seragam menghadap ke arah yang sama (upright)!")
    print("=" * 65)

if __name__ == "__main__":
    main()
