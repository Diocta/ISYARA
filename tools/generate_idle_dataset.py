"""
Script untuk menghasilkan gambar variasi background / idle 96x96 grayscale
untuk melatih kelas 'idle' (negatif) di Edge Impulse.
"""
import os
import numpy as np
from PIL import Image, ImageFilter

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset", "idle")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NUM_SAMPLES = 80
WIDTH, HEIGHT = 96, 96

print(f"Membuat {NUM_SAMPLES} gambar synthetic background/idle ke {OUTPUT_DIR}...")

for i in range(NUM_SAMPLES):
    bg_type = i % 5
    
    if bg_type == 0:
        # Polos dengan variasi intensitas cahaya dinding (dinding terang hingga redup)
        base_val = np.random.randint(40, 220)
        noise = np.random.normal(0, np.random.uniform(2, 8), (HEIGHT, WIDTH))
        arr = np.clip(base_val + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr, mode='L')
        
    elif bg_type == 1:
        # Gradien cahaya (simulasi pencahayaan lampu dari satu sisi)
        grad_dir = np.random.choice(['horiz', 'vert', 'diag'])
        val_start = np.random.randint(30, 120)
        val_end = np.random.randint(140, 240)
        
        if grad_dir == 'horiz':
            gradient = np.tile(np.linspace(val_start, val_end, WIDTH), (HEIGHT, 1))
        elif grad_dir == 'vert':
            gradient = np.tile(np.linspace(val_start, val_end, HEIGHT)[:, None], (1, WIDTH))
        else:
            x = np.linspace(val_start, val_end, WIDTH)
            y = np.linspace(0, 50, HEIGHT)[:, None]
            gradient = (x + y) / 1.2
            
        noise = np.random.normal(0, 5, (HEIGHT, WIDTH))
        arr = np.clip(gradient + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr, mode='L')
        
    elif bg_type == 2:
        # Tekstur permukaan meja / lantai / ruangan dengan noise terfilter blur
        base_val = np.random.randint(60, 190)
        raw_noise = np.random.randint(0, 255, (HEIGHT // 4, WIDTH // 4), dtype=np.uint8)
        noise_img = Image.fromarray(raw_noise, mode='L').resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)
        noise_arr = np.array(noise_img).astype(np.float32) - 128.0
        arr = np.clip(base_val + (noise_arr * np.random.uniform(0.15, 0.45)), 0, 255).astype(np.uint8)
        img = Image.fromarray(arr, mode='L')
        
    elif bg_type == 3:
        # Simulasi garis/tepi latar belakang (misal sudut dinding, bingkai pintu)
        base_val = np.random.randint(80, 180)
        arr = np.full((HEIGHT, WIDTH), base_val, dtype=np.uint8)
        line_pos = np.random.randint(20, 76)
        line_val = np.random.randint(20, 240)
        if np.random.rand() > 0.5:
            arr[:, line_pos:line_pos+np.random.randint(3, 12)] = line_val
        else:
            arr[line_pos:line_pos+np.random.randint(3, 12), :] = line_val
        noise = np.random.normal(0, 6, (HEIGHT, WIDTH))
        arr = np.clip(arr.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr, mode='L').filter(ImageFilter.GaussianBlur(radius=np.random.uniform(0.5, 2.0)))
        
    else:
        # Pola bintik atau kontras rendah (bayangan lembut ruangan)
        base_val = np.random.randint(50, 200)
        cx, cy = np.random.randint(20, 76), np.random.randint(20, 76)
        y, x = np.ogrid[:HEIGHT, :WIDTH]
        dist = np.sqrt((x - cx)**2 + (y - cy)**2)
        radius = np.random.randint(25, 60)
        shadow = np.exp(-(dist**2)/(2 * (radius**2))) * np.random.randint(30, 80)
        sign = 1 if np.random.rand() > 0.5 else -1
        arr = np.clip(base_val + sign * shadow, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr, mode='L')

    filename = os.path.join(OUTPUT_DIR, f"idle_synthetic_{i+1:03d}.jpg")
    img.save(filename, quality=95)

print(f"Berhasil membuat {NUM_SAMPLES} gambar idle di folder '{OUTPUT_DIR}'.")
