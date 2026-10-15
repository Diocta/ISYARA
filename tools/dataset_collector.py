"""
Script Kolektor Dataset Langsung dari ESP32-CAM via HTTP
Penggunaan:
1. Hubungkan PC/laptop ke Wi-Fi yang sama dengan ESP32-CAM.
2. Jalankan: python tools/dataset_collector.py
3. Masukkan IP ESP32-CAM (misal 192.168.43.120)
4. Pilih label (misal A, B, atau idle)
5. Masukkan jumlah foto burst (misal 15 foto)
6. Foto otomatis disimpan ke dataset/<label>/
"""

import os
import time
import urllib.request
import urllib.error

DATASET_ROOT = os.path.join(os.path.dirname(__file__), "..", "dataset")

def capture_image(cam_ip, target_folder, label_name, index):
    url = f"http://{cam_ip}/capture?t={int(time.time() * 1000)}"
    filename = os.path.join(target_folder, f"{label_name}_{int(time.time())}_{index:02d}.jpg")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'ISYARA-Collector/1.0'})
        with urllib.request.urlopen(req, timeout=4) as response:
            if response.status == 200:
                with open(filename, 'wb') as f:
                    f.write(response.read())
                print(f"  [OK] Tersimpan: {os.path.basename(filename)}")
                return True
    except Exception as e:
        print(f"  [GAGAL] Gagal mengambil foto: {e}")
    return False

def main():
    print("="*55)
    print("    ISYARA - ESP32-CAM DATASET COLLECTOR TOOL")
    print("="*55)
    
    default_ip = "192.168.4.1"
    cam_ip = input(f"Masukkan IP Address ESP32-CAM [{default_ip}]: ").strip()
    if not cam_ip:
        cam_ip = default_ip

    while True:
        print("\n--- MENU PENGUMPULAN DATASET ---")
        label = input("Ketik Label Huruf (misal: A, B, C, ..., idle atau 'q' untuk keluar): ").strip()
        if label.lower() == 'q':
            break
        if not label:
            continue

        label_folder = os.path.join(DATASET_ROOT, label)
        os.makedirs(label_folder, exist_ok=True)

        count_str = input(f"Berapa banyak foto burst yang ingin diambil untuk '{label}'? [default: 10]: ").strip()
        count = int(count_str) if count_str.isdigit() else 10

        delay_str = input("Jeda antar foto dalam detik (misal: 0.5 atau 1.0) [default: 0.6]: ").strip()
        delay = float(delay_str) if delay_str.replace('.', '', 1).isdigit() else 0.6

        print(f"\nBersiap! Mengambil {count} foto untuk label '{label}'...")
        print("Silakan variasikan posisi/kemiringan tangan Anda sedikit di depan lensa.")
        for sec in range(3, 0, -1):
            print(f"Mulai dalam {sec}...")
            time.sleep(1)

        sukses = 0
        for i in range(1, count + 1):
            if capture_image(cam_ip, label_folder, label, i):
                sukses += 1
            time.sleep(delay)

        print(f"\nSelesai! Berhasil menyimpan {sukses}/{count} foto ke: {label_folder}")

if __name__ == "__main__":
    main()
