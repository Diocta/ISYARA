"""
Upload dataset BISINDO ke Edge Impulse project ISYARA_BISINDO_v2
Auto-mode: tanpa input manual, dengan retry logic.
"""

import os, sys, glob, random, time, requests

API_KEY = "ei_d7f3a3d8d7c896f7dd2d3442ac08fc88ea0576b3313e5cd7"
DATASET_ROOT = r"C:\Users\Acer Nitro 5\Documents\TUGAS SMK TELKOM\lomba\AITC UNAIR 2026\BISINDO_dataset\BISINDO_dataset"
URL_TRAIN = "https://ingestion.edgeimpulse.com/api/training/files"
URL_TEST  = "https://ingestion.edgeimpulse.com/api/testing/files"
BATCH_SIZE = 20
MAX_RETRIES = 3

def upload_batch(file_paths, label, is_training=True):
    url = URL_TRAIN if is_training else URL_TEST
    headers = {"x-api-key": API_KEY, "x-label": label}

    for attempt in range(MAX_RETRIES):
        opened_fps = []
        try:
            files = []
            for p in file_paths:
                fp = open(p, "rb")
                opened_fps.append(fp)
                files.append(("data", (os.path.basename(p), fp, "image/jpeg")))

            res = requests.post(url, headers=headers, files=files, timeout=60)
            if res.status_code == 200:
                return True, len(files)
            else:
                print(f"\n  [HTTP {res.status_code}] {res.text[:150]}")
                return False, 0
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"r", end="", flush=True)
                time.sleep(3 * (attempt + 1))
            else:
                print(f"\n  [GAGAL setelah {MAX_RETRIES} retry]: {e}")
                return False, 0
        finally:
            for fp in opened_fps:
                fp.close()

def main():
    print("=" * 65)
    print("  ISYARA - UPLOAD KE EDGE IMPULSE v2 (CLASSIFICATION)")
    print("=" * 65)

    # Verify API key
    print("Verifikasi API Key...", end=" ", flush=True)
    try:
        r = requests.get("https://ingestion.edgeimpulse.com/api/training/files",
                         headers={"x-api-key": API_KEY}, timeout=10)
        print(f"OK (status {r.status_code})")
    except Exception as e:
        print(f"Warning: {e}")

    subfolders = sorted([d for d in os.listdir(DATASET_ROOT)
                         if os.path.isdir(os.path.join(DATASET_ROOT, d))])
    print(f"\nDitemukan {len(subfolders)} kelas: {', '.join(subfolders)}\n")

    total_ok = 0
    total_fail = 0

    for idx, label in enumerate(subfolders):
        folder = os.path.join(DATASET_ROOT, label)
        imgs = [os.path.join(folder, f) for f in sorted(os.listdir(folder))
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not imgs:
            continue

        random.seed(42)
        random.shuffle(imgs)
        split = int(len(imgs) * 0.8)
        train = imgs[:split]
        test  = imgs[split:]

        print(f"[{idx+1}/{len(subfolders)}] {label}: {len(imgs)} foto (Train:{len(train)}, Test:{len(test)}) ", end="", flush=True)

        for i in range(0, len(train), BATCH_SIZE):
            ok, n = upload_batch(train[i:i+BATCH_SIZE], label, True)
            if ok:
                total_ok += n
                print(".", end="", flush=True)
            else:
                total_fail += len(train[i:i+BATCH_SIZE])
                print("x", end="", flush=True)

        for i in range(0, len(test), BATCH_SIZE):
            ok, n = upload_batch(test[i:i+BATCH_SIZE], label, False)
            if ok:
                total_ok += n
                print("+", end="", flush=True)
            else:
                total_fail += len(test[i:i+BATCH_SIZE])
                print("x", end="", flush=True)

        print(" OK")

    print("\n" + "=" * 65)
    print(f"SELESAI! Berhasil: {total_ok} | Gagal: {total_fail}")
    print("=" * 65)

if __name__ == "__main__":
    main()
