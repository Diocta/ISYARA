#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <BISINDO_inferencing.h>
#include <esp_heap_caps.h>

// Pin I2C untuk Layar OLED 0.96"
#define I2C_SDA 8
#define I2C_SCL 9

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// Pin Serial1 untuk komunikasi dengan ESP32-CAM
#define RX_CAM 18
#define TX_CAM 17
#define CAM_BAUD 460800

// Buffer Gambar 96x96 Grayscale (9216 bytes)
#define IMG_SIZE 9216
#define HEADER_TIMEOUT_MS 1000
#define FRAME_TIMEOUT_MS 1000
uint8_t img_buffer[IMG_SIZE];

unsigned long paket_sukses_total = 0;
unsigned long last_diag_update = 0;
const char* status_uart = "Handshake (Ketuk)...";

// Logika Pembentukan Kata/Kalimat
String kalimat = "";
String huruf_terakhir = "";
String huruf_terkunci = "";
unsigned long waktu_deteksi_mulai = 0;
unsigned long waktu_pose_hilang = 0;
const unsigned long HOLD_TIME_MS = 1200; // Tahan pose 1.2 detik untuk mengunci huruf
const unsigned long RELEASE_TIME_MS = 600; // Lepaskan tangan sebelum huruf berikutnya
const float CONFIDENCE_THRESHOLD = 0.55f; // Ambang batas keyakinan 55%
bool menunggu_lepas_tangan = false;

// Edge Impulse meminta blok besar untuk tensor arena; gunakan PSRAM bila tersedia.
void *ei_calloc(size_t nitems, size_t size) {
  if (nitems == 0 || size == 0 || nitems > SIZE_MAX / size) {
    return nullptr;
  }

  size_t total = nitems * size;
  if (total >= 65536 && psramFound()) {
    void *memory = heap_caps_calloc(nitems, size, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (memory != nullptr) {
      return memory;
    }
  }

  return heap_caps_calloc(nitems, size, MALLOC_CAP_DEFAULT);
}

// Fungsi callback untuk memasukkan piksel gambar ke Edge Impulse
static int raw_feature_get_data(size_t offset, size_t length, float *out_ptr) {
  for (size_t i = 0; i < length; i++) {
    uint8_t gray = img_buffer[offset + i];
    // Edge Impulse membaca nilai warna dalam format RGB uint32_t
    uint32_t packed = ((uint32_t)gray << 16) | ((uint32_t)gray << 8) | (uint32_t)gray;
    out_ptr[i] = (float)packed;
  }
  return 0;
}

// Fungsi Handshake: Minta 1 frame ke ESP32-CAM ('C') dan baca 9216 bytes
bool minta_dan_baca_frame() {
  // 1. Bersihkan sisa data lama di buffer
  while (Serial1.available()) {
    Serial1.read();
  }

  // 2. Ketuk pintu: Kirim perintah 'C' (Capture) ke ESP32-CAM
  Serial1.write('C');

  // 3. Cari header [0xAA, 0x55] dengan timeout yang cukup
  unsigned long timeout_header = millis() + HEADER_TIMEOUT_MS;
  bool header_ketemu = false;
  uint8_t byte_sebelumnya = 0;

  while (millis() < timeout_header) {
    while (Serial1.available()) {
      uint8_t byte_sekarang = (uint8_t)Serial1.read();
      if (byte_sebelumnya == 0xAA && byte_sekarang == 0x55) {
        header_ketemu = true;
        break;
      }
      byte_sebelumnya = byte_sekarang;
    }

    if (header_ketemu) {
      break;
    }
  }

  if (!header_ketemu) {
    status_uart = "UART: Header gagal";
    Serial.println("UART gagal: header tidak diterima");
    return false;
  }

  // 4. Baca 9216 byte piksel secara utuh
  size_t terbaca = 0;
  unsigned long timeout_data = millis() + FRAME_TIMEOUT_MS;
  while (terbaca < IMG_SIZE && millis() < timeout_data) {
    int s = Serial1.available();
    if (s > 0) {
      size_t baca_sekarang = min((size_t)s, (size_t)(IMG_SIZE - terbaca));
      Serial1.readBytes((char*)&img_buffer[terbaca], baca_sekarang);
      terbaca += baca_sekarang;
    }
  }

  if (terbaca == IMG_SIZE) {
    paket_sukses_total++;
    status_uart = "UART: Frame OK";
    return true;
  }

  status_uart = "UART: Frame kurang";
  Serial.printf("UART gagal: frame %u/%u byte\n",
                (unsigned int)terbaca, (unsigned int)IMG_SIZE);
  return false;
}

void gambar_status_kunci(bool terkunci) {
  if (terkunci) {
    display.drawLine(1, 39, 4, 42, WHITE);
    display.drawLine(4, 42, 10, 35, WHITE);
  } else {
    display.drawCircle(6, 39, 5, WHITE);
    display.drawLine(6, 39, 6, 35, WHITE);
    display.drawLine(6, 39, 9, 39, WHITE);
  }
}

void update_layar_oled(String prediksi, float akurasi, int progress_persen,
                       bool terkunci) {
  display.clearDisplay();
  
  // Header + Indikator Frame Aktif (Berkedip)
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.print("--- ISYARA AI --- ");
  display.print((paket_sukses_total % 2 == 0) ? "*" : " ");

  // Hasil Tebakan Huruf & Akurasi
  display.setCursor(0, 14);
  display.print("Huruf : ");
  display.setTextSize(2);
  display.print(prediksi);
  display.setTextSize(1);
  
  if (prediksi != "-") {
    display.printf(" (%.0f%%)\n", akurasi * 100);
  } else {
    display.println(" (Idle)");
  }

  // Ikon jam menunjukkan pose sedang ditahan, centang menunjukkan huruf tersimpan.
  gambar_status_kunci(terkunci);
  display.setCursor(15, 34);
  display.print("[");
  int bar_len = map(progress_persen, 0, 100, 0, 8);
  for (int i = 0; i < 8; i++) {
    if (i < bar_len) display.print("=");
    else display.print(" ");
  }
  display.print("]");

  // Rangkaian Kalimat
  display.setCursor(0, 48);
  display.print("Teks: ");
  display.print(kalimat);

  display.display();
}

void setup() {
  Serial.begin(115200);
  Serial.printf("PSRAM: %u byte, bebas: %u byte\n",
                ESP.getPsramSize(), ESP.getFreePsram());

  // Penampungan Serial1 diperbesar untuk keamanan buffer
  Serial1.setRxBufferSize(16384);
  Serial1.begin(CAM_BAUD, SERIAL_8N1, RX_CAM, TX_CAM);

  Wire.begin(I2C_SDA, I2C_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED Gagal!");
    while (1);
  }

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 20);
  display.println("Sistem ISYARA Siap");
  display.display();
}

void loop() {
  // 1. Minta 1 frame ke kamera via Handshake
  if (minta_dan_baca_frame()) {
    
    // 2. Siapkan data untuk inferensi Edge Impulse
    signal_t signal;
    signal.total_length = IMG_SIZE;
    signal.get_data = &raw_feature_get_data;

    ei_impulse_result_t result = { 0 };
    EI_IMPULSE_ERROR res = run_classifier(&signal, &result, false);

    if (res == EI_IMPULSE_OK) {
      // 3. Cari huruf dengan probabilitas tertinggi
      String best_label = "-";
      float best_value = 0.0f;

      for (size_t ix = 0; ix < EI_CLASSIFIER_LABEL_COUNT; ix++) {
        if (result.classification[ix].value > best_value) {
          best_value = result.classification[ix].value;
          best_label = String(result.classification[ix].label);
        }
      }

      // 4. Logika Ambang Batas, tahan pose, dan lepas tangan sebelum input berikutnya
      int progress = 0;
      if (best_value >= CONFIDENCE_THRESHOLD) {
        waktu_pose_hilang = 0;

        if (menunggu_lepas_tangan) {
          best_label = huruf_terkunci;
          progress = 100;
        } else if (best_label == huruf_terakhir) {
          unsigned long durasi = millis() - waktu_deteksi_mulai;
          progress = min(100, (int)((durasi * 100) / HOLD_TIME_MS));

          if (durasi >= HOLD_TIME_MS) {
            kalimat += best_label;
            huruf_terkunci = best_label;
            menunggu_lepas_tangan = true;
            progress = 100;
          }
        } else {
          huruf_terakhir = best_label;
          waktu_deteksi_mulai = millis();
        }
      } else {
        best_label = "-";

        if (menunggu_lepas_tangan) {
          if (waktu_pose_hilang == 0) {
            waktu_pose_hilang = millis();
          } else if (millis() - waktu_pose_hilang >= RELEASE_TIME_MS) {
            menunggu_lepas_tangan = false;
            huruf_terakhir = "";
            huruf_terkunci = "";
            waktu_deteksi_mulai = 0;
            waktu_pose_hilang = 0;
          }

          if (menunggu_lepas_tangan) {
            best_label = huruf_terkunci;
            progress = 100;
          }
        } else {
          huruf_terakhir = "";
          progress = 0;
        }
      }

      // 5. Perbarui tampilan di Layar OLED
      update_layar_oled(best_label, best_value, progress, menunggu_lepas_tangan);
    } else {
      Serial.printf("AI gagal: run_classifier() mengembalikan %d\n", (int)res);
      update_layar_oled("ERR", 0.0f, 0, false);
    }
  } else {
    // Jika belum berhasil handshake, tampilkan layar status percobaan
    if (paket_sukses_total == 0 && millis() - last_diag_update > 250) {
      last_diag_update = millis();
      display.clearDisplay();
      display.setCursor(0, 0);
      display.println("--- STATUS ISYARA ---");
      display.setCursor(0, 18);
      display.println(status_uart);
      display.setCursor(0, 36);
      display.print("Coba ulang otomatis...");
      display.display();
    }
  }
}
