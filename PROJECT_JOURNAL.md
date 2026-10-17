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
- **[13 Oktober 2026]**:
  - **Peningkatan Firmware ESP32-CAM (`src/cam/main.cpp`):**
    - Mengoptimasi tuning sensor OV3660: Kontras (+2), Ketajaman (+2), Kecerahan (+1), Auto White Balance, dan pembatasan `gainceiling` untuk menghilangkan noise bintik semut pada citra 96x96 Grayscale.
    - Menambahkan endpoint HTTP `/capture` dan tombol interaktif *"Ambil Foto Dataset"* di web browser HP untuk mempermudah pengambilan data sampel langsung dari lensa kamera asli.
  - **Peningkatan Firmware ESP32-S3 (`src/s3/main.cpp`):**
    - Menerapkan peredam jitter **Majority Voting (Sliding Window 5 Frame)**: AI mensyaratkan konsensus minimal 3/5 frame agar tidak mudah reset ketika ada 1 frame noise.
    - Menambahkan filter **Confidence Gap Margin (12%)**: Selisih probabilitas peringkat 1 dan peringkat 2 harus >= 12% untuk mengabaikan tebakan ambigu.
    - Menerapkan proteksi **Anti-Repeat Hold-to-Type**: Mencegah pengetikan huruf berulang kali saat pose masih ditahan.
    - Menambahkan penanganan otomatis untuk kelas negatif (`idle` / `background`).
    - Desain ulang tampilan OLED SSD1306 agar lebih informatif (Status Kunci, Akurasi %, dan Auto-scroll kalimat).
  - **Peralatan Otomasi Dataset & Augmentasi (`tools/`):**
    - Membuat `tools/generate_idle_dataset.py` & `tools/augment_dataset.py`: Telah menghasilkan **480 gambar** variasi latar belakang untuk kelas `idle` di folder `dataset/idle/` yang siap diunggah ke Edge Impulse.
    - Membuat `tools/dataset_collector.py` untuk mengoleksi foto pose tangan langsung dari stream ESP32-CAM ke PC via burst shot.
  - **Status Build:** Kedua firmware (`esp32s3` dan `esp32cam`) berhasil dikompilasi 100% sukses.
- **[15 Oktober 2026]**:
  - **Implementasi Keyboard Braille 4x4 Tactile Matrix (`src/s3/braille_keypad.h` & `src/s3/main.cpp`):**
    - Mengintegrasikan modul push button 4x4 (16 tombol taktil S1-S16) ke ESP32-S3 menggunakan 8 pin GPIO aman (Rows: GPIO 4, 5, 6, 7 | Cols: GPIO 10, 11, 12, 13).
    - Memetakan 6 tombol tengah (`S2, S3, S6, S7, S10, S11`) menjadi bentuk fisik **2x3 Braille Cell (Titik 1 sampai 6)** yang ergonomis dan intuitif.
    - Menerapkan tombol kontrol fungsional: `S1` (Mode Switch AI BISINDO <-> Braille), `S4` (Clear All), `S5/S13` (Backspace), `S8/S15` (Enter/Commit), `S9/S14` (Spasi), `S12` (Toggle Angka/Huruf), dan `S16` (TTS / Baca Suara).
    - Menulis dekoder standar Grade 1 Braille (A-Z, Angka 0-9, dan Tanda Baca) berbasis 6-bit binary mask.
    - Menambahkan visualizer interaktif pada Layar OLED SSD1306 (preview 6 titik Braille lingkaran berongga/padat, huruf aktif, dan auto-scroll kalimat).
    - Menerapkan fitur *Auto-Commit Timeout* (850ms) dan proteksi *anti-ghosting* matrix.
    - **Status Build:** Firmware `esp32s3` berhasil dikompilasi 100% sukses (Flash 26.8%, RAM 11.9%).

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

- **[15 Oktober 2026 - PREVIEW KAMERA KE TFT ST7735S]**:
  - Menambahkan library Adafruit ST7735 dan preview frame 96x96 grayscale ke TFT 1.77 inci (diperbesar 128x128, di tengah layar 160x128) setiap frame UART diterima, sebelum inferensi. Logika AI, OLED, UART, dan teks tidak diubah.
  - Wiring TFT -> ESP32-S3: GND->GND, VCC->3.3V, SCK->GPIO12, SDA->GPIO11, RES->GPIO15, RS->GPIO14, CS->GPIO10, LEDA->3.3V. Pin 9-14 TFT (touch/duplikat) tidak dipakai.
  - Mengganti kode ESP32-CAM: WiFi dan web stream dihapus; CAM hanya mengirim frame saat menerima 'C'. Preview kini lewat TFT tanpa WiFi.
  - Jika warna/posisi TFT bergeser, coba ganti INITR_BLACKTAB dengan INITR_GREENTAB atau INITR_REDTAB di setup(). Upload kedua env (esp32s3 dan esp32cam).

- **[17 Oktober 2026 - INTEGRASI DUAL DISPLAY TFT, SUARA DFPLAYER MINI, & PENYESUAIAN PIN KEYPAD BRAILLE]**:
  - **Sinkronisasi TFT ST7735S dari Main:** Menarik kode pinning SPI TFT 1.77" dari branch `main` (SCK=GPIO12, MOSI/SDA=GPIO11, CS=GPIO10, DC/RS=GPIO14, RST/RES=GPIO15).
  - **Resolusi Konflik Pin Keypad 4x4 Braille:** Memindahkan pin kolom keypad dari GPIO 10, 11, 12, 13 (yang bertabrakan dengan SPI TFT) ke pin GPIO aman dan bebas strapping:
    - *Baris (Rows):* GPIO 4, 5, 6, 7 (INPUT_PULLUP)
    - *Kolom (Cols):* GPIO 13, 16, 21, 47 (Drive LOW / High-Z)
  - **Integrasi DFPlayer Mini + Mini Speaker 4Ω 3W (`src/s3/audio_manager.h`):**
    - Menggunakan HardwareSerial2 ESP32-S3: TX2=GPIO1 (dihubungkan via resistor 1kΩ ke RX DFPlayer), RX2=GPIO2 (dari TX DFPlayer), BUSY=GPIO42 (status memutar audio).
    - Menghubungkan mini speaker 4Ω 3W langsung ke pin SPK_1 dan SPK_2 pada DFPlayer Mini.
    - Menambahkan logika pemutaran audio non-blocking untuk:
      1. Pergantian mode sistem via tombol S1 (suara Track 50 untuk AI BISINDO, Track 51 untuk Braille).
      2. Setiap huruf terkunci dari deteksi kamera AI BISINDO (suara alfabet Track 1-26).
      3. Setiap huruf yang diketik via keyboard Braille fisik (suara alfabet Track 1-26 / angka Track 27-36).
      4. Tombol kontrol S4 (Clear), S5/S13 (Backspace), S9/S14 (Spasi), dan S16 (TTS / Baca Seluruh Kalimat).
  - **Skema Wiring Switch ON/OFF 3-Pin SPDT:**
    - Pin 1 (IN): Input daya +5V dari Baterai / USB Power.
    - Pin 2 (COMMON / OUT): Jalur rel daya 5V utama (menyalakan pin 5V ESP32-S3, ESP32-CAM, dan DFPlayer Mini).
    - Pin 3: NC (Tidak terhubung) / Indikator LED opsional.
    - Memutus daya secara fisik pada seluruh modul saat OFF untuk efisiensi baterai 0 mA quiescent.
  - **Status Build Firmware:** Kedua target (`esp32s3` dan `esp32cam`) berhasil dikompilasi 100% SUKSES tanpa error.

- **[17 Oktober 2026 - KALIBRASI MATRIKS KEYPAD 4x4, ELIMINASI RACE CONDITION OLED, & PENINGKATAN UX BRAILLE]**:
  - **Investigasi & Kalibrasi Pemetaan Pinout Matriks 4x4 Tactile:**
    - Melakukan penelusuran kontinuitas hardware pada modul 4x4 tombol taktil standar (header 8-pin: Pin 1–4 untuk Kolom C4–C1, Pin 5–8 untuk Baris R1–R4).
    - Memetakan kabel jumper fisik ESP32-S3:
      - Pin 1 (Top) = Col 4 -> GPIO 4
      - Pin 2 = Col 3 -> GPIO 5
      - Pin 3 = Col 2 -> GPIO 6
      - Pin 4 = Col 1 -> GPIO 7
      - Pin 5 = Row 1 -> GPIO 13 (Baris 1: S1, S2, S3, S4)
      - Pin 6 = Row 2 -> GPIO 16 (Baris 2: S5, S6, S7, S8)
      - Pin 7 = Row 4 -> GPIO 21 (Baris 4: S13, S14, S15, S16)
      - Pin 8 (Bottom) = Row 3 -> GPIO 47 (Baris 3: S9, S10, S11, S12)
    - **Solusi Masalah Dot Bawah di S14 & S15:**
      - Terjadi inversi pemetaan baris pada perangkat keras: Pin 7 (GPIO 21) terhubung ke baris fisik ke-4, sedangkan Pin 8 (GPIO 47) terhubung ke baris fisik ke-3.
      - Memperbarui array baris di `src/s3/braille_keypad.h` menjadi `ROW_PINS[4] = { 13, 16, 47, 21 }`.
      - Hasilnya, **Titik 3 & Titik 6 Braille** kembali presisi ke posisi ergonomisnya di tombol fisik **S10** (Kiri Bawah) dan **S11** (Kanan Bawah).
      - Tombol **S14** dan **S15** kembali ke fungsinya sebagai jalan pintas baris bawah untuk **Spasi** dan **Enter**.
  - **Eliminasi Race Condition / Corrupt Display OLED SSD1306:**
    - Pemindaian keypad yang sempat dicoba dijalankan pada FreeRTOS Task di Core 0 dihapus karena menyebabkan tabrakan buffer I2C dengan proses rendering display di Core 1 (mengakibatkan layar OLED corrupt / glitch piksel).
    - Polling scanner dikembalikan ke single-threaded non-blocking di dalam `loop()` dan loop penungguan header UART `minta_dan_baca_frame()`. Tampilan OLED kembali 100% jernih dan stabil.
  - **Peningkatan Sistem Debounce Independen Per-Tombol:**
    - Mengganti variabel debounce tunggal dengan array per-tombol `key_debounce_time[4][4]` (interval 35 ms). Hal ini mencegah tertelannya (*drop*) input saat pengetikan cepat atau saat dua tombol ditekan dalam interval berdekatan.
  - **Fitur Auto-Switch Mode Braille dari Pengetikan Fisik:**
    - Jika sistem sedang berada pada Mode AI BISINDO dan pengguna mulai menekan tombol pengetikan (S2–S16), sistem akan **otomatis beralih ke Mode Braille** seketika tanpa mengharuskan pengguna menekan tombol mode switch S1 terlebih dahulu.
  - **Indikator Badge Real-Time pada Layar OLED:**
    - Menambahkan notifikasi visual instan berdurasi 1.8 detik pada koordinat (x:46, y:38) di layar OLED (contoh: `[S10:DOT 3]`, `[S4:CLEAR]`, `[S8:ENTER]`, `[S9:SPASI]`, `[S12:[NUM]]`, `[S16:TTS]`). Pengguna mendapatkan kepastian visual seketika untuk setiap aksi tombol.
  - **Optimasi Waktu Auto-Commit Braille:**
    - Meningkatkan batas waktu penguncian karakter otomatis (*auto-commit timeout*) dari 850 ms menjadi **2500 ms (2.5 detik)** agar pengguna memiliki waktu yang cukup leluasa untuk memeriksa pratinjau huruf sebelum karakter terkunci ke dalam kalimat. Pengguna juga dapat mengunci huruf secara manual kapan saja dengan menekan tombol **S8 / S15 [ENTER]**.
  - **Banner Informatif TFT ST7735S pada Mode Braille:**
    - Saat Mode Braille aktif, kamera dipause dan layar TFT menampilkan banner visual cyan-kuning "MODE KEYBOARD BRAILLE" untuk menghemat daya dan mencegah kebingungan layar blank.
  - **Status Kompilasi (Build Verification):**
    - Environment `esp32s3`: **SUCCESS** (RAM 19.4%, Flash 16.1%).
    - Environment `esp32cam`: **SUCCESS** (RAM 8.0%, Flash 11.1%).

- **[17 Oktober 2026 - PERBAIKAN BUG TFT LAYAR PUTIH & RESTORASI SENSOR KAMERA OV3660]**:
  - **Investigasi Akar Masalah Kamera (Camera Failure Diagnosis):**
    - Manipulasi pin hardware `PWDN` (`digitalWrite(PWDN_GPIO_NUM, HIGH)`) sebelumnya ternyata mematikan daya sensor OV3660 sepenuhnya, yang berakibat fatal: register konfigurasi internal SCCB sensor (format grayscale 96x96, framing, gain, contrast) terhapus dari memori volatil sensor. Ketika sensor dihidupkan kembali, driver `esp_camera_fb_get()` mengembalikan nilai `NULL` atau mengalami kegagalan transmisi.
    - Selain itu, transmisi karakter `'S'` / `'W'` melalui jalur Serial1 sempat mengacaukan sinkronisasi *frame parser* `[0xAA, 0x55]`.
  - **Solusi Manajemen Termal Kamera yang Aman & Stabil:**
    - Menghilangkan *hardware power-down* (`PWDN`) agar register OV3660 tetap awet dan stabil.
    - Pada ESP32-CAM (`src/cam/main.cpp`), sistem kini menerapkan **FreeRTOS CPU Throttling (`vTaskDelay(pdMS_TO_TICKS(15))`)** saat tidak menerima trigger `'C'`.
    - Karena ESP32-S3 tidak mengirim perintah `'C'` saat berada di Mode Braille, beban CPU ESP32-CAM langsung anjlok ke **< 1%** dan sensor kamera tidak melakukan pemrosesan, sehingga modul kamera tetap **dingin dan anti-overheat** tanpa mengorbankan stabilitas sensor!
  - **Investigasi & Solusi Layar LCD TFT 1.77" Putih Polos (White Screen):**
    - Secara fisik, layar TFT ST7735S memiliki lampu latar (*backlight*) yang menyala putih begitu pin VCC/LEDA menerima tegangan 3.3V. Jika layar belum menerima stream visual dari kamera, layarnya akan tetap berada di kondisi bawaan (putih).
    - Sebelumnya, fungsi `tampilkan_preview_tft()` hanya terpanggil jika `minta_dan_baca_frame()` sukses. Ketika kamera terhambat, layar TFT tidak pernah diisi gambar apapun sehingga tertinggal putih polos.
    - Ditambah lagi, *timeout* pembacaan header UART di ESP32-S3 sebelumnya terlalu sempit (80 ms), sehingga frame dari OV3660 sering terputus sebelum sempat diterima.
  - **Pembaruan Firmware ESP32-S3 (`src/s3/main.cpp`):**
    - Menambahkan **Hardware Reset Pulse** pada pin `TFT_RST` (GPIO 15) di dalam `setup()` sebelum memanggil `tft.initR(INITR_BLACKTAB)`.
    - Menambahkan fungsi **`tampilkan_standby_tft()`** yang langsung dipanggil di dalam `setup()`. Begitu perangkat dinyalakan, layar TFT seketika berubah dari putih menjadi latar hitam pekat dengan judul cyan "ISYARA", subtitle kuning, status koneksi kamera, dan petunjuk navigasi hijau `[S1] Beralih ke Braille`.
    - Menyelaraskan transisi layar: saat beralih dari Mode Braille kembali ke Mode AI BISINDO, `tampilkan_standby_tft()` otomatis dipanggil untuk menyegarkan tampilan.
    - Meningkatkan *timeout* pencarian header UART menjadi 300 ms dengan tetap mempertahankan polling keypad instan di dalamnya.
  - **Status Kompilasi Final (Build Verification):**
    - Environment `esp32s3`: **SUCCESS** (Flash: 16.1%, RAM: 19.5%).
    - Environment `esp32cam`: **SUCCESS** (Flash: 11.1%, RAM: 8.0%).


