#ifndef BRAILLE_KEYPAD_H
#define BRAILLE_KEYPAD_H

#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "audio_manager.h"

// =============================================================================
// ISYARA - Universal 8-Pin All-Pairs Keypad Scanner (ESP32-S3 Core 0 FreeRTOS)
// Mampu mendeteksi penekanan tombol APAPUN terlepas dari orientasi modul PCB
// (Bisa untuk Row/Col lurus, terbalik, tertukar, maupun interleaved)
// =============================================================================

// 8 Pin Jumper ESP32-S3 yang terhubung ke Pin 1 s.d 8 modul 4x4 (dari atas ke bawah)
// Pin 1 = GPIO 4
// Pin 2 = GPIO 5
// Pin 3 = GPIO 6
// Pin 4 = GPIO 7
// Pin 5 = GPIO 13
// Pin 6 = GPIO 16
// Pin 7 = GPIO 21
// Pin 8 = GPIO 47
const uint8_t KEYPAD_PINS[8] = {4, 5, 6, 7, 13, 16, 21, 47};

// State Debounce untuk semua pasangan pin (8 x 8)
static bool pair_prev_state[8][8] = {false};
static unsigned long last_key_press_time = 0;
const unsigned long DEBOUNCE_MS = 30;

// Variabel Diagnostik untuk Layar OLED & Serial Monitor
extern volatile int last_detected_pin_a;
extern volatile int last_detected_pin_b;
extern volatile char last_detected_label[16];
extern volatile unsigned long last_detected_time;

// Buffer Titik Braille (6-dot cell)
// Bit 0: Titik 1 | Bit 3: Titik 4
// Bit 1: Titik 2 | Bit 4: Titik 5
// Bit 2: Titik 3 | Bit 5: Titik 6
static volatile uint8_t braille_dots = 0;
static volatile bool number_mode = false;
static volatile unsigned long last_dot_time = 0;
const unsigned long AUTO_COMMIT_MS = 850;

// Mode Sistem
enum DeviceMode {
  MODE_AI_BISINDO = 0,
  MODE_BRAILLE = 1
};
extern volatile DeviceMode current_device_mode;
extern String kalimat;

// Fungsi Dekoder Braille (Mask 6-bit -> Karakter ASCII)
char decode_braille_to_char(uint8_t mask, bool is_num) {
  if (mask == 0) return '\0';

  char ch = '\0';
  switch (mask) {
    case 0b000001: ch = 'A'; break; // Titik 1
    case 0b000011: ch = 'B'; break; // Titik 1, 2
    case 0b001001: ch = 'C'; break; // Titik 1, 4
    case 0b011001: ch = 'D'; break; // Titik 1, 4, 5
    case 0b010001: ch = 'E'; break; // Titik 1, 5
    case 0b001011: ch = 'F'; break; // Titik 1, 2, 4
    case 0b011011: ch = 'G'; break; // Titik 1, 2, 4, 5
    case 0b010011: ch = 'H'; break; // Titik 1, 2, 5
    case 0b001010: ch = 'I'; break; // Titik 2, 4
    case 0b011010: ch = 'J'; break; // Titik 2, 4, 5
    case 0b000101: ch = 'K'; break; // Titik 1, 3
    case 0b000111: ch = 'L'; break; // Titik 1, 2, 3
    case 0b001101: ch = 'M'; break; // Titik 1, 3, 4
    case 0b011101: ch = 'N'; break; // Titik 1, 3, 4, 5
    case 0b010101: ch = 'O'; break; // Titik 1, 3, 5
    case 0b001111: ch = 'P'; break; // Titik 1, 2, 3, 4
    case 0b011111: ch = 'Q'; break; // Titik 1, 2, 3, 4, 5
    case 0b010111: ch = 'R'; break; // Titik 1, 2, 3, 5
    case 0b001110: ch = 'S'; break; // Titik 2, 3, 4
    case 0b011110: ch = 'T'; break; // Titik 2, 3, 4, 5
    case 0b100101: ch = 'U'; break; // Titik 1, 3, 6
    case 0b100111: ch = 'V'; break; // Titik 1, 2, 3, 6
    case 0b111010: ch = 'W'; break; // Titik 2, 4, 5, 6
    case 0b101101: ch = 'X'; break; // Titik 1, 3, 4, 6
    case 0b111101: ch = 'Y'; break; // Titik 1, 3, 4, 5, 6
    case 0b110101: ch = 'Z'; break; // Titik 1, 3, 5, 6
    
    // Tanda Baca
    case 0b000010: ch = ','; break;
    case 0b110010: ch = '.'; break;
    case 0b100110: ch = '?'; break;
    case 0b010110: ch = '!'; break;
    case 0b100100: ch = '-'; break;
    default: ch = '?'; break;
  }

  if (is_num && ch >= 'A' && ch <= 'J') {
    if (ch == 'J') return '0';
    return (char)('1' + (ch - 'A'));
  }

  return ch;
}

// Commit karakter Braille ke baris teks
void commit_braille_char() {
  if (braille_dots != 0) {
    char c = decode_braille_to_char(braille_dots, number_mode);
    if (c != '\0' && c != '?') {
      kalimat += c;
      Serial.printf("[BRAILLE] Huruf Dikunci: '%c' (Mask: 0x%02X) -> Kalimat: %s\n", c, braille_dots, kalimat.c_str());
      audio.playChar(c);
    } else {
      Serial.printf("[BRAILLE] Pola Titik Tidak Dikenal (Mask: 0x%02X)\n", braille_dots);
    }
    braille_dots = 0;
  }
}

// Aksi Logika Fungsional Tombol
void toggle_system_mode() {
  if (current_device_mode == MODE_AI_BISINDO) {
    current_device_mode = MODE_BRAILLE;
    Serial.println("-> [MODE SWITCH]: BRAILLE KEYBOARD AKTIF");
    audio.playModeChange(true);
  } else {
    current_device_mode = MODE_AI_BISINDO;
    Serial.println("-> [MODE SWITCH]: AI BISINDO AKTIF");
    audio.playModeChange(false);
  }
}

void toggle_dot(uint8_t dot_index) { // 0: Dot 1, 1: Dot 2, 2: Dot 3, 3: Dot 4, 4: Dot 5, 5: Dot 6
  braille_dots ^= (1 << dot_index);
  last_dot_time = millis();
  Serial.printf("-> Titik %d Di-toggle! (Mask: 0x%02X)\n", dot_index + 1, braille_dots);
}

// Handler Pemetaan Pasangan Pin (pin_a dan pin_b dalam indeks 0..7)
void handle_pin_pair_press(int a, int b) {
  if (a > b) { int tmp = a; a = b; b = tmp; } // Selalu a < b
  int pA = a + 1; // Pin Header 1 s.d 8
  int pB = b + 1;

  last_detected_pin_a = pA;
  last_detected_pin_b = pB;
  last_detected_time  = millis();

  Serial.printf("\n[KEYPAD-HIT] >>> Pin %d (GPIO %d) & Pin %d (GPIO %d) Terhubung! <<<\n",
                pA, KEYPAD_PINS[a], pB, KEYPAD_PINS[b]);

  // =========================================================================
  // PEMETAAN JALUR PCB MODUL (Berdasarkan Hasil Tes Fisik Aktual Pengguna)
  // =========================================================================
  // Dari hasil tes fisik:
  // - S4 (Pojok Kanan Atas) menghubungkan Pin 1 & Pin 5
  // - S5 (Kiri Baris 2) menghubungkan Pin 1 & Pin 6
  // - S7 (Tengah Baris 2) menghubungkan Pin 2 & Pin 6
  // - S8 (Kanan Baris 2) menghubungkan Pin 3 & Pin 6
  // =========================================================================

  // Mode Switch (S1 atau S4):
  if ((pA == 1 && pB == 5) || (pA == 1 && pB == 8) || (pA == 4 && pB == 5)) {
    snprintf((char*)last_detected_label, 16, "MODE SWITCH");
    toggle_system_mode();
    return;
  }

  // --- TITIK-TITIK BRAILLE ---
  // Titik 1 (Kiri Atas): S2 fisik
  if ((pA == 1 && pB == 6) || (pA == 2 && pB == 5)) {
    snprintf((char*)last_detected_label, 16, "DOT 1");
    toggle_dot(0);
    return;
  }

  // Titik 2 (Kiri Tengah): S6 fisik
  if ((pA == 2 && pB == 6) || (pA == 2 && pB == 7)) {
    snprintf((char*)last_detected_label, 16, "DOT 2");
    toggle_dot(1);
    return;
  }

  // Titik 3 (Kiri Bawah): S10 fisik
  if ((pA == 3 && pB == 6) || (pA == 3 && pB == 7)) {
    snprintf((char*)last_detected_label, 16, "DOT 3");
    toggle_dot(2);
    return;
  }

  // Titik 4 (Kanan Atas): S3 fisik
  if ((pA == 1 && pB == 7) || (pA == 3 && pB == 5)) {
    snprintf((char*)last_detected_label, 16, "DOT 4");
    toggle_dot(3);
    return;
  }

  // Titik 5 (Kanan Tengah): S7 fisik
  if ((pA == 2 && pB == 7) || (pA == 2 && pB == 8)) {
    snprintf((char*)last_detected_label, 16, "DOT 5");
    toggle_dot(4);
    return;
  }

  // Titik 6 (Kanan Bawah): S11 fisik
  if ((pA == 3 && pB == 7) || (pA == 3 && pB == 8)) {
    snprintf((char*)last_detected_label, 16, "DOT 6");
    toggle_dot(5);
    return;
  }

  // Spasi: S9 atau S14
  if ((pA == 4 && pB == 6) || (pA == 4 && pB == 7)) {
    snprintf((char*)last_detected_label, 16, "SPASI");
    commit_braille_char();
    kalimat += " ";
    audio.playChar(' ');
    Serial.printf("-> Tambah Spasi -> Kalimat: '%s'\n", kalimat.c_str());
    return;
  }

  // Backspace: S5 atau S13
  if ((pA == 4 && pB == 5) || (pA == 4 && pB == 8)) {
    snprintf((char*)last_detected_label, 16, "BACKSPACE");
    if (braille_dots != 0) {
      braille_dots = 0;
      Serial.println("-> Batalkan Titik Aktif");
    } else if (kalimat.length() > 0) {
      kalimat.remove(kalimat.length() - 1);
      audio.playBackspace();
      Serial.printf("-> Backspace -> Kalimat: '%s'\n", kalimat.c_str());
    }
    return;
  }

  // Hapus Semua (Clear All)
  if (pA == 1 && pB == 8) {
    snprintf((char*)last_detected_label, 16, "CLEAR ALL");
    kalimat = "";
    braille_dots = 0;
    audio.playClear();
    Serial.println("-> Hapus Seluruh Kalimat");
    return;
  }

  // Enter / Commit Manual: S8 atau S15
  if ((pA == 3 && pB == 6) || (pA == 4 && pB == 7)) {
    snprintf((char*)last_detected_label, 16, "ENTER");
    commit_braille_char();
    Serial.println("-> Enter / Commit");
    return;
  }

  // Tombol belum terpetakan khusus: Catat labelnya
  snprintf((char*)last_detected_label, 16, "P%d-P%d", pA, pB);
  Serial.printf("-> Tombol Baru Terdeteksi (Pair P%d & P%d)\n", pA, pB);
}

// Fungsi Scanner Matriks All-Pairs (Memeriksa seluruh kemungkinan pasangan pin)
void braille_keypad_update() {
  unsigned long now = millis();

  // Scan Simetris: Drive satu pin LOW, baca pin lainnya yang diberi INPUT_PULLUP
  for (int i = 0; i < 8; i++) {
    // Siapkan pin i sebagai OUTPUT LOW
    pinMode(KEYPAD_PINS[i], OUTPUT);
    digitalWrite(KEYPAD_PINS[i], LOW);
    delayMicroseconds(35); // Settling time

    for (int j = i + 1; j < 8; j++) {
      bool is_pressed = (digitalRead(KEYPAD_PINS[j]) == LOW);

      if (is_pressed && !pair_prev_state[i][j] && (now - last_key_press_time > DEBOUNCE_MS)) {
        last_key_press_time = now;
        pair_prev_state[i][j] = true;
        handle_pin_pair_press(i, j);
      } else if (!is_pressed && pair_prev_state[i][j]) {
        pair_prev_state[i][j] = false;
      }
    }

    // Kembalikan pin i ke INPUT_PULLUP
    pinMode(KEYPAD_PINS[i], INPUT_PULLUP);
  }

  // Auto-commit huruf braille setelah tidak ada tombol ditekan selama AUTO_COMMIT_MS
  if (braille_dots != 0 && (now - last_dot_time > AUTO_COMMIT_MS)) {
    commit_braille_char();
  }
}

// Background Task FreeRTOS pada Core 0 (Scan 100x per detik)
static void keypad_freertos_task(void *pvParameters) {
  while (true) {
    braille_keypad_update();
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

// Inisialisasi 8 Pin Keypad
void braille_keypad_init() {
  for (int i = 0; i < 8; i++) {
    pinMode(KEYPAD_PINS[i], INPUT_PULLUP);
  }

  xTaskCreatePinnedToCore(
    keypad_freertos_task,
    "KeypadScanner",
    3072,
    NULL,
    2,
    NULL,
    0 // Core 0
  );

  Serial.println("[BRAILLE] Universal All-Pairs Keypad Scanner Aktif di Core 0!");
}

// Tampilan Visual Braille Khusus Layar OLED
void render_braille_oled(Adafruit_SSD1306 &display) {
  display.clearDisplay();

  // 1. Header & Status Mode
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.print("BRAILLE MODE ");
  if (number_mode) display.print("[NUM]");
  else display.print("[A-Z]");

  // Tampilkan notifikasi tombol fisik jika baru ditekan (< 1.5 detik)
  if (millis() - last_detected_time < 1500 && last_detected_pin_a > 0) {
    display.setCursor(76, 0);
    display.printf("[%s]", (char*)last_detected_label);
  }

  // 2. Visualisasi 6 Titik Braille (2x3 Grid) di Sisi Kiri Layar
  int dot_coords[6][2] = {
    {10, 14}, // Titik 1
    {10, 25}, // Titik 2
    {10, 36}, // Titik 3
    {26, 14}, // Titik 4
    {26, 25}, // Titik 5
    {26, 36}  // Titik 6
  };

  for (int i = 0; i < 6; i++) {
    int cx = dot_coords[i][0];
    int cy = dot_coords[i][1];
    if (braille_dots & (1 << i)) {
      display.fillCircle(cx, cy, 4, WHITE); // Titik Aktif (Bulatan Padat)
    } else {
      display.drawCircle(cx, cy, 4, WHITE); // Titik Kosong (Lingkaran Berongga)
    }
  }

  // 3. Karakter Preview Real-Time (Ukuran Besar di Sisi Kanan)
  char preview_ch = decode_braille_to_char(braille_dots, number_mode);
  display.setCursor(48, 14);
  display.setTextSize(1);
  display.print("Char: ");
  display.setTextSize(3);
  display.setCursor(84, 14);
  if (braille_dots != 0) {
    if (preview_ch != '\0' && preview_ch != '?') {
      display.print(preview_ch);
    } else {
      display.print("?");
    }
  } else {
    display.setTextSize(1);
    display.setCursor(84, 22);
    display.print("[-]");
  }

  // 4. Baris Kalimat Teks Hasil Ketikan (Auto-scroll jika panjang)
  display.setTextSize(1);
  display.setCursor(0, 52);
  display.print("Teks: ");
  String teks_scroll = (kalimat.length() > 14) ? (".." + kalimat.substring(kalimat.length() - 12)) : kalimat;
  display.print(teks_scroll);

  display.display();
}

#endif // BRAILLE_KEYPAD_H
