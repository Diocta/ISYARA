import os
import sys
import asyncio
import argparse
import edge_tts

# =============================================================================
# ISYARA - Audio Assets Generator (Microsoft Azure Neural TTS)
# Suara Alami, Jernih, dan Profesional untuk Assistive Device ISYARA
# =============================================================================

# Pilihan suara Microsoft Azure Neural Bahasa Indonesia:
# - id-ID-GadisNeural: Suara wanita studio yang ramah, artikulatif, hangat & jernih (Default)
# - id-ID-ArdiNeural : Suara pria penyiar yang berwibawa, formal, & profesional
DEFAULT_VOICE = "id-ID-GadisNeural"

# Deteksi otomatis direktori MicroSD eksternal (Drive D: atau E:)
def detect_sd_dir():
    candidates = ["D:/mp3", "E:/mp3", "D:/", "E:/"]
    for path in candidates:
        if os.path.exists(path):
            if path.endswith("/mp3"):
                return path
            return os.path.join(path, "mp3")
    return "D:/mp3"

BACKUP_MP3_DIR = "audio_assets/mp3"

# 1. Alfabet A - Z (Track 1 - 26)
# Pelafalan fonetik bahasa Indonesia yang jelas dan tegas
ALPHABET = [
    (1, "A", "A"),
    (2, "Be", "B"),
    (3, "Ce", "C"),
    (4, "De", "D"),
    (5, "E", "E"),
    (6, "Ef", "F"),
    (7, "Ge", "G"),
    (8, "Ha", "H"),
    (9, "I", "I"),
    (10, "Je", "J"),
    (11, "Ka", "K"),
    (12, "El", "L"),
    (13, "Em", "M"),
    (14, "En", "N"),
    (15, "O", "O"),
    (16, "Pe", "P"),
    (17, "Ki", "Q"),
    (18, "Er", "R"),
    (19, "Es", "S"),
    (20, "Te", "T"),
    (21, "U", "U"),
    (22, "Ve", "V"),
    (23, "We", "W"),
    (24, "Eks", "X"),
    (25, "Ye", "Y"),
    (26, "Zet", "Z"),
]

# 2. Angka 0 - 9 (Track 27 - 36)
NUMBERS = [
    (27, "Nol", "0"),
    (28, "Satu", "1"),
    (29, "Dua", "2"),
    (30, "Tiga", "3"),
    (31, "Empat", "4"),
    (32, "Lima", "5"),
    (33, "Enam", "6"),
    (34, "Tujuh", "7"),
    (35, "Delapan", "8"),
    (36, "Sembilan", "9"),
]

# 3. Suara Sistem & Navigasi (Track 40 - 99)
SYSTEM_AUDIO = [
    (40, "Spasi", "SPASI"),
    (41, "Hapus", "HAPUS"),
    (42, "Hapus semua", "CLEAR"),
    (50, "Mode bahasa isyarat aktif", "MODE_AI"),
    (51, "Mode keyboard braille aktif", "MODE_BRAILLE"),
    (99, "Sistem Isyara siap", "STARTUP"),
]

# 4. Kosa Kata & Frasa Esensial Bahasa Indonesia (Track 101 - 170)
WORDS = [
    (101, "Saya", "SAYA"),
    (102, "Kamu", "KAMU"),
    (103, "Dia", "DIA"),
    (104, "Kita", "KITA"),
    (105, "Kami", "KAMI"),
    (106, "Mereka", "MEREKA"),
    (107, "Makan", "MAKAN"),
    (108, "Minum", "MINUM"),
    (109, "Mau", "MAU"),
    (110, "Bisa", "BISA"),
    (111, "Tolong", "TOLONG"),
    (112, "Terima kasih", "TERIMA KASIH"),
    (113, "Sama-sama", "SAMA-SAMA"),
    (114, "Halo", "HALO"),
    (115, "Hai", "HAI"),
    (116, "Selamat pagi", "SELAMAT PAGI"),
    (117, "Selamat siang", "SELAMAT SIANG"),
    (118, "Selamat malam", "SELAMAT MALAM"),
    (119, "Apa", "APA"),
    (120, "Siapa", "SIAPA"),
    (121, "Dimana", "DIMANA"),
    (122, "Kapan", "KAPAN"),
    (123, "Kenapa", "KENAPA"),
    (124, "Bagaimana", "BAGAIMANA"),
    (125, "Ya", "YA"),
    (126, "Tidak", "TIDAK"),
    (127, "Bukan", "BUKAN"),
    (128, "Ada", "ADA"),
    (129, "Sakit", "SAKIT"),
    (130, "Dokter", "DOKTER"),
    (131, "Obat", "OBAT"),
    (132, "Rumah sakit", "RUMAH SAKIT"),
    (133, "Nama", "NAMA"),
    (134, "Bantu", "BANTU"),
    (135, "Suka", "SUKA"),
    (136, "Pergi", "PERGI"),
    (137, "Pulang", "PULANG"),
    (138, "Rumah", "RUMAH"),
    (139, "Sekolah", "SEKOLAH"),
    (140, "Teman", "TEMAN"),
    (141, "Senang", "SENANG"),
    (142, "Sedih", "SEDIH"),
    (143, "Lapar", "LAPAR"),
    (144, "Haus", "HAUS"),
    (145, "Dan", "DAN"),
    (146, "Atau", "ATAU"),
    (147, "Di", "DI"),
    (148, "Ke", "KE"),
    (149, "Dari", "DARI"),
    (150, "Ini", "INI"),
    (151, "Itu", "ITU"),
    (152, "Baik", "BAIK"),
    (153, "Sehat", "SEHAT"),
    (154, "Belajar", "BELAJAR"),
    (155, "Tidur", "TIDUR"),
    (156, "Permisi", "PERMISI"),
    (157, "Maaf", "MAAF"),
    (158, "Kamar mandi", "KAMAR MANDI"),
    (159, "Toilet", "TOILET"),
    (160, "Air", "AIR"),
    (161, "Nasi", "NASI"),
    (162, "Roti", "ROTI"),
    (163, "Duduk", "DUDUK"),
    (164, "Berdiri", "BERDIRI"),
    (165, "Jalan", "JALAN"),
    (166, "Melihat", "MELIHAT"),
    (167, "Mendengar", "MENDENGAR"),
    (168, "Bicara", "BICARA"),
    (169, "Tulis", "TULIS"),
    (170, "Baca", "BACA"),
]

ALL_AUDIO = ALPHABET + NUMBERS + SYSTEM_AUDIO + WORDS

async def generate_single_audio(track_num, speech_text, label, voice, sd_dir, backup_dir, overwrite=True):
    filename = f"{track_num:04d}.mp3"
    sd_path = os.path.join(sd_dir, filename) if sd_dir else None
    backup_path = os.path.join(backup_dir, filename)

    # Cek apakah file sudah ada dan tidak di-overwrite
    if not overwrite and os.path.exists(backup_path) and os.path.getsize(backup_path) > 1000:
        print(f"  [SKIP] #{track_num:04d} ({label}) sudah ada.")
        return True

    # Retry up to 3 times jika ada gangguan jaringan
    for attempt in range(1, 4):
        try:
            communicate = edge_tts.Communicate(speech_text, voice, rate="+0%", pitch="+0Hz")
            await communicate.save(backup_path)

            # Salin ke kartu MicroSD jika direktori tersedia
            if sd_path:
                with open(backup_path, 'rb') as f_in, open(sd_path, 'wb') as f_out:
                    f_out.write(f_in.read())

            file_size = os.path.getsize(backup_path)
            print(f"  [OK] #{track_num:04d} -> \"{speech_text}\" ({label}) [{file_size} bytes]")
            return True
        except Exception as e:
            if attempt == 3:
                print(f"  [ERROR] #{track_num:04d} (\"{speech_text}\") gagal: {e}")
                return False
            await asyncio.sleep(0.5)

async def main():
    parser = argparse.ArgumentParser(description="ISYARA Professional Audio Assets Generator")
    parser.add_argument("--voice", type=str, default=DEFAULT_VOICE,
                        help=f"Edge-TTS voice (default: {DEFAULT_VOICE}, pilihan: id-ID-GadisNeural, id-ID-ArdiNeural)")
    parser.add_argument("--sd-dir", type=str, default=None,
                        help="Path ke direktori mp3 di MicroSD (misal: D:/mp3). Jika kosong, deteksi otomatis.")
    parser.add_argument("--no-overwrite", action="store_true",
                        help="Lewati file yang sudah ada.")
    args = parser.parse_args()

    sd_dir = args.sd_dir if args.sd_dir else detect_sd_dir()
    os.makedirs(BACKUP_MP3_DIR, exist_ok=True)
    if sd_dir:
        os.makedirs(sd_dir, exist_ok=True)

    print("=" * 65)
    print(" ISYARA Audio Assets Generator (Microsoft Azure Neural TTS)")
    print("=" * 65)
    print(f" Suara Terpilih     : {args.voice}")
    print(f" Direktori MicroSD  : {sd_dir if sd_dir else '(Tidak terdeteksi)'}")
    print(f" Direktori Cadangan : {BACKUP_MP3_DIR}")
    print(f" Total File MP3     : {len(ALL_AUDIO)} track")
    print(f" Overwrite          : {'Tidak' if args.no_overwrite else 'Ya (Perbarui seluruh sampling)'}")
    print("=" * 65)
    print("Memulai pembuatan sampling suara profesional...\n")

    success_count = 0
    for track_num, speech_text, label in ALL_AUDIO:
        ok = await generate_single_audio(
            track_num, speech_text, label,
            args.voice, sd_dir, BACKUP_MP3_DIR,
            overwrite=not args.no_overwrite
        )
        if ok:
            success_count += 1
        await asyncio.sleep(0.04) # Delay halus agar koneksi stabil

    print("\n" + "=" * 65)
    print(f"Selesai! Berhasil membuat {success_count}/{len(ALL_AUDIO)} file audio berkualitas tinggi.")
    if sd_dir and os.path.exists(sd_dir):
        print(f"Seluruh file MP3 telah disinkronkan langsung ke kartu MicroSD: {sd_dir}")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
