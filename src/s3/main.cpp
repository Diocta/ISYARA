/*
 * ISYARA - ESP32-S3 Master Firmware
 * Menggabungkan:
 * 1. AI BISINDO Sign Language Recognition via ESP32-CAM (UART 460800 baud)
 * 2. Visual Viewfinder Kamera Live pada Layar LCD TFT ST7735S 1.77" (SPI FSPI)
 * 3. Text Display & Status Interaktif pada Layar OLED 0.96" SSD1306 (I2C)
 * 4. Keyboard Braille 4x4 Tactile Matrix (Braille Grade 1: A-Z, 0-9)
 * 5. Output Suara & TTS via Modul DFPlayer Mini + Mini Speaker 4Ω 3W (Serial2)
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_ST7735.h>
#include <SPI.h>
#include <BISINDO_inferencing.h>
#include <esp_heap_caps.h>
#include "audio_manager.h"
#include "braille_keypad.h"

// ─── Instance Global Audio Manager ──────────────────────────────────────────
AudioManager audio;

// ─── Mode Sistem (Toggle via Tombol S1 pada Keypad) ──────────────────────────
volatile DeviceMode current_device_mode = MODE_AI_BISINDO;

// ─── Layar OLED 0.96" SSD1306 (I2C) ──────────────────────────────────────────
#define I2C_SDA 8
#define I2C_SCL 9

#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT  64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// ─── Layar LCD TFT 1.77" ST7735S (SPI FSPI) ───────────────────────────────────
// Pinout SPI: CS=10, MOSI=11, SCK=12, DC=14, RST=15 (LEDA ke 3.3V)
#define TFT_CS   10
#define TFT_MOSI 11
#define TFT_SCK  12
#define TFT_DC   14
#define TFT_RST  15

#define TFT_PREVIEW_SIZE 128
#define TFT_PREVIEW_X    16
SPIClass tft_spi(FSPI);
Adafruit_ST7735 tft(&tft_spi, TFT_CS, TFT_DC, TFT_RST);
bool tft_siap = false;
uint16_t tft_buffer[TFT_PREVIEW_SIZE * TFT_PREVIEW_SIZE];

// ─── Komunikasi Serial1 UART ke ESP32-CAM ───────────────────────────────────
#define RX_CAM   18
#define TX_CAM   17
#define CAM_BAUD 460800

// ─── Buffer Citra 96x96 Grayscale (9216 bytes) ──────────────────────────────
#define IMG_SIZE          9216
#define HEADER_TIMEOUT_MS 1000
#define FRAME_TIMEOUT_MS  1000
uint8_t img_buffer[IMG_SIZE];

unsigned long paket_sukses_total = 0;
unsigned long last_diag_update   = 0;
const char*   status_uart        = "Handshake...";

// ─── Logika Penguncian Pose AI BISINDO (Hold-to-Type) ────────────────────────
String        kalimat               = "";   // Buffer kalimat terintegrasi (AI + Braille)
String        huruf_terakhir        = "";
String        huruf_terkunci        = "";
unsigned long waktu_deteksi_mulai   = 0;
unsigned long waktu_pose_hilang     = 0;
unsigned long waktu_huruf_terkunci  = 0;
bool          menunggu_lepas_tangan = false;

const unsigned long HOLD_TIME_MS      = 1200; // Tahan pose 1.2 detik untuk mengunci huruf
const unsigned long RELEASE_TIME_MS   =  600; // Lepas tangan sebelum mendeteksi huruf berikutnya
const unsigned long CHECKMARK_TIME_MS = 1000; // Durasi ikon centang setelah huruf tersimpan
const float         CONFIDENCE_THRESHOLD = 0.55f; // Ambang batas keyakinan minimal model (55%)

// ─── PSRAM-aware calloc untuk TensorFlow Lite Micro ──────────────────────────
void *ei_calloc(size_t nitems, size_t size) {
  if (nitems == 0 || size == 0 || nitems > SIZE_MAX / size) return nullptr;
  size_t total = nitems * size;
  if (total >= 65536 && psramFound()) {
    void *mem = heap_caps_calloc(nitems, size, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (mem) return mem;
  }
  return heap_caps_calloc(nitems, size, MALLOC_CAP_DEFAULT);
}

// ─── Callback Piksel Citra → Edge Impulse DSP ────────────────────────────────
static int raw_feature_get_data(size_t offset, size_t length, float *out_ptr) {
  for (size_t i = 0; i < length; i++) {
    uint8_t gray = img_buffer[offset + i];
    uint32_t packed = ((uint32_t)gray << 16) | ((uint32_t)gray << 8) | gray;
    out_ptr[i] = (float)packed;
  }
  return 0;
}

// ─── Handshake & Penerimaan Frame UART dari ESP32-CAM ────────────────────────
bool minta_dan_baca_frame() {
  while (Serial1.available()) Serial1.read(); // Bersihkan buffer sisa
  Serial1.write('C');                         // Kirim trigger capture

  // Cari pasangan byte header [0xAA, 0x55] (60ms cukup pada baudrate 460800)
  unsigned long timeout_header = millis() + 60;
  bool    header_ketemu   = false;
  uint8_t byte_sebelumnya = 0;

  while (millis() < timeout_header) {
    braille_keypad_update(); // Pastikan tombol S1-S16 selalu terbaca responsif
    if (current_device_mode == MODE_BRAILLE) return false;

    while (Serial1.available()) {
      uint8_t b = (uint8_t)Serial1.read();
      if (byte_sebelumnya == 0xAA && b == 0x55) { header_ketemu = true; break; }
      byte_sebelumnya = b;
    }
    if (header_ketemu) break;
  }

  if (!header_ketemu) {
    status_uart = "UART: Kamera Standby";
    return false;
  }

  // Baca 9216 byte piksel grayscale
  size_t terbaca = 0;
  unsigned long timeout_data = millis() + FRAME_TIMEOUT_MS;
  while (terbaca < IMG_SIZE && millis() < timeout_data) {
    braille_keypad_update();
    if (current_device_mode == MODE_BRAILLE) return false;

    int s = Serial1.available();
    if (s > 0) {
      size_t baca = min((size_t)s, (size_t)(IMG_SIZE - terbaca));
      Serial1.readBytes((char*)&img_buffer[terbaca], baca);
      terbaca += baca;
    }
  }

  if (terbaca == IMG_SIZE) {
    paket_sukses_total++;
    status_uart = "UART: Frame OK";
    return true;
  }

  status_uart = "UART: Frame kurang";
  Serial.printf("UART gagal: frame %u/%u byte\n", (unsigned)terbaca, (unsigned)IMG_SIZE);
  return false;
}

// ─── Tampilkan Frame Kamera 96x96 ke TFT LCD ST7735S ─────────────────────────
void tampilkan_preview_tft() {
  if (!tft_siap) return;

  // Skalakan citra 96x96 grayscale menjadi 128x128 RGB565 (nearest-neighbor)
  for (int y = 0; y < TFT_PREVIEW_SIZE; y++) {
    const uint8_t *baris = &img_buffer[(y * 96 / TFT_PREVIEW_SIZE) * 96];
    uint16_t *keluaran = &tft_buffer[y * TFT_PREVIEW_SIZE];
    for (int x = 0; x < TFT_PREVIEW_SIZE; x++) {
      uint8_t g = baris[x * 96 / TFT_PREVIEW_SIZE];
      keluaran[x] = ((g & 0xF8) << 8) | ((g & 0xFC) << 3) | (g >> 3);
    }
  }
  tft.drawRGBBitmap(TFT_PREVIEW_X, 0, tft_buffer, TFT_PREVIEW_SIZE, TFT_PREVIEW_SIZE);
}

// ─── Ikon Status Kunci (Jam / Centang) pada OLED ──────────────────────────────
void gambar_status_kunci(bool terkunci) {
  if (terkunci) {
    // Ikon centang ✓
    display.drawLine(1, 39, 4, 42, WHITE);
    display.drawLine(4, 42, 10, 35, WHITE);
  } else {
    // Ikon jam ◷
    display.drawCircle(6, 39, 5, WHITE);
    display.drawLine(6, 39, 6, 35, WHITE);
    display.drawLine(6, 39, 9, 39, WHITE);
  }
}

// ─── Update Tampilan Layar OLED Mode AI BISINDO ──────────────────────────────
void update_layar_oled(String prediksi, float akurasi, int progress_persen,
                       bool centang_aktif) {
  display.clearDisplay();

  // Baris 1: Header + frame indicator + nilai akurasi
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.print("ISYARA AI ");
  display.print((paket_sukses_total % 2 == 0) ? "[*]" : "[ ]");
  display.setCursor(78, 0);
  if (prediksi != "-" && prediksi != "ERR") {
    display.printf("%2.0f%%", akurasi * 100);
  } else if (prediksi == "ERR") {
    display.print("ERR");
  } else {
    display.print("Idle");
  }

  // Baris 2: Huruf prediksi besar (Font Size 2)
  display.setCursor(0, 16);
  display.setTextSize(1);
  display.print("Pose: ");
  display.setTextSize(2);
  display.print(prediksi);
  display.setTextSize(1);

  // Status Kunci di kanan huruf
  display.setCursor(76, 18);
  if (centang_aktif) {
    display.print("[KUNCI]");
  } else if (prediksi != "-") {
    display.printf("%3d%%", progress_persen);
  }

  // Baris 3: Ikon + Progress Bar penguncian pose
  gambar_status_kunci(centang_aktif);
  display.setCursor(15, 34);
  display.print("[");
  int bar_len = map(progress_persen, 0, 100, 0, 8);
  for (int i = 0; i < 8; i++) {
    display.print(i < bar_len ? "=" : " ");
  }
  display.print("]");

  // Baris 4: Auto-scroll teks kalimat (AI BISINDO + Braille bersatu)
  display.setCursor(0, 52);
  display.print("Teks: ");
  String teks_scroll = (kalimat.length() > 13)
    ? (".." + kalimat.substring(kalimat.length() - 11))
    : kalimat;
  display.print(teks_scroll);

  display.display();
}

// ─── Setup ───────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println("\n==============================================");
  Serial.println("  ISYARA Master ESP32-S3 Firmware Memulai...  ");
  Serial.println("==============================================");
  Serial.printf("PSRAM: %u byte, Bebas: %u byte\n",
                ESP.getPsramSize(), ESP.getFreePsram());

  // 1. Inisialisasi UART Serial1 ke ESP32-CAM
  Serial1.setRxBufferSize(16384);
  Serial1.begin(CAM_BAUD, SERIAL_8N1, RX_CAM, TX_CAM);

  // 2. Inisialisasi Layar OLED 0.96" (I2C: SDA=8, SCL=9)
  Wire.begin(I2C_SDA, I2C_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED SSD1306 Gagal Diinisialisasi!");
  } else {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(WHITE);
    display.setCursor(0, 8);
    display.println("  ISYARA v2.0 Siap");
    display.setCursor(0, 24);
    display.println("Dual Display & Audio");
    display.setCursor(0, 40);
    display.println("Memulai perangkat...");
    display.display();
  }

  // 3. Inisialisasi Layar LCD TFT 1.77" ST7735S (SPI FSPI)
  tft_spi.begin(TFT_SCK, -1, TFT_MOSI, TFT_CS);
  tft.initR(INITR_BLACKTAB);
  tft.setSPISpeed(27000000);
  tft.setRotation(1);
  tft.fillScreen(ST77XX_BLACK);
  tft_siap = true;
  Serial.println("[TFT] ST7735S SPI Siap (CS:10, MOSI:11, SCK:12, DC:14, RST:15)");

  // 4. Inisialisasi Keypad 4x4 Braille (Rows: 4,5,6,7 | Cols: 13,16,21,47)
  braille_keypad_init();

  // 5. Inisialisasi Modul Suara DFPlayer Mini (TX:1, RX:2, BUSY:42)
  audio.begin();

  delay(1000);
}

// ─── Loop Utama ──────────────────────────────────────────────────────────────
void loop() {
  // [1] Selalu scan matriks tombol 4x4 secara non-blocking
  braille_keypad_update();

  // [2] Mode Braille: render visualizer OLED + lewati inferensi kamera
  if (current_device_mode == MODE_BRAILLE) {
    render_braille_oled(display);
    delay(15);
    return;
  }

  // [3] Mode AI BISINDO: minta frame dari kamera ESP32-CAM via UART
  if (minta_dan_baca_frame()) {
    // Tampilkan viewfinder kamera secara real-time ke TFT ST7735S
    tampilkan_preview_tft();

    // Siapkan data fitur untuk Edge Impulse TinyML
    signal_t signal;
    signal.total_length = IMG_SIZE;
    signal.get_data     = &raw_feature_get_data;

    ei_impulse_result_t result = { 0 };
    EI_IMPULSE_ERROR res = run_classifier(&signal, &result, false);

    if (res == EI_IMPULSE_OK) {
      // Cari label prediksi dengan probabilitas tertinggi
      String best_label = "-";
      float  best_value = 0.0f;
      for (size_t ix = 0; ix < EI_CLASSIFIER_LABEL_COUNT; ix++) {
        float val = result.classification[ix].value;
        if (val > best_value) {
          best_value = val;
          best_label = String(result.classification[ix].label);
        }
      }

      // Abaikan kelas latar/idle
      bool is_idle = (best_label.equalsIgnoreCase("idle")       ||
                      best_label.equalsIgnoreCase("background") ||
                      best_label.equalsIgnoreCase("none"));
      if (is_idle) { best_label = "-"; best_value = 0.0f; }

      int progress = 0;
      bool prediksi_valid = (best_value >= CONFIDENCE_THRESHOLD);

      // Logika Pelepasan Tangan (Release Detection)
      if (menunggu_lepas_tangan) {
        bool sinyal_lepas = (!prediksi_valid || best_label != huruf_terkunci);
        if (sinyal_lepas) {
          if (waktu_pose_hilang == 0) {
            waktu_pose_hilang = millis();
          } else if (millis() - waktu_pose_hilang >= RELEASE_TIME_MS) {
            menunggu_lepas_tangan = false;
            huruf_terakhir        = "";
            huruf_terkunci        = "";
            waktu_deteksi_mulai   = 0;
            waktu_pose_hilang     = 0;
          }
        } else {
          waktu_pose_hilang = 0;
        }
      }

      if (menunggu_lepas_tangan) {
        if (!prediksi_valid) best_label = "-";
        progress = (millis() - waktu_huruf_terkunci < CHECKMARK_TIME_MS) ? 100 : 0;
      } else if (prediksi_valid) {
        waktu_pose_hilang = 0;
        if (best_label == huruf_terakhir) {
          unsigned long durasi = millis() - waktu_deteksi_mulai;
          progress = min(100, (int)((durasi * 100) / HOLD_TIME_MS));

          // Kunci huruf ketika durasi penahanan pose mencapai batas (1.2 detik)
          if (durasi >= HOLD_TIME_MS) {
            kalimat               += best_label;
            huruf_terkunci         = best_label;
            menunggu_lepas_tangan  = true;
            waktu_huruf_terkunci   = millis();
            progress               = 100;

            Serial.printf("[AI BISINDO] Huruf Terkunci: %s -> Kalimat: %s\n",
                          best_label.c_str(), kalimat.c_str());

            // Output suara via DFPlayer Mini setiap kali kamera membaca & mengunci huruf
            if (best_label.length() > 0) {
              audio.playChar(best_label.charAt(0));
            }
          }
        } else {
          huruf_terakhir      = best_label;
          waktu_deteksi_mulai = millis();
        }
      } else {
        best_label     = "-";
        huruf_terakhir = "";
        progress       = 0;
      }

      // Update tampilan visual OLED
      bool centang_aktif = (menunggu_lepas_tangan &&
                           (millis() - waktu_huruf_terkunci < CHECKMARK_TIME_MS));
      update_layar_oled(best_label, best_value, progress, centang_aktif);

    } else {
      Serial.printf("AI gagal: run_classifier() mengembalikan kode %d\n", (int)res);
      update_layar_oled("ERR", 0.0f, 0, false);
    }

  } else {
    // Layar diagnostik jika handshake kamera belum tersambung
    if (paket_sukses_total == 0 && millis() - last_diag_update > 250) {
      last_diag_update = millis();
      display.clearDisplay();
      display.setCursor(0, 0);
      display.println("--- STATUS ISYARA ---");
      display.setCursor(0, 18);
      display.println(status_uart);
      display.setCursor(0, 36);
      display.print("Coba ulang otomatis...");
      display.setCursor(0, 52);
      display.print("[S1] -> Braille Mode");
      display.display();
    }
  }
}
