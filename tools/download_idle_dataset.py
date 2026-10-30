"""
ISYARA - Downloader Dataset Real-World Idle (Negative Class) dari Internet
Mengunduh ~210 gambar nyata berkualitas tinggi dari internet:
- Orang duduk / santai tanpa gerakan isyarat (neutral pose, hands at rest, portraits)
- Latar belakang ruangan indoor (kantor, kelas, ruang tamu, dinding, jendela)
- Objek meja / perabot (laptop, buku, meja, kursi)
- Variasi pencahayaan ruangan nyata

Format output: 224x224 RGB JPEG (konsisten dengan kelas A-Z dan 7 kata BISINDO).
Target lokasi penyimpanan:
1. dataset/idle/
2. BISINDO_dataset/BISINDO_dataset/idle/
"""

import os
import io
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

# Lokasi folder tujuan
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_DIR_1 = os.path.join(PROJECT_DIR, "dataset", "idle")
TARGET_DIR_2 = r"C:\Users\Acer Nitro 5\Documents\TUGAS SMK TELKOM\lomba\AITC UNAIR 2026\BISINDO_dataset\BISINDO_dataset\idle"

os.makedirs(TARGET_DIR_1, exist_ok=True)
if os.path.exists(os.path.dirname(TARGET_DIR_2)):
    os.makedirs(TARGET_DIR_2, exist_ok=True)

TARGET_COUNT = 210
IMG_SIZE = (224, 224)
MAX_WORKERS = 8

def fetch_photo_metadata(target_count=350):
    """Mengambil daftar metadata foto nyata dari API Picsum/Unsplash."""
    print("Mengambil katalog foto nyata dari internet...")
    session = requests.Session()
    photos = []
    page = 1
    while len(photos) < target_count:
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
    print(f"Katalog terkumpul: {len(photos)} foto.")
    return photos

def download_and_process_image(session, photo_id, index):
    """Mengunduh 1 foto nyata, me-resize ke 224x224 RGB JPEG, dan menyimpannya."""
    url = f"https://picsum.photos/id/{photo_id}/224/224"
    for attempt in range(3):
        try:
            res = session.get(url, timeout=12)
            if res.status_code == 200:
                img = Image.open(io.BytesIO(res.content))
                # Pastikan mode RGB dan ukuran tepat 224x224
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                if img.size != IMG_SIZE:
                    img = img.resize(IMG_SIZE, Image.Resampling.LANCZOS)
                
                filename = f"idle_real_{index:03d}.jpg"
                
                # Simpan ke lokasi 1 (Project ISYARA)
                path1 = os.path.join(TARGET_DIR_1, filename)
                img.save(path1, "JPEG", quality=92)
                
                # Simpan ke lokasi 2 (BISINDO_dataset jika ada)
                if os.path.exists(TARGET_DIR_2):
                    path2 = os.path.join(TARGET_DIR_2, filename)
                    img.save(path2, "JPEG", quality=92)
                
                return index, True, photo_id, None
            else:
                time.sleep(0.5)
        except Exception as e:
            time.sleep(1.0)
            
    return index, False, photo_id, "Max retries reached"

def main():
    print("=" * 65)
    print("  ISYARA - REAL-WORLD IDLE DATASET DOWNLOADER")
    print("=" * 65)
    print(f"Target jumlah gambar baru : {TARGET_COUNT}")
    print(f"Resolusi & Format         : {IMG_SIZE[0]}x{IMG_SIZE[1]} RGB JPEG")
    print(f"Target folder 1           : {TARGET_DIR_1}")
    print(f"Target folder 2           : {TARGET_DIR_2}")
    print("=" * 65)
    
    metadata = fetch_photo_metadata(target_count=350)
    if not metadata:
        print("Gagal mengambil metadata foto dari internet.")
        return

    # Ambil list photo_id yang valid
    photo_ids = [item['id'] for item in metadata]
    
    # Filter dan pilih target_count foto
    selected_ids = photo_ids[:TARGET_COUNT]
    
    print(f"\nMemulai pengunduhan {len(selected_ids)} gambar secara multi-threaded (workers={MAX_WORKERS})...")
    start_time = time.time()
    
    session = requests.Session()
    success_count = 0
    fail_count = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(download_and_process_image, session, pid, i + 1): i
            for i, pid in enumerate(selected_ids)
        }
        
        for future in as_completed(futures):
            idx, ok, pid, err = future.result()
            if ok:
                success_count += 1
                if success_count % 25 == 0 or success_count == len(selected_ids):
                    elapsed = time.time() - start_time
                    print(f"  [Progress] {success_count}/{len(selected_ids)} gambar berhasil diunduh ({elapsed:.1f}s)...")
            else:
                fail_count += 1
                print(f"  [Gagal #{idx}] Photo ID {pid}: {err}")
                
    total_time = time.time() - start_time
    print("\n" + "=" * 65)
    print(f"Pengunduhan Selesai!")
    print(f"Total berhasil : {success_count} gambar")
    print(f"Total gagal    : {fail_count} gambar")
    print(f"Waktu tempuh   : {total_time:.2f} detik")
    print("=" * 65)
    
    # Verifikasi jumlah total file di folder idle
    files1 = [f for f in os.listdir(TARGET_DIR_1) if f.endswith('.jpg')]
    print(f"Total gambar di folder '{TARGET_DIR_1}': {len(files1)} gambar")
    
    if os.path.exists(TARGET_DIR_2):
        files2 = [f for f in os.listdir(TARGET_DIR_2) if f.endswith('.jpg')]
        print(f"Total gambar di folder '{TARGET_DIR_2}': {len(files2)} gambar")

if __name__ == '__main__':
    main()
