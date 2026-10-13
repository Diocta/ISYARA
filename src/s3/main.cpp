#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <BISINDO_inferencing.h>

// Pin I2C untuk Layar OLED 0.96"
#define I2C_SDA 8
#define I2C_SCL 9

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// Pin Serial1 untuk komunikasi dengan ESP32-CAM (Kecepatan Stabil)
#define RX_CAM 18
#define TX_CAM 17
#define CAM_BAUD 230400

// Buffer Gambar 96x96 Grayscale (9216 bytes)
#define IMG_SIZE 9216
uint8_t img_buffer[IMG_SIZE];

unsigned long paket_sukses_total = 0;
unsigned long last_diag_update = 0;

// Logika Pembentukan Kata/Kalimat
String kalimat = "";
String huruf_terakhir = "";
unsigned long waktu_deteksi_mulai = 0;
const unsigned long HOLD_TIME_MS = 1200; // Tahan pose 1.2 detik untuk mengunci huruf
const float CONFIDENCE_THRESHOLD = 0.55f; // Ambang batas keyakinan 55%

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

  // 3. Tunggu header [0xAA, 0x55] dengan timeout 350ms
  unsigned long timeout_header = millis() + 350;
  bool header_ketemu = false;

  while (millis() < timeout_header) {
    if (Serial1.available() >= 2) {
      if (Serial1.read() == 0xAA) {
        if (Serial1.read() == 0x55) {
          header_ketemu = true;
          break;
        }
      }
    }
  }

  if (!header_ketemu) return false;

  // 4. Baca 9216 byte piksel secara utuh
  size_t terbaca = 0;
  unsigned long timeout_data = millis() + 450;
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
    return true;
  }

  return false;
}

void update_layar_oled(String prediksi, float akurasi, int progress_persen) {
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

  // Bar Progress Menahan Pose
  display.setCursor(0, 34);
  display.print("Kunci : [");
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

      // 4. Logika Ambang Batas (Confidence Threshold) & Penguncian Huruf
      int progress = 0;
      if (best_value >= CONFIDENCE_THRESHOLD) {
        if (best_label == huruf_terakhir) {
          unsigned long durasi = millis() - waktu_deteksi_mulai;
          progress = min(100, (int)((durasi * 100) / HOLD_TIME_MS));

          // Jika pose ditahan selama 1.2 detik, kunci ke dalam kalimat!
          if (durasi >= HOLD_TIME_MS) {
            kalimat += best_label;
            waktu_deteksi_mulai = millis(); // Reset
            progress = 0;
          }
        } else {
          huruf_terakhir = best_label;
          waktu_deteksi_mulai = millis();
        }
      } else {
        // Jika tidak ada pose atau akurasi di bawah 55%, anggap Idle
        best_label = "-";
        huruf_terakhir = "";
        progress = 0;
      }

      // 5. Perbarui tampilan di Layar OLED
      update_layar_oled(best_label, best_value, progress);
    }
  } else {
    // Jika belum berhasil handshake, tampilkan layar status percobaan
    if (paket_sukses_total == 0 && millis() - last_diag_update > 250) {
      last_diag_update = millis();
      display.clearDisplay();
      display.setCursor(0, 0);
      display.println("--- STATUS ISYARA ---");
      display.setCursor(0, 18);
      display.println("Menghubungkan Kamera");
      display.setCursor(0, 36);
      display.print("Handshake (Ketuk)...");
      display.display();
    }
  }
}
