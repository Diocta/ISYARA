# ISYARA Project Journal

Dokumen ini berfungsi sebagai rekam jejak (changelog) dan dokumentasi berkelanjutan untuk proyek ISYARA. Dokumen ini akan terus diperbarui seiring berjalannya pengembangan alat agar seluruh anggota tim dan AI pendamping mengetahui konteks struktur proyek dari awal hingga akhir.

## Fase 1: Analisis Kebutuhan & Arsitektur (Selesai)
- **Konsep:** Alat penerjemah komunikasi 2-in-1 (Bahasa Isyarat via Kamera & Input Teks via Tombol Braille).
- **Arsitektur Utama:** Menggunakan arsitektur *Master-Slave*.
  - **ESP32-S3 (Master):** Otak utama yang memproses Machine Learning (TensorFlow Lite), membaca input Braille, dan mengontrol layar serta suara.
  - **ESP32-CAM (Slave):** Hanya bertugas sebagai lensa kamera yang menjepret gambar dan mengirimkannya ke ESP32-S3 via komunikasi UART (Kabel Jumper).
- **UI/Display (Dual Screen):**
  - **OLED 0.96" (I2C):** Didedikasikan khusus untuk menampilkan Teks (tebakan isyarat & ketikan braille).
  - **TFT LCD 1.77" / 2.4" (SPI):** Didedikasikan khusus untuk *viewfinder* / jendela live-video dari kamera agar pengguna mudah mengarahkan tangan.
- **Komponen Ekstra:**
  - DFPlayer Mini + MicroSD + Speaker untuk output suara (mp3).
  - 6 Tombol Tactile untuk ketikan Braille (titik 1-6) + 1 Tombol Ekstra (Spasi/Hapus).
  - 1 Tombol Toggle/Push untuk mengganti mode (Isyarat <-> Braille).

## Fase 2: Rencana Pengembangan (Akan Dikerjakan)
1. **[Selesai] Konfigurasi Workspace:** Mengubah `platformio.ini` agar mendukung dua board (ESP32-S3 dan ESP32-CAM) di dalam satu folder proyek.
2. **[Selesai] Setup Layar Teks (OLED):** Menulis kode untuk ESP32-S3 agar bisa menampilkan teks sapaan / status ke OLED 0.96".
3. **[Selesai] Uji Komunikasi Dua ESP32:** Menyambungkan ESP32-CAM dan ESP32-S3 dengan kabel jumper, lalu membuat program sederhana (Hello World) untuk memastikan data bisa dikirim antar-board.
4. **Logika Tombol Braille:** Memprogram pembacaan 6+1 tombol matriks/taktil agar menghasilkan karakter sesuai standar Braille.
5. **Streaming Gambar Kamera:** Memprogram ESP32-CAM mengambil gambar dan mengirim byte gambarnya ke ESP32-S3, lalu menampilkannya di TFT LCD (jika layar sudah datang).
6. **Integrasi Machine Learning (AI):** Memasukkan model AI (Edge Impulse) ke ESP32-S3 untuk mengklasifikasi gambar yang masuk.
7. **Integrasi Suara & Finalisasi:** Menyatukan fungsi logika Mode Switch dan menambahkan *output* suara dari DFPlayer.

---
*Catatan Log Aktivitas:*
- **[10 Oktober 2026]**: 
  - Memisahkan folder *source code* menjadi `src/s3/` dan `src/cam/`.
  - Mengubah `platformio.ini` agar membaca masing-masing folder berdasarkan *environment* yang dipilih.
  - Membuat kode pengetesan OLED dan penerima UART (Serial1) di ESP32-S3.
  - Membuat kode pengirim tes "Ping" di ESP32-CAM.
  - **[UPDATE]** Uji komunikasi UART dan OLED berhasil (Teks tampil di layar).
  - Pivot (Ubah Fokus): Melompat ke fase Pembuatan AI & Dataset (Machine Learning) sesuai permintaan pengguna. Menulis ulang kode ESP32-CAM untuk uji fungsi lensa via Web Server.
- **[11 Oktober 2026]**:
  - Berhasil menguji stream kamera via web. Ditemukan bahwa sensor kamera adalah **OV3660 (3MP)**.
  - Mengoptimasi kode ESP32-CAM khusus OV3660: resolusi dikunci ke QVGA (320x240), `jpeg_quality = 15`, `fb_count = 2`, dan `grab_mode = CAMERA_GRAB_LATEST` agar dingin, ringan, dan tidak ada lag/delay.
  - Pengguna berhasil melatih model Machine Learning pertama di Edge Impulse (Huruf A sampai I) menggunakan arsitektur MobileNetV2 96x96 (Akurasi 72.1%).
  - Mempersiapkan proses *deployment* library Edge Impulse ke PlatformIO ESP32-S3.
- **[12 Oktober 2026]**:
  - Berhasil mengintegrasikan library Edge Impulse `BISINDO_inferencing` ke dalam proyek.
  - Menulis kode produksi untuk `src/cam/main.cpp`: Menangkap citra 96x96 Grayscale (OV3660), menyiarkan cermin langsung ke browser via HTTP MJPEG, serta mentransmisikan 9216 bytes piksel secara simultan ke ESP32-S3 via UART berkecepatan tinggi (921600 baud).
  - Menulis kode produksi untuk `src/s3/main.cpp`: Membaca 9216 bytes piksel UART, menjalankan inferensi AI Edge Impulse `run_classifier()`, menerapkan logika *hold-to-type* (1.2 detik), dan menampilkan hasil prediksi serta kalimat yang tersusun ke layar OLED SSD1306.
  - **Kompilasi Sukses 100%:** Kedua environment (`esp32s3` dan `esp32cam`) berhasil di-*build* tanpa error sama sekali.
  - **[UPDATE - HANDSHAKE & THRESHOLD]**: 
    - Menerapkan arsitektur protokol **Handshake (Ketuk Pintu)**: ESP32-S3 meminta 1 frame secara eksplisit menggunakan perintah `'C'` hanya ketika siap menjalankan inferensi. Ini menyelesaikan masalah buffer macet dan mengembalikan kelancaran web streaming di HP ke FPS maksimal.
    - Menambahkan ambang batas **Confidence Threshold (55%)**: Jika tidak ada pose tangan atau akurasi di bawah 55%, sistem masuk ke mode `Idle (-)` dan tidak akan mengetik huruf salah ke dalam kalimat.
    - Kedua firmware berhasil dikompilasi 100% sukses.

