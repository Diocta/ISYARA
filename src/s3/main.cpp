/*
 * ISYARA - ESP32-S3 Master Firmware
 * Menggabungkan: AI BISINDO Sign Language Recognition + Braille Keyboard 4x4 Matrix
 *
 * Mode AI BISINDO : Inferensi TFLite via kamera ESP32-CAM (UART 460800 baud)
 *                   Hold-to-type 1.2s + menunggu_lepas_tangan 600ms anti-repeat
 * Mode Braille    : Keypad taktil 4x4 S1-S16, Braille Grade 1 (A-Z, 0-9)
 *                   Toggle via tombol S1
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <BISINDO_inferencing.h>
#include <esp_heap_caps.h>
#include "braille_keypad.h"

// Mode Sistem (toggle via tombol S1 pada keypad)
DeviceMode current_device_mode = MODE_AI_BISINDO;

// ─── Pin I2C Layar OLED 0.96" ───────────────────────────────────────────────
#define I2C_SDA 8
#define I2C_SCL 9

#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT  64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// ─── Pin Serial1 UART ke ESP32-CAM ──────────────────────────────────────────
#define RX_CAM   18
#define TX_CAM   17
#define CAM_BAUD 460800

// ─── Buffer Gambar 96x96 Grayscale (9216 bytes) ──────────────────────────────
#define IMG_SIZE          9216
#define HEADER_TIMEOUT_MS 1000
#define FRAME_TIMEOUT_MS  1000
uint8_t img_buffer[IMG_SIZE];

unsigned long paket_sukses_total = 0;
unsigned long last_diag_update   = 0;
const char*   status_uart        = "Handshake...";

// ─── Logika Hold-to-Type AI BISINDO ──────────────────────────────────────────
String        kalimat             = "";   // buffer teks bersama (AI + Braille)
String        huruf_terakhir      = "";
String        huruf_terkunci      = "";
unsigned long waktu_deteksi_mulai = 0;
unsigned long waktu_pose_hilang   = 0;
bool          menunggu_lepas_tangan = false;

const unsigned long HOLD_TIME_MS    = 1200; // ms tahan pose untuk kunci huruf
const unsigned long RELEASE_TIME_MS =  600; // ms hilang pose sebelum input berikutnya
const float         CONFIDENCE_THRESHOLD = 0.55f; // threshold minimal AI

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

// ─── Callback piksel gambar → Edge Impulse ───────────────────────────────────
static int raw_feature_get_data(size_t offset, size_t length, float *out_ptr) {
  for (size_t i = 0; i < length; i++) {
    uint8_t gray = img_buffer[offset + i];
    uint32_t packed = ((uint32_t)gray << 16) | ((uint32_t)gray << 8) | gray;
    out_ptr[i] = (float)packed;
  }
  return 0;
}

// ─── Handshake Frame dari ESP32-CAM ──────────────────────────────────────────
bool minta_dan_baca_frame() {
  while (Serial1.available()) Serial1.read(); // flush stale bytes
  Serial1.write('C');

  // Cari header 0xAA 0x55
  unsigned long timeout_header = millis() + HEADER_TIMEOUT_MS;
  bool   header_ketemu   = false;
  uint8_t byte_sebelumnya = 0;

  while (millis() < timeout_header) {
    while (Serial1.available()) {
      uint8_t b = (uint8_t)Serial1.read();
      if (byte_sebelumnya == 0xAA && b == 0x55) { header_ketemu = true; break; }
      byte_sebelumnya = b;
    }
    if (header_ketemu) break;
  }

  if (!header_ketemu) {
    status_uart = "UART: Header gagal";
    Serial.println("UART gagal: header tidak diterima");
    return false;
  }

  // Baca 9216 byte piksel
  size_t terbaca = 0;
  unsigned long timeout_data = millis() + FRAME_TIMEOUT_MS;
  while (terbaca < IMG_SIZE && millis() < timeout_data) {
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

// ─── Ikon status kunci / menunggu di OLED ────────────────────────────────────
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

// ─── Update tampilan OLED mode AI BISINDO ────────────────────────────────────
void update_layar_oled(String prediksi, float akurasi, int progress_persen,
                       bool terkunci) {
  display.clearDisplay();

  // Baris 1: Header + Blinking frame indicator + akurasi
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

  // Baris 2: Huruf prediksi besar
  display.setCursor(0, 16);
  display.setTextSize(1);
  display.print("Pose: ");
  display.setTextSize(2);
  display.print(prediksi);
  display.setTextSize(1);

  // Status kunci (kanan huruf)
  display.setCursor(76, 18);
  if (terkunci) {
    display.print("[KUNCI]");
  } else if (prediksi != "-") {
    display.printf("%3d%%", progress_persen);
  }

  // Baris 3: Ikon + progress bar tahan pose
  gambar_status_kunci(terkunci);
  display.setCursor(15, 34);
  display.print("[");
  int bar_len = map(progress_persen, 0, 100, 0, 8);
  for (int i = 0; i < 8; i++) {
    display.print(i < bar_len ? "=" : " ");
  }
  display.print("]");

  // Baris 4: Auto-scroll kalimat (AI + Braille bersatu)
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
  Serial.printf("PSRAM: %u byte, bebas: %u byte\n",
                ESP.getPsramSize(), ESP.getFreePsram());

  Serial1.setRxBufferSize(16384);
  Serial1.begin(CAM_BAUD, SERIAL_8N1, RX_CAM, TX_CAM);

  Wire.begin(I2C_SDA, I2C_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED Gagal!");
    while (1);
  }

  // Inisialisasi Keypad 4x4 Braille
  braille_keypad_init();

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 8);
  display.println("  ISYARA v2.0 Siap");
  display.setCursor(0, 24);
  display.println("Mode: AI BISINDO");
  display.setCursor(0, 40);
  display.println("[S1] -> Braille Mode");
  display.display();
  delay(1200);
}

// ─── Loop ────────────────────────────────────────────────────────────────────
void loop() {
  // [1] Selalu baca keypad matriks 4x4 (non-blocking)
  braille_keypad_update();

  // [2] Mode Braille aktif: render OLED braille + skip inferensi kamera
  if (current_device_mode == MODE_BRAILLE) {
    render_braille_oled(display);
    delay(15);
    return;
  }

  // [3] Mode AI BISINDO: minta frame dari kamera
  if (minta_dan_baca_frame()) {
    signal_t signal;
    signal.total_length = IMG_SIZE;
    signal.get_data     = &raw_feature_get_data;

    ei_impulse_result_t result = { 0 };
    EI_IMPULSE_ERROR res = run_classifier(&signal, &result, false);

    if (res == EI_IMPULSE_OK) {
      // Cari prediksi terbaik
      String best_label = "-";
      float  best_value = 0.0f;
      for (size_t ix = 0; ix < EI_CLASSIFIER_LABEL_COUNT; ix++) {
        float val = result.classification[ix].value;
        if (val > best_value) {
          best_value = val;
          best_label = String(result.classification[ix].label);
        }
      }

      // Abaikan kelas idle/background
      bool is_idle = (best_label.equalsIgnoreCase("idle")       ||
                      best_label.equalsIgnoreCase("background") ||
                      best_label.equalsIgnoreCase("none"));
      if (is_idle) { best_label = "-"; best_value = 0.0f; }

      // Logika hold-to-type + menunggu_lepas_tangan anti-repeat
      int progress = 0;
      if (best_value >= CONFIDENCE_THRESHOLD) {
        waktu_pose_hilang = 0;

        if (menunggu_lepas_tangan) {
          // Tampilkan huruf terkunci dengan ikon centang sampai tangan dilepas
          best_label = huruf_terkunci;
          progress   = 100;
        } else if (best_label == huruf_terakhir) {
          unsigned long durasi = millis() - waktu_deteksi_mulai;
          progress = min(100, (int)((durasi * 100) / HOLD_TIME_MS));
          if (durasi >= HOLD_TIME_MS) {
            kalimat            += best_label;
            huruf_terkunci      = best_label;
            menunggu_lepas_tangan = true;
            progress            = 100;
          }
        } else {
          huruf_terakhir      = best_label;
          waktu_deteksi_mulai = millis();
        }
      } else {
        best_label = "-";
        if (menunggu_lepas_tangan) {
          if (waktu_pose_hilang == 0) waktu_pose_hilang = millis();
          else if (millis() - waktu_pose_hilang >= RELEASE_TIME_MS) {
            menunggu_lepas_tangan = false;
            huruf_terakhir        = "";
            huruf_terkunci        = "";
            waktu_deteksi_mulai   = 0;
            waktu_pose_hilang     = 0;
          }
          if (menunggu_lepas_tangan) { best_label = huruf_terkunci; progress = 100; }
        } else {
          huruf_terakhir = "";
          progress       = 0;
        }
      }

      update_layar_oled(best_label, best_value, progress, menunggu_lepas_tangan);

    } else {
      Serial.printf("AI gagal: run_classifier() mengembalikan %d\n", (int)res);
      update_layar_oled("ERR", 0.0f, 0, false);
    }

  } else {
    // Belum berhasil handshake
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
