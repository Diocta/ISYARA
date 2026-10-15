"""
Script Data Augmentation untuk Dataset BISINDO 96x96
Menggandakan jumlah data per kelas secara otomatis dengan variasi realistis:
- Sedikit rotasi (-8 derajat s.d. +8 derajat)
- Penyesuaian kecerahan (gelap 0.85x, terang 1.15x)
- Sedikit pergeseran posisi (translasi +/- 3 piksel)
- Sedikit zoom in/out
"""

import os
import glob
from PIL import Image, ImageEnhance

DATASET_ROOT = os.path.join(os.path.dirname(__file__), "..", "dataset")

def augment_folder(folder_path):
    label = os.path.basename(folder_path)
    image_files = glob.glob(os.path.join(folder_path, "*.jpg")) + glob.glob(os.path.join(folder_path, "*.png"))
    
    # Filter hanya file asli (bukan yang sudah diaugmentasi)
    original_files = [f for f in image_files if "_aug_" not in os.path.basename(f)]
    
    if not original_files:
        print(f"[{label}] Tidak ada file asli di {folder_path} untuk diaugmentasi.")
        return

    print(f"[{label}] Ditemukan {len(original_files)} file asli. Memulai augmentasi...")
    created_count = 0

    for idx, filepath in enumerate(original_files):
        try:
            with Image.open(filepath) as img:
                img_gray = img.convert('L')
                base_name = os.path.splitext(os.path.basename(filepath))[0]

                # 1. Rotasi sedikit kiri (-6 deg)
                rot_left = img_gray.rotate(-6, resample=Image.Resampling.BILINEAR)
                rot_left.save(os.path.join(folder_path, f"{base_name}_aug_rot_l.jpg"), quality=95)
                created_count += 1

                # 2. Rotasi sedikit kanan (+6 deg)
                rot_right = img_gray.rotate(6, resample=Image.Resampling.BILINEAR)
                rot_right.save(os.path.join(folder_path, f"{base_name}_aug_rot_r.jpg"), quality=95)
                created_count += 1

                # 3. Kecerahan lebih gelap (0.85x)
                enhancer = ImageEnhance.Brightness(img_gray)
                dark = enhancer.enhance(0.85)
                dark.save(os.path.join(folder_path, f"{base_name}_aug_dark.jpg"), quality=95)
                created_count += 1

                # 4. Kecerahan lebih terang (1.18x)
                bright = enhancer.enhance(1.18)
                bright.save(os.path.join(folder_path, f"{base_name}_aug_bright.jpg"), quality=95)
                created_count += 1

                # 5. Sedikit Zoom / Crop tengah
                w, h = img_gray.size
                pad = 4
                crop_box = (pad, pad, w - pad, h - pad)
                zoom = img_gray.crop(crop_box).resize((w, h), Image.Resampling.BILINEAR)
                zoom.save(os.path.join(folder_path, f"{base_name}_aug_zoom.jpg"), quality=95)
                created_count += 1

        except Exception as e:
            print(f"Error memproses {filepath}: {e}")

    print(f"[{label}] Selesai! Ditambahkan {created_count} data baru.")

def main():
    if not os.path.exists(DATASET_ROOT):
        print(f"Folder dataset '{DATASET_ROOT}' belum ada.")
        return

    subfolders = [os.path.join(DATASET_ROOT, d) for d in os.listdir(DATASET_ROOT) if os.path.isdir(os.path.join(DATASET_ROOT, d))]
    
    if not subfolders:
        print("Belum ada subfolder label di dalam folder dataset.")
        return

    print("=== BISINDO DATA AUGMENTER ===")
    for folder in sorted(subfolders):
        augment_folder(folder)

    total_images = len(glob.glob(os.path.join(DATASET_ROOT, "*", "*.jpg")))
    print(f"\nTotal seluruh gambar di folder dataset sekarang: {total_images} gambar.")

if __name__ == "__main__":
    main()
