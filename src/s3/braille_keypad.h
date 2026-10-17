#ifndef BRAILLE_KEYPAD_H
#define BRAILLE_KEYPAD_H

#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "audio_manager.h"

// =============================================================================
// ISYARA - Modul Keyboard Braille 4x4 Tactile Matrix (ESP32-S3)
// =============================================================================
// Pemetaan Pinout Modul 4x4 Tactile (Option A Breakout PCB):
// Pin 1 (Top)    = Col 4 -> GPIO 4
// Pin 2          = Col 3 -> GPIO 5
// Pin 3          = Col 2 -> GPIO 6
// Pin 4          = Col 1 -> GPIO 7
// Pin 5          = Row 1 -> GPIO 13
// Pin 6          = Row 2 -> GPIO 16
// Pin 7          = Row 3 -> GPIO 21
// Pin 8 (Bottom) = Row 4 -> GPIO 47
// =============================================================================

// Baris (Rows): Pin 5, 6, 7, 8 pada modul (INPUT_PULLUP)
// Pin 5 = Row 1 -> GPIO 13 (S1, S2, S3, S4)
// Pin 6 = Row 2 -> GPIO 16 (S5, S6, S7, S8)
// Pin 8 = Row 3 -> GPIO 47 (S9, S10, S11, S12)
// Pin 7 = Row 4 -> GPIO 21 (S13, S14, S15, S16)
#define KEYPAD_R1 13
#define KEYPAD_R2 16
#define KEYPAD_R3 47
#define KEYPAD_R4 21

// Kolom (Cols): Pin 4, 3, 2, 1 pada modul (OUTPUT LOW saat di-scan)
// Pin 4 = Col 1 -> GPIO 7  (S1, S5, S9, S13)
// Pin 3 = Col 2 -> GPIO 6  (S2, S6, S10, S14)
// Pin 2 = Col 3 -> GPIO 5  (S3, S7, S11, S15)
// Pin 1 = Col 4 -> GPIO 4  (S4, S8, S12, S16)
#define KEYPAD_C1 7
#define KEYPAD_C2 6
#define KEYPAD_C3 5
#define KEYPAD_C4 4

const uint8_t ROW_PINS[4] = {KEYPAD_R1, KEYPAD_R2, KEYPAD_R3, KEYPAD_R4};
const uint8_t COL_PINS[4] = {KEYPAD_C1, KEYPAD_C2, KEYPAD_C3, KEYPAD_C4};

// Indeks ID Tombol S1 - S16 Sesuai Silkscreen PCB Fisik:
// S1  = (R1, C1) | S2  = (R1, C2) | S3  = (R1, C3) | S4  = (R1, C4)
// S5  = (R2, C1) | S6  = (R2, C2) | S7  = (R2, C3) | S8  = (R2, C4)
// S9  = (R3, C1) | S10 = (R3, C2) | S11 = (R3, C3) | S12 = (R3, C4)
// S13 = (R4, C1) | S14 = (R4, C2) | S15 = (R4, C3) | S16 = (R4, C4)

// State Tombol Matriks (Debounce Independen per Tombol)
static bool key_state[4][4] = {false};
static unsigned long key_debounce_time[4][4] = {0};
const unsigned long DEBOUNCE_MS = 35;

// Indikator Tombol Terakhir untuk Feedback Visual OLED
static char last_key_badge[16] = "";
static unsigned long last_key_badge_time = 0;
const unsigned long BADGE_DURATION_MS = 1800;

// Buffer Titik Braille (6-dot cell)
// Bit 0: Titik 1 (S2)  | Bit 3: Titik 4 (S3)
// Bit 1: Titik 2 (S6)  | Bit 4: Titik 5 (S7)
// Bit 2: Titik 3 (S10) | Bit 5: Titik 6 (S11)
static uint8_t braille_dots = 0;
static bool number_mode = false;
static unsigned long last_dot_time = 0;
const unsigned long AUTO_COMMIT_MS = 2500; // Nyaman: 2.5 detik untuk mengecek preview titik

// Mode Sistem
enum DeviceMode {
  MODE_AI_BISINDO = 0,
  MODE_BRAILLE = 1
};
extern DeviceMode current_device_mode;
extern String kalimat;
extern bool tft_butuh_update_mode;

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

// Inisialisasi Pin Keypad 4x4
void braille_keypad_init() {
  for (int r = 0; r < 4; r++) {
    pinMode(ROW_PINS[r], INPUT_PULLUP);
  }
  for (int c = 0; c < 4; c++) {
    pinMode(COL_PINS[c], INPUT);
  }
  Serial.println("[BRAILLE] Keypad 4x4 Diinisialisasi (Rows: 13,16,47,21 | Cols: 7,6,5,4)");
  Serial.println("==================================================");
  Serial.println("  ISYARA - Layout Fisik Keyboard Braille 4x4:");
  Serial.println("  [S1:Mode]   [S2:Dot1]   [S3:Dot4]   [S4:Clear]");
  Serial.println("  [S5:Bksp]   [S6:Dot2]   [S7:Dot5]   [S8:Enter]");
  Serial.println("  [S9:Space]  [S10:Dot3]  [S11:Dot6]  [S12:Num]");
  Serial.println("  [S13:Bksp]  [S14:Space] [S15:Enter] [S16:TTS]");
  Serial.println("==================================================");
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

  // Jika sedang di mode AI BISINDO dan tombol pengetikan ditekan, otomatis beralih ke Braille mode
  if (key_num != 1 && current_device_mode != MODE_BRAILLE) {
    current_device_mode = MODE_BRAILLE;
    tft_butuh_update_mode = true;
    Serial.print("[AUTO SWITCH KE BRAILLE MODE] ");
    audio.playModeChange(true);
  }

  switch (key_num) {
    // Tombol S1: Ganti Mode Sistem (BISINDO AI <-> BRAILLE KEYBOARD)
    case 1:
      snprintf(last_key_badge, sizeof(last_key_badge), "S1:MODE");
      last_key_badge_time = millis();
      tft_butuh_update_mode = true;
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
    case 2:  // S2: Titik 1 (Kiri Atas)
      snprintf(last_key_badge, sizeof(last_key_badge), "S2:DOT 1");
      last_key_badge_time = millis();
      braille_dots ^= (1 << 0);
      last_dot_time = millis();
      Serial.println("-> Titik 1 (Kiri Atas) Ditekan");
      break;

    case 3:  // S3: Titik 4 (Kanan Atas)
      snprintf(last_key_badge, sizeof(last_key_badge), "S3:DOT 4");
      last_key_badge_time = millis();
      braille_dots ^= (1 << 3);
      last_dot_time = millis();
      Serial.println("-> Titik 4 (Kanan Atas) Ditekan");
      break;

    case 4:  // S4: Clear All (Hapus Seluruh Kalimat)
      snprintf(last_key_badge, sizeof(last_key_badge), "S4:CLEAR");
      last_key_badge_time = millis();
      kalimat = "";
      braille_dots = 0;
      Serial.println("-> HAPUS SELURUH TEKS (Clear All)");
      audio.playClear();
      break;

    case 5:  // S5: Backspace (Hapus 1 Karakter Terakhir)
    case 13: // S13: Alternatif Backspace (Pojok Kiri Bawah)
      snprintf(last_key_badge, sizeof(last_key_badge), (key_num == 5) ? "S5:BKSP" : "S13:BKSP");
      last_key_badge_time = millis();
      if (braille_dots != 0) {
        braille_dots = 0;
        Serial.println("-> Batalkan Titik Aktif");
      } else if (kalimat.length() > 0) {
        kalimat.remove(kalimat.length() - 1);
        Serial.printf("-> Backspace: %s\n", kalimat.c_str());
        audio.playBackspace();
      }
      break;

    case 6:  // S6: Titik 2 (Kiri Tengah)
      snprintf(last_key_badge, sizeof(last_key_badge), "S6:DOT 2");
      last_key_badge_time = millis();
      braille_dots ^= (1 << 1);
      last_dot_time = millis();
      Serial.println("-> Titik 2 (Kiri Tengah) Ditekan");
      break;

    case 7:  // S7: Titik 5 (Kanan Tengah)
      snprintf(last_key_badge, sizeof(last_key_badge), "S7:DOT 5");
      last_key_badge_time = millis();
      braille_dots ^= (1 << 4);
      last_dot_time = millis();
      Serial.println("-> Titik 5 (Kanan Tengah) Ditekan");
      break;

    case 8:  // S8: Enter / Kunci Huruf Sekarang
    case 15: // S15: Alternatif Enter (Baris Bawah)
      snprintf(last_key_badge, sizeof(last_key_badge), (key_num == 8) ? "S8:ENTER" : "S15:ENTER");
      last_key_badge_time = millis();
      commit_braille_char();
      Serial.println("-> Enter / Commit Huruf");
      break;

    case 9:  // S9: Spasi
    case 14: // S14: Alternatif Spasi (Baris Bawah)
      snprintf(last_key_badge, sizeof(last_key_badge), (key_num == 9) ? "S9:SPASI" : "S14:SPASI");
      last_key_badge_time = millis();
      commit_braille_char();
      kalimat += " ";
      Serial.printf("-> Tambah Spasi -> Kalimat: '%s'\n", kalimat.c_str());
      audio.playChar(' ');
      break;

    case 10: // S10: Titik 3 (Kiri Bawah)
      snprintf(last_key_badge, sizeof(last_key_badge), "S10:DOT 3");
      last_key_badge_time = millis();
      braille_dots ^= (1 << 2);
      last_dot_time = millis();
      Serial.println("-> Titik 3 (Kiri Bawah) Ditekan");
      break;

    case 11: // S11: Titik 6 (Kanan Bawah)
      snprintf(last_key_badge, sizeof(last_key_badge), "S11:DOT 6");
      last_key_badge_time = millis();
      braille_dots ^= (1 << 5);
      last_dot_time = millis();
      Serial.println("-> Titik 6 (Kanan Bawah) Ditekan");
      break;

    case 12: // S12: Mode Angka / Huruf
      number_mode = !number_mode;
      snprintf(last_key_badge, sizeof(last_key_badge), number_mode ? "S12:[NUM]" : "S12:[A-Z]");
      last_key_badge_time = millis();
      Serial.printf("-> Mode Angka: %s\n", number_mode ? "AKTIF" : "NONAKTIF");
      break;

    case 16: // S16: Tombol TTS / Suara (Pojok Kanan Bawah)
      snprintf(last_key_badge, sizeof(last_key_badge), "S16:TTS");
      last_key_badge_time = millis();
      Serial.printf("-> SUARA / BACA TEKS: '%s'\n", kalimat.c_str());
      audio.readSentence(kalimat);
      break;

    default:
      Serial.println();
      break;
  }
}

// Fungsi Update Matrix Scanner (Debounce Independen per Tombol)
void braille_keypad_update() {
  unsigned long now = millis();

  // Scan Matriks 4x4
  for (int c = 0; c < 4; c++) {
    pinMode(COL_PINS[c], OUTPUT);
    digitalWrite(COL_PINS[c], LOW);
    delayMicroseconds(45); // Waktu stabilisasi sinyal

    for (int r = 0; r < 4; r++) {
      bool is_pressed = (digitalRead(ROW_PINS[r]) == LOW);

      if (is_pressed != key_state[r][c]) {
        if (now - key_debounce_time[r][c] > DEBOUNCE_MS) {
          key_debounce_time[r][c] = now;
          key_state[r][c] = is_pressed;

          if (is_pressed) {
            int key_num = (r * 4) + c + 1; // S1 sampai S16
            Serial.printf("[KEYPAD] Tombol S%d Terdeteksi (Row%d:GPIO%d, Col%d:GPIO%d)\n",
                          key_num, r + 1, ROW_PINS[r], c + 1, COL_PINS[c]);
            handle_key_action(key_num);
          }
        }
      }
    }

    pinMode(COL_PINS[c], INPUT); // Lepas kembali ke High-Z
  }

  // Auto-commit huruf braille setelah tidak ada tombol ditekan selama AUTO_COMMIT_MS
  if (braille_dots != 0 && (now - last_dot_time > AUTO_COMMIT_MS)) {
    commit_braille_char();
  }
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
  // Titik 1 (x:10, y:14) | Titik 4 (x:26, y:14)
  // Titik 2 (x:10, y:25) | Titik 5 (x:26, y:25)
  // Titik 3 (x:10, y:36) | Titik 6 (x:26, y:36)
  int dot_coords[6][2] = {
    {10, 14}, // Titik 1 (S2)
    {10, 25}, // Titik 2 (S6)
    {10, 36}, // Titik 3 (S10)
    {26, 14}, // Titik 4 (S3)
    {26, 25}, // Titik 5 (S7)
    {26, 36}  // Titik 6 (S11)
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
  display.setCursor(46, 14);
  display.setTextSize(1);
  display.print("Char: ");
  display.setTextSize(3);
  display.setCursor(82, 14);
  if (braille_dots != 0) {
    if (preview_ch != '\0' && preview_ch != '?') {
      display.print(preview_ch);
    } else {
      display.print("?");
    }
  } else {
    display.setTextSize(1);
    display.setCursor(82, 22);
    display.print("[-]");
  }

  // 4. Feedback Real-Time Tombol Terakhir (Badge di x:46, y:38)
  if (millis() - last_key_badge_time < BADGE_DURATION_MS && last_key_badge[0] != '\0') {
    display.setTextSize(1);
    display.setCursor(46, 38);
    display.printf("[%s]", last_key_badge);
  }

  // 5. Baris Kalimat Teks Hasil Ketikan (Auto-scroll jika panjang)
  display.setTextSize(1);
  display.setCursor(0, 53);
  display.print("Teks: ");
  String teks_scroll = (kalimat.length() > 14) ? (".." + kalimat.substring(kalimat.length() - 12)) : kalimat;
  display.print(teks_scroll);

  display.display();
}

#endif // BRAILLE_KEYPAD_H
