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

- **[13 Oktober 2026 - UART HANDSHAKE DIAGNOSTIK]**:
  - Daya ESP32-CAM berhasil dipastikan menggunakan pin 5V yang benar dari expansion board dengan adaptor eksternal 12V pada input expansion. ESP32-CAM dapat menyala, terhubung Wi-Fi, dan menyediakan web stream.
  - Karena OLED tetap menampilkan status handshake setelah masalah daya selesai, fokus diagnosis dipindahkan dari daya ke komunikasi UART. AI Edge Impulse belum menjadi sumber masalah karena inferensi hanya dijalankan setelah frame 9216 byte diterima penuh.
  - Mengubah baud rate komunikasi UART pada `src/s3/main.cpp` dan `src/cam/main.cpp` dari `230400` menjadi `460800` sebagai kompromi antara kecepatan transfer dan stabilitas kabel.
  - Memperpanjang timeout pencarian header menjadi 1000 ms dan timeout penerimaan frame menjadi 1000 ms.
  - Memperbaiki parser header pada ESP32-S3 agar mencari pasangan byte `0xAA 0x55` secara berurutan, bukan hanya membaca dua byte sekaligus. Ini mencegah header terlewat jika byte tiba tidak tepat bersamaan.
  - Menambahkan status diagnostik UART pada OLED dan Serial Monitor untuk membedakan header tidak diterima dari frame yang tidak lengkap.
  - Menambahkan validasi ukuran frame di ESP32-CAM; frame hanya dikirim jika ukurannya tepat 9216 byte sesuai input model 96x96 grayscale.
  - Setelah perubahan ini, kedua firmware perlu di-upload ulang: environment `esp32cam` ke ESP32-CAM dan environment `esp32s3` ke ESP32-S3.

- **[14 Oktober 2026 - KONFIGURASI MEMORI ESP32-S3 N16R8]**:
  - Log Serial Monitor ESP32-S3 menunjukkan bahwa UART telah menerima data kamera setidaknya sebagian (`6826/9216` byte), sehingga pin `U0T` dan `U0R` ESP32-CAM serta GPIO17/GPIO18 ESP32-S3 bukan lagi tersangka utama.
  - Log juga menunjukkan `Failed to allocate tensor arena`. Model BISINDO membutuhkan arena TensorFlow Lite hingga 256403 byte, tetapi sebelumnya dialokasikan secara dinamis dari heap internal ESP32-S3 dan gagal mendapatkan blok memori berukuran besar.
  - Modul ESP32-S3 yang digunakan bertanda N16R8, sedangkan definisi board PlatformIO semula adalah varian N8 tanpa PSRAM. Environment `esp32s3` diperbarui untuk flash 16 MB, partisi `default_16MB.csv`, dan tipe memori `qio_opi` agar PSRAM OPI digunakan.
  - Arena model Edge Impulse tetap dialokasikan dinamis, tetapi alokasi berukuran besar (minimal 64 KB) kini diarahkan ke PSRAM melalui `heap_caps_calloc()` bila PSRAM tersedia. Cara ini menghindari kegagalan alokasi heap sekaligus mempertahankan RAM internal untuk OLED, UART, dan Arduino.
  - Menambahkan log Serial Monitor `PSRAM: <total> byte, bebas: <jumlah> byte` saat ESP32-S3 menyala untuk memverifikasi PSRAM benar-benar aktif.
  - Pengujian perangkat mengonfirmasi PSRAM aktif (sekitar 8 MB). Inisialisasi model kemudian menemukan batas default 10 buffer overflow Edge Impulse terlalu kecil untuk model ini, menghasilkan pesan `Failed to allocate persistent buffer ... EI_MAX_OVERFLOW_BUFFER_COUNT` dan reset berulang.
  - Menetapkan `EI_MAX_OVERFLOW_BUFFER_COUNT=128` pada environment `esp32s3` agar buffer persisten kecil yang diperlukan model dapat dialokasikan. Header porting Edge Impulse disesuaikan agar batas khusus ESP32-S3 tidak menimpa nilai konfigurasi proyek tersebut. Jika inferensi tetap gagal, OLED sekarang menampilkan `ERR` dan Serial Monitor mencetak kode error tanpa membuat program berhenti pada status siap.
  - Backtrace berikutnya menunjukkan `CORRUPT HEAP: Bad tail` saat runtime mereset arena model. Penyebabnya adalah arena bawaan model terkompilasi hanya 246720 byte, lebih kecil daripada kebutuhan model 256403 byte pada metadata. Konfigurasi `EI_TENSOR_ARENA_SIZE=286720` ditambahkan sebagai arena 280 KB di PSRAM, sehingga tersedia margin 30317 byte di atas kebutuhan metadata dan model tidak perlu menulis melewati arena/buffer overflow.
  - Hanya firmware environment `esp32s3` yang perlu di-upload ulang untuk perubahan ini. Firmware `esp32cam` dan wiring tidak berubah pada tahap ini.

- **[14 Oktober 2026 - MIGRASI RUNTIME TENSORFLOW LITE]**:
  - Runtime EON Compiler dari deployment awal menghasilkan `CORRUPT HEAP` saat model mereset overflow buffer pada ESP32-S3, walaupun PSRAM 8 MB telah terdeteksi dengan benar.
  - Library deployment baru dari Edge Impulse dipilih menggunakan opsi **TensorFlow Lite** (bukan EON Compiler). Metadata library baru menetapkan `EI_CLASSIFIER_COMPILED = 0`, sehingga inferensi memakai TensorFlow Lite Micro standar.
  - Library EON sebelumnya dipertahankan sebagai cadangan pada `lib/BISINDO_inferencing_eon_backup/`. Library TensorFlow Lite baru dipasang sebagai `lib/BISINDO_inferencing/`.
  - Konfigurasi khusus EON (`EI_MAX_OVERFLOW_BUFFER_COUNT` dan `EI_TENSOR_ARENA_SIZE`) dihapus dari `platformio.ini` karena tidak digunakan oleh runtime TensorFlow Lite Micro standar.
  - Override `ei_calloc()` pada firmware ESP32-S3 tetap digunakan untuk mengarahkan alokasi besar TensorFlow Lite Micro ke PSRAM.
  - Hanya environment `esp32s3` yang perlu di-build dan di-upload ulang. ESP32-CAM serta wiring UART tidak berubah.

- **[14 Oktober 2026 - ARENA TENSORFLOW LITE MICRO]**:
  - Pengujian runtime TensorFlow Lite standar mencapai `AllocateTensors()`, tetapi gagal dengan kode `EI_IMPULSE_TFLITE_ERROR (-3)`. Firmware tidak reboot dan OLED menampilkan `ERR`, sehingga jalur kamera, UART, PSRAM, dan error handling sudah bekerja.
  - Library hasil deployment menyediakan arena 256403 byte, tetapi ukuran tersebut tidak cukup untuk tensor, metadata, alignment, dan scratch buffer TensorFlow Lite Micro pada ESP32-S3.
  - Menambahkan konfigurasi `EI_CLASSIFIER_TFLITE_ARENA_SIZE=524288` (512 KB) pada environment `esp32s3`.
  - Runtime `tflite_micro.h` diperbarui agar memakai ukuran terbesar antara kebutuhan metadata model dan konfigurasi proyek, untuk alokasi arena serta konstruktor `MicroInterpreter`.
  - Arena 512 KB tetap dialokasikan dinamis melalui `ei_calloc()` ke PSRAM; RAM internal tetap tersedia untuk UART, OLED, dan sistem Arduino.
  - Hanya firmware `esp32s3` perlu di-upload ulang setelah build berhasil. ESP32-CAM dan wiring tidak berubah.

- **[15 Oktober 2026 - UX HOLD-TO-TYPE OLED]**:
  - Pengujian perangkat berhasil mengenali beberapa pose BISINDO A-I dan menampilkan status `Idle` saat tidak ada pose. Perbedaan akurasi antarhuruf, khususnya kecenderungan kelas `I`, dicatat sebagai prioritas perbaikan dataset dan penambahan kelas `idle/background` pada pelatihan berikutnya.
  - Mengganti label teks `Kunci:` pada OLED dengan ikon jam saat pose sedang ditahan dan ikon centang saat huruf berhasil disimpan. Progress bar tahan pose tetap dipertahankan.
  - Menambahkan state `menunggu_lepas_tangan`: satu pose hanya dapat menambahkan satu huruf. Setelah huruf tersimpan, sistem menampilkan centang dan menunggu tangan/pose hilang selama 600 ms sebelum menerima huruf berikutnya. Ini mencegah teks berulang seperti `EEEE` atau `IIII` saat pose terus ditahan.
  - Teks hasil tidak dihapus otomatis; penghapusan, spasi, dan bersihkan teks direncanakan pada tahap tombol Braille/push button.
  - Hanya firmware environment `esp32s3` perlu di-upload ulang. ESP32-CAM, model, dan wiring tidak berubah.
