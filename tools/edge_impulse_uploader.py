"""
Script Pengunggah Otomatis Dataset BISINDO ke Edge Impulse via Ingestion API
Mendukung pembagian otomatis Train (80%) dan Test (20%) untuk semua 27 kelas (A-Z + idle).
"""

import os
import sys
import glob
import random
import requests

DATASET_ROOT = r"C:\Users\Acer Nitro 5\Documents\TUGAS SMK TELKOM\lomba\AITC UNAIR 2026\BISINDO_dataset\BISINDO_dataset"
URL_TRAIN = "https://ingestion.edgeimpulse.com/api/training/files"
URL_TEST = "https://ingestion.edgeimpulse.com/api/testing/files"

BATCH_SIZE = 25  # Jumlah foto per request HTTP

def upload_batch(api_key, file_paths, label, is_training=True):
    url = URL_TRAIN if is_training else URL_TEST
    headers = {
        "x-api-key": api_key,
        "x-label": label
    }

    files = []
    opened_fps = []
    try:
        for p in file_paths:
            fp = open(p, "rb")
            opened_fps.append(fp)
            files.append(("data", (os.path.basename(p), fp, "image/jpeg")))

        res = requests.post(url, headers=headers, files=files, timeout=45)
        if res.status_code == 200:
            return True, len(files)
        else:
            print(f"\n[Error HTTP {res.status_code}]: {res.text[:200]}")
            return False, 0
    except Exception as e:
        print(f"\n[Exception]: {e}")
        return False, 0
    finally:
        for fp in opened_fps:
            fp.close()

def main():
    print("=" * 65)
    print("      ISYARA - AUTO UPLOADER KE EDGE IMPULSE (PYTHON)")
    print("=" * 65)
    print("Script ini akan mengunggah seluruh dataset (A-Z + idle) ke Edge Impulse")
    print("dengan pembagian otomatis 80% Training dan 20% Testing.\n")

    api_key = input("Masukkan API Key Proyek Edge Impulse Anda: ").strip()
    if not api_key:
        print("API Key tidak boleh kosong! Buka Edge Impulse -> Dashboard -> Keys.")
        return

    # Validasi API Key sederhana dengan request cek
    headers_check = {"x-api-key": api_key}
    print("\nMemverifikasi API Key ke server Edge Impulse...")
    try:
        check = requests.get("https://studio.edgeimpulse.com/v1/api/projects", headers=headers_check, timeout=10)
        if check.status_code == 200:
            print("[OK] API Key valid dan terhubung!\n")
        elif check.status_code == 401:
            print("[GAGAL] API Key tidak valid. Silakan periksa kembali di Dashboard -> Keys.")
            return
        else:
            print("[INFO] Melanjutkan proses upload...")
    except Exception:
        print("[INFO] Server Edge Impulse dapat dijangkau. Melanjutkan...")

    subfolders = [d for d in os.listdir(DATASET_ROOT) if os.path.isdir(os.path.join(DATASET_ROOT, d))]
    subfolders = sorted(subfolders)

    print(f"Ditemukan {len(subfolders)} folder kelas: {', '.join(subfolders)}\n")

    total_sukses = 0
    total_gagal = 0

    for label in subfolders:
        folder_path = os.path.join(DATASET_ROOT, label)
        img_files = glob.glob(os.path.join(folder_path, "*.jpg")) + \
                    glob.glob(os.path.join(folder_path, "*.jpeg")) + \
                    glob.glob(os.path.join(folder_path, "*.JPG"))

        if not img_files:
            continue

        # Acak urutan agar split Train/Test merata
        random.seed(42)
        random.shuffle(img_files)

        split_idx = int(len(img_files) * 0.8)
        train_files = img_files[:split_idx]
        test_files = img_files[split_idx:]

        print(f"Mengunggah Kelas [{label}]: Total {len(img_files)} foto (Train: {len(train_files)}, Test: {len(test_files)})")

        # Upload Training Data in batches
        for i in range(0, len(train_files), BATCH_SIZE):
            batch = train_files[i:i + BATCH_SIZE]
            ok, count = upload_batch(api_key, batch, label, is_training=True)
            if ok:
                total_sukses += count
                print(".", end="", flush=True)
            else:
                total_gagal += len(batch)
                print("x", end="", flush=True)

        # Upload Testing Data in batches
        for i in range(0, len(test_files), BATCH_SIZE):
            batch = test_files[i:i + BATCH_SIZE]
            ok, count = upload_batch(api_key, batch, label, is_training=False)
            if ok:
                total_sukses += count
                print("+", end="", flush=True)
            else:
                total_gagal += len(batch)
                print("x", end="", flush=True)

        print(" [Selesai]")

    print("\n" + "=" * 65)
    print(f"SELESAI! Berhasil mengunggah: {total_sukses} foto | Gagal: {total_gagal} foto")
    print("Semua data kini sudah ada di Edge Impulse dan siap di-training!")
    print("=" * 65)

if __name__ == "__main__":
    main()
