#ifndef BRAILLE_KEYPAD_H
#define BRAILLE_KEYPAD_H

#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "audio_manager.h"

// =============================================================================
// ISYARA - Modul Keyboard Braille 4x4 Tactile Matrix (ESP32-S3)
// Menggunakan FreeRTOS Task pada Core 0 (Independent Scanner)
// =============================================================================

// Pinout Rows (Header Kiri: Pin 4, 5, 6, 7 berurutan)
#define KEYPAD_R1 4
#define KEYPAD_R2 5
#define KEYPAD_R3 6
#define KEYPAD_R4 7

// Pinout Cols (Bebas tabrakan dari TFT & strapping pins)
#define KEYPAD_C1 13
#define KEYPAD_C2 16
#define KEYPAD_C3 21
#define KEYPAD_C4 47

const uint8_t ROW_PINS[4] = {KEYPAD_R1, KEYPAD_R2, KEYPAD_R3, KEYPAD_R4};
const uint8_t COL_PINS[4] = {KEYPAD_C1, KEYPAD_C2, KEYPAD_C3, KEYPAD_C4};

// Indeks ID Tombol S1 - S16 (1..16)
// S1  = (R0, C0) | S2  = (R0, C1) | S3  = (R0, C2) | S4  = (R0, C3)
// S5  = (R1, C0) | S6  = (R1, C1) | S7  = (R1, C2) | S8  = (R1, C3)
// S9  = (R2, C0) | S10 = (R2, C1) | S11 = (R2, C2) | S12 = (R2, C3)
// S13 = (R3, C0) | S14 = (R3, C1) | S15 = (R3, C2) | S16 = (R3, C3)

// State Tombol Matriks (Debounce)
static bool key_state[4][4] = {false};
static bool key_prev_state[4][4] = {false};
static unsigned long last_key_press_time = 0;
const unsigned long DEBOUNCE_MS = 25;

// Buffer Titik Braille (6-dot cell)
// Bit 0: Titik 1 (S2)  | Bit 3: Titik 4 (S3)
// Bit 1: Titik 2 (S6)  | Bit 4: Titik 5 (S7)
// Bit 2: Titik 3 (S10) | Bit 5: Titik 6 (S11)
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
    case 0b000010: ch = ','; break; // Titik 2
    case 0b110010: ch = '.'; break; // Titik 2, 5, 6
    case 0b100110: ch = '?'; break; // Titik 2, 3, 6
    case 0b010110: ch = '!'; break; // Titik 2, 3, 5
    case 0b100100: ch = '-'; break; // Titik 3, 6
    default: ch = '?'; break;
  }

  // Jika sedang dalam Mode Angka (1..9, 0)
  if (is_num && ch >= 'A' && ch <= 'J') {
    if (ch == 'J') return '0';
    return (char)('1' + (ch - 'A'));
  }

  return ch;
}

// Fungsi Commit Karakter Braille ke Kalimat
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

// Handler Aksi Setiap Tombol S1 - S16
void handle_key_action(int key_num) {
  Serial.printf("[KEYPAD] Tombol S%d Ditekan! ", key_num);

  switch (key_num) {
    // Tombol S1: Ganti Mode Sistem (BISINDO AI <-> BRAILLE KEYBOARD)
    case 1:
      if (current_device_mode == MODE_AI_BISINDO) {
        current_device_mode = MODE_BRAILLE;
        Serial.println("-> MODE SWITCH: BRAILLE KEYBOARD AKTIF");
        audio.playModeChange(true);
      } else {
        current_device_mode = MODE_AI_BISINDO;
        Serial.println("-> MODE SWITCH: AI BISINDO AKTIF");
        audio.playModeChange(false);
      }
      break;

    // Titik-titik Braille (2x3 Cell Grid di S2, S3, S6, S7, S10, S11)
    case 2:  // Titik 1 (Kiri Atas)
      braille_dots ^= (1 << 0);
      last_dot_time = millis();
      Serial.println("-> Titik 1 Ditekan");
      break;

    case 3:  // Titik 4 (Kanan Atas)
      braille_dots ^= (1 << 3);
      last_dot_time = millis();
      Serial.println("-> Titik 4 Ditekan");
      break;

    case 4:  // S4: Clear All (Hapus Seluruh Kalimat)
      kalimat = "";
      braille_dots = 0;
      Serial.println("-> HAPUS SELURUH TEKS (Clear All)");
      audio.playClear();
      break;

    case 5:  // S5: Backspace (Hapus 1 Karakter Terakhir)
    case 13: // S13: Alternatif Backspace
      if (braille_dots != 0) {
        braille_dots = 0;
        Serial.println("-> Batalkan Titik Aktif");
      } else if (kalimat.length() > 0) {
        kalimat.remove(kalimat.length() - 1);
        Serial.printf("-> Backspace: %s\n", kalimat.c_str());
        audio.playBackspace();
      }
      break;

    case 6:  // Titik 2 (Kiri Tengah)
      braille_dots ^= (1 << 1);
      last_dot_time = millis();
      Serial.println("-> Titik 2 Ditekan");
      break;

    case 7:  // Titik 5 (Kanan Tengah)
      braille_dots ^= (1 << 4);
      last_dot_time = millis();
      Serial.println("-> Titik 5 Ditekan");
      break;

    case 8:  // S8: Enter / Kunci Huruf Sekarang
    case 15: // S15: Alternatif Enter
      commit_braille_char();
      Serial.println("-> Enter / Commit Huruf");
      break;

    case 9:  // S9: Spasi
    case 14: // S14: Alternatif Spasi (Jempol Bawah)
      commit_braille_char();
      kalimat += " ";
      Serial.printf("-> Tambah Spasi -> Kalimat: '%s'\n", kalimat.c_str());
      audio.playChar(' ');
      break;

    case 10: // Titik 3 (Kiri Bawah)
      braille_dots ^= (1 << 2);
      last_dot_time = millis();
      Serial.println("-> Titik 3 Ditekan");
      break;

    case 11: // Titik 6 (Kanan Bawah)
      braille_dots ^= (1 << 5);
      last_dot_time = millis();
      Serial.println("-> Titik 6 Ditekan");
      break;

    case 12: // S12: Mode Angka / Huruf
      number_mode = !number_mode;
      Serial.printf("-> Mode Angka: %s\n", number_mode ? "AKTIF" : "NONAKTIF");
      break;

    case 16: // S16: Tombol TTS / Suara
      Serial.printf("-> SUARA / BACA TEKS: '%s'\n", kalimat.c_str());
      audio.readSentence(kalimat);
      break;

    default:
      Serial.println();
      break;
  }
}

// Fungsi Update Matrix Scanner (Dipanggil di task Core 0 atau loop)
void braille_keypad_update() {
  unsigned long now = millis();

  // Scan Matriks 4x4
  for (int c = 0; c < 4; c++) {
    digitalWrite(COL_PINS[c], LOW);
    pinMode(COL_PINS[c], OUTPUT);
    delayMicroseconds(35); // Beri jeda cukup agar kapasitansi jalur stabil

    for (int r = 0; r < 4; r++) {
      bool is_pressed = (digitalRead(ROW_PINS[r]) == LOW);

      // Deteksi Event Edge: Tombol baru saja ditekan
      if (is_pressed && !key_prev_state[r][c] && (now - last_key_press_time > DEBOUNCE_MS)) {
        last_key_press_time = now;
        key_state[r][c] = true;
        int key_num = (r * 4) + c + 1; // S1 sampai S16
        Serial.printf("[KEYPAD-RAW] Ditekan: Row%d (GPIO%d) & Col%d (GPIO%d) => S%d\n",
                      r + 1, ROW_PINS[r], c + 1, COL_PINS[c], key_num);
        handle_key_action(key_num);
      } else if (!is_pressed && key_prev_state[r][c]) {
        key_state[r][c] = false;
      }
      key_prev_state[r][c] = is_pressed;
    }

    pinMode(COL_PINS[c], INPUT); // Lepas kembali kolom ke High-Z
  }

  // Auto-commit huruf braille setelah tidak ada tombol ditekan selama AUTO_COMMIT_MS
  if (braille_dots != 0 && (now - last_dot_time > AUTO_COMMIT_MS)) {
    commit_braille_char();
  }
}

// Task FreeRTOS Independen pada Core 0 (Scan Keypad 100x per detik)
static void keypad_freertos_task(void *pvParameters) {
  while (true) {
    braille_keypad_update();
    vTaskDelay(pdMS_TO_TICKS(10)); // Jeda 10ms
  }
}

// Inisialisasi Pin Keypad 4x4 & Jalankan Scanner di Core 0
void braille_keypad_init() {
  for (int r = 0; r < 4; r++) {
    pinMode(ROW_PINS[r], INPUT_PULLUP);
  }
  for (int c = 0; c < 4; c++) {
    pinMode(COL_PINS[c], INPUT);
  }

  // Jalankan background task di Core 0 (agar tak terhalang inferensi AI di Core 1)
  xTaskCreatePinnedToCore(
    keypad_freertos_task,
    "KeypadScanner",
    3072,
    NULL,
    2,
    NULL,
    0 // Core 0
  );

  Serial.println("[BRAILLE] Keypad 4x4 Diinisialisasi di Core 0 (R: 4,5,6,7 | C: 13,16,21,47)");
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
