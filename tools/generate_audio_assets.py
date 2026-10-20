import os
import sys
import time
from gtts import gTTS

# Target direktori di MicroSD (Drive E:) dan cadangan di proyek
SD_MP3_DIR = "E:/mp3"
BACKUP_MP3_DIR = "audio_assets/mp3"

os.makedirs(SD_MP3_DIR, exist_ok=True)
os.makedirs(BACKUP_MP3_DIR, exist_ok=True)

# 1. Alfabet A - Z (Track 1 - 26)
# Menggunakan pelafalan fonetik bahasa Indonesia yang jelas
ALPHABET = [
    (1, "a", "a"),
    (2, "be", "b"),
    (3, "ce", "c"),
    (4, "de", "d"),
    (5, "e", "e"),
    (6, "ef", "f"),
    (7, "ge", "g"),
    (8, "ha", "h"),
    (9, "i", "i"),
    (10, "je", "j"),
    (11, "ka", "k"),
    (12, "el", "l"),
    (13, "em", "m"),
    (14, "en", "n"),
    (15, "o", "o"),
    (16, "pe", "p"),
    (17, "ki", "q"),
    (18, "er", "r"),
    (19, "es", "s"),
    (20, "te", "t"),
    (21, "u", "u"),
    (22, "fe", "v"),
    (23, "we", "w"),
    (24, "eks", "x"),
    (25, "ye", "y"),
    (26, "zet", "z"),
]

# 2. Angka 0 - 9 (Track 27 - 36)
NUMBERS = [
    (27, "nol", "0"),
    (28, "satu", "1"),
    (29, "dua", "2"),
    (30, "tiga", "3"),
    (31, "empat", "4"),
    (32, "lima", "5"),
    (33, "enam", "6"),
    (34, "tujuh", "7"),
    (35, "delapan", "8"),
    (36, "sembilan", "9"),
]

# 3. Suara Sistem & Kontrol (Track 40 - 99)
SYSTEM_AUDIO = [
    (40, "spasi", "SPASI"),
    (41, "hapus", "HAPUS"),
    (42, "hapus semua", "CLEAR"),
    (50, "mode bahasa isyarat aktif", "MODE_AI"),
    (51, "mode keyboard braille aktif", "MODE_BRAILLE"),
    (99, "sistem isyara siap", "STARTUP"),
]

# 4. Kosa Kata Esensial Bahasa Indonesia (Track 101+)
# Kata-kata harian, medis, kebutuhan dasar komunikasi inklusif
WORDS = [
    (101, "saya", "SAYA"),
    (102, "kamu", "KAMU"),
    (103, "dia", "DIA"),
    (104, "kita", "KITA"),
    (105, "kami", "KAMI"),
    (106, "mereka", "MEREKA"),
    (107, "makan", "MAKAN"),
    (108, "minum", "MINUM"),
    (109, "mau", "MAU"),
    (110, "bisa", "BISA"),
    (111, "tolong", "TOLONG"),
    (112, "terima kasih", "TERIMA KASIH"),
    (113, "sama-sama", "SAMA-SAMA"),
    (114, "halo", "HALO"),
    (115, "hai", "HAI"),
    (116, "selamat pagi", "SELAMAT PAGI"),
    (117, "selamat siang", "SELAMAT SIANG"),
    (118, "selamat malam", "SELAMAT MALAM"),
    (119, "apa", "APA"),
    (120, "siapa", "SIAPA"),
    (121, "dimana", "DIMANA"),
    (122, "kapan", "KAPAN"),
    (123, "kenapa", "KENAPA"),
    (124, "bagaimana", "BAGAIMANA"),
    (125, "ya", "YA"),
    (126, "tidak", "TIDAK"),
    (127, "bukan", "BUKAN"),
    (128, "ada", "ADA"),
    (129, "sakit", "SAKIT"),
    (130, "dokter", "DOKTER"),
    (131, "obat", "OBAT"),
    (132, "rumah sakit", "RUMAH SAKIT"),
    (133, "nama", "NAMA"),
    (134, "bantu", "BANTU"),
    (135, "suka", "SUKA"),
    (136, "pergi", "PERGI"),
    (137, "pulang", "PULANG"),
    (138, "rumah", "RUMAH"),
    (139, "sekolah", "SEKOLAH"),
    (140, "teman", "TEMAN"),
    (141, "senang", "SENANG"),
    (142, "sedih", "SEDIH"),
    (143, "lapar", "LAPAR"),
    (144, "haus", "HAUS"),
    (145, "dan", "DAN"),
    (146, "atau", "ATAU"),
    (147, "di", "DI"),
    (148, "ke", "KE"),
    (149, "dari", "DARI"),
    (150, "ini", "INI"),
    (151, "itu", "ITU"),
    (152, "baik", "BAIK"),
    (153, "sehat", "SEHAT"),
    (154, "belajar", "BELAJAR"),
    (155, "tidur", "TIDUR"),
    (156, "permisi", "PERMISI"),
    (157, "maaf", "MAAF"),
    (158, "kamar mandi", "KAMAR MANDI"),
    (159, "toilet", "TOILET"),
    (160, "air", "AIR"),
    (161, "nasi", "NASI"),
    (162, "roti", "ROTI"),
    (163, "duduk", "DUDUK"),
    (164, "berdiri", "BERDIRI"),
    (165, "jalan", "JALAN"),
    (166, "melihat", "MELIHAT"),
    (167, "mendengar", "MENDENGAR"),
    (168, "bicara", "BICARA"),
    (169, "tulis", "TULIS"),
    (170, "baca", "BACA"),
]

ALL_AUDIO = ALPHABET + NUMBERS + SYSTEM_AUDIO + WORDS

print(f"Total track yang akan dibuat: {len(ALL_AUDIO)} file MP3")
print("Memulai proses pembuatan file suara ke Drive E: ...")

success_count = 0
for track_num, speech_text, label in ALL_AUDIO:
    filename = f"{track_num:04d}.mp3"
    sd_path = os.path.join(SD_MP3_DIR, filename)
    backup_path = os.path.join(BACKUP_MP3_DIR, filename)

    # Lewati jika sudah pernah dibuat
    if os.path.exists(sd_path) and os.path.getsize(sd_path) > 500:
        print(f"  [SKIP] #{track_num:04d} ({label}) sudah ada.")
        success_count += 1
        continue

    try:
        tts = gTTS(text=speech_text, lang='id', slow=False)
        tts.save(sd_path)
        # Salin juga ke folder backup proyek
        with open(sd_path, 'rb') as f_in, open(backup_path, 'wb') as f_out:
            f_out.write(f_in.read())
        print(f"  [OK] #{track_num:04d} -> \"{speech_text}\" ({label})")
        success_count += 1
        time.sleep(0.15) # Jeda ringan agar request gTTS lancar
    except Exception as e:
        print(f"  [ERROR] Gagal pada #{track_num:04d} (\"{speech_text}\"): {e}")

print(f"\nSelesai! Berhasil membuat {success_count}/{len(ALL_AUDIO)} file audio di {SD_MP3_DIR}")

