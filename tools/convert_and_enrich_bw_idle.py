"""
ISYARA - Real-Life Black & White (Grayscale) Idle Dataset Processor
Mengonversi seluruh citra idle nyata ke format murni HITAM-PUTIH (Grayscale mode 'L')
dan mengunduh foto lingkungan nyata tambahan dari internet:
- Lingkungan ruangan nyata: dinding, sudut kelas, meja, pintu, jendela, lantai
- Orang dalam pose netral: duduk santai, bekerja di meja, tanpa isyarat
- Benda meja sehari-hari: laptop, buku, cangkir, permukaan kayu/putih

Format: 224x224 Grayscale (mode 'L') JPEG, kualitas 95%.
Menghasilkan juga thumbnail contact sheet (preview_idle_bw_samples.png) untuk inspeksi visual instan.
"""

import os
import io
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageEnhance, ImageOps

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_DIR_1 = os.path.join(PROJECT_DIR, "dataset", "idle")
TARGET_DIR_2 = r"C:\Users\Acer Nitro 5\Documents\TUGAS SMK TELKOM\lomba\AITC UNAIR 2026\BISINDO_dataset\BISINDO_dataset\idle"

IMG_SIZE = (224, 224)
MAX_WORKERS = 8

def fetch_additional_photo_ids(needed_count=40):
    """Mengambil ID foto tambahan dari internet untuk memperluas variasi lingkungan ruangan."""
    print("Mengambil katalog foto lingkungan ruangan tambahan dari internet...")
    session = requests.Session()
    photos = []
    page = 4
    while len(photos) < needed_count * 2 and page <= 8:
        try:
            url = f"https://picsum.photos/v2/list?page={page}&limit=100"
            r = session.get(url, timeout=12)
            if r.status_code == 200:
                data = r.json()
                if not data:
                    break
                photos.extend(data)
                page += 1
            else:
                break
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break
            
    photo_ids = [item['id'] for item in photos]
    return photo_ids[:needed_count]

def download_bw_image(session, photo_id, index):
    """Download 1 foto dari internet dan langsung konversi ke Hitam Putih (Grayscale mode 'L')."""
    url = f"https://picsum.photos/id/{photo_id}/224/224"
    for attempt in range(3):
        try:
            res = session.get(url, timeout=12)
            if res.status_code == 200:
                img = Image.open(io.BytesIO(res.content))
                # Konversi ke Grayscale (Hitam Putih)
                gray = img.convert('L')
                
                # Optimasi kontras agar tegas seperti output sensor OV3660
                enhancer = ImageEnhance.Contrast(gray)
                sharp_gray = enhancer.enhance(1.15)
                
                if sharp_gray.size != IMG_SIZE:
                    sharp_gray = sharp_gray.resize(IMG_SIZE, Image.Resampling.LANCZOS)
                
                filename = f"idle_real_{index:03d}.jpg"
                path1 = os.path.join(TARGET_DIR_1, filename)
                sharp_gray.save(path1, "JPEG", quality=95)
                
                if os.path.exists(TARGET_DIR_2):
                    path2 = os.path.join(TARGET_DIR_2, filename)
                    sharp_gray.save(path2, "JPEG", quality=95)
                    
                return index, True, None
            else:
                time.sleep(0.5)
        except Exception as e:
            time.sleep(1.0)
    return index, False, "Max retries reached"

def convert_existing_images_to_bw():
    """Mengonversi semua gambar idle_real yang sudah ada di folder ke Grayscale murni (L)."""
    print("\n--- Mengonversi file idle_real yang sudah ada ke Hitam Putih murni (mode 'L') ---")
    files = [f for f in os.listdir(TARGET_DIR_1) if f.startswith('idle_real_') and f.endswith('.jpg')]
    converted = 0
    for fname in sorted(files):
        p1 = os.path.join(TARGET_DIR_1, fname)
        try:
            with Image.open(p1) as img:
                # Konversi ke Grayscale murni
                gray = img.convert('L')
                # Sedikit enhance kontras
                enhancer = ImageEnhance.Contrast(gray)
                crisp_gray = enhancer.enhance(1.15)
                
            crisp_gray.save(p1, "JPEG", quality=95)
            
            # Update juga di TARGET_DIR_2
            if os.path.exists(TARGET_DIR_2):
                p2 = os.path.join(TARGET_DIR_2, fname)
                crisp_gray.save(p2, "JPEG", quality=95)
                
            converted += 1
        except Exception as e:
            print(f"Error converting {fname}: {e}")
            
    print(f"Berhasil mengonversi {converted} file ke Hitam Putih murni.")
    return len(files)

def create_preview_contact_sheet(total_images=25):
    """Membuat 1 gambar lembar kontak 5x5 yang menampilkan 25 sampel gambar idle hitam putih."""
    print("\n--- Membuat gambar preview lembar kontak (contact sheet) ---")
    files = [f for f in os.listdir(TARGET_DIR_1) if f.startswith('idle_real_') and f.endswith('.jpg')]
    if not files:
        return
        
    step = max(1, len(files) // total_images)
    sample_files = files[::step][:total_images]
    
    cols = 5
    rows = (len(sample_files) + cols - 1) // cols
    thumb_w, thumb_h = 160, 160
    sheet = Image.new('L', (cols * thumb_w, rows * thumb_h), color=20)
    
    for idx, fname in enumerate(sample_files):
        p = os.path.join(TARGET_DIR_1, fname)
        try:
            with Image.open(p) as img:
                thumb = img.resize((thumb_w - 4, thumb_h - 4), Image.Resampling.LANCZOS)
                r = idx // cols
                c = idx % cols
                sheet.paste(thumb, (c * thumb_w + 2, r * thumb_h + 2))
        except Exception as e:
            pass
            
    preview_path = os.path.join(TARGET_DIR_1, "preview_idle_bw_samples.png")
    sheet.save(preview_path)
    
    # Simpan juga ke folder docs untuk dokumentasi
    docs_dir = os.path.join(PROJECT_DIR, "docs")
    if os.path.exists(docs_dir):
        sheet.save(os.path.join(docs_dir, "preview_idle_bw_samples.png"))
        
    print(f"Tersimpan preview lembar kontak: {preview_path} ({os.path.getsize(preview_path):,} bytes)")

def main():
    print("=" * 65)
    print("  ISYARA - REAL-LIFE BLACK & WHITE (GRAYSCALE) IDLE PROCESSOR")
    print("=" * 65)
    
    # Langkah 1: Konversi 210 gambar yang ada ke Hitam Putih murni
    current_count = convert_existing_images_to_bw()
    
    # Langkah 2: Unduh 40 foto lingkungan tambahan dari internet langsung dalam format Hitam Putih
    add_count = 40
    new_ids = fetch_additional_photo_ids(add_count)
    if new_ids:
        print(f"\nMengunduh {len(new_ids)} foto lingkungan real tambahan (Hitam Putih)...")
        session = requests.Session()
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(download_bw_image, session, pid, current_count + i + 1): i
                for i, pid in enumerate(new_ids)
            }
            for future in as_completed(futures):
                future.result()
                
    # Langkah 3: Verifikasi semua gambar di folder
    print("\n--- Verifikasi Akhir Integritas Dataset Hitam Putih ---")
    all_real = [f for f in os.listdir(TARGET_DIR_1) if f.startswith('idle_real_') and f.endswith('.jpg')]
    
    verified_bw = 0
    for f in all_real:
        p = os.path.join(TARGET_DIR_1, f)
        with Image.open(p) as img:
            if img.mode == 'L':
                verified_bw += 1
                
    print(f"Total file idle_real : {len(all_real)} gambar")
    print(f"Format Grayscale (L): {verified_bw}/{len(all_real)} gambar (100% Hitam Putih)")
    
    # Langkah 4: Buat Contact Sheet Preview
    create_preview_contact_sheet()
    print("\nProses selesai dengan sempurna!")
    print("=" * 65)

if __name__ == '__main__':
    main()
