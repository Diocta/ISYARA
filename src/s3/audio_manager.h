#ifndef AUDIO_MANAGER_H
#define AUDIO_MANAGER_H

#include <Arduino.h>
#include <DFRobotDFPlayerMini.h>

// =============================================================================
// ISYARA - Audio Feedback Manager (DFPlayer Mini + Speaker 4Ω 3W)
// Menggunakan HardwareSerial (Serial2) pada ESP32-S3
// =============================================================================

// Pinout HardwareSerial2 ESP32-S3 ke DFPlayer Mini
// ESP32-S3 TX2 -> Resistor 1kΩ -> DFPlayer RX (Pin 2)
// ESP32-S3 RX2 <- DFPlayer TX (Pin 3)
// ESP32-S3 BUSY <- DFPlayer BUSY (Pin 16)
#define DF_TX_PIN   1
#define DF_RX_PIN   2
#define DF_BUSY_PIN 42

// Daftar Nomor Trek MP3 pada MicroSD (Folder /mp3/0001.mp3 dst)
#define AUDIO_TRACK_SPACE        40  // Suara "Spasi" / Klik
#define AUDIO_TRACK_BACKSPACE    41  // Suara "Hapus"
#define AUDIO_TRACK_CLEAR        42  // Suara "Hapus Semua"
#define AUDIO_TRACK_MODE_AI      50  // Suara "Mode BISINDO Aktif"
#define AUDIO_TRACK_MODE_BRAILLE 51  // Suara "Mode Braille Aktif"
#define AUDIO_TRACK_STARTUP      99  // Suara "ISYARA Siap"

class AudioManager {
private:
  HardwareSerial mp3Serial;
  DFRobotDFPlayerMini dfplayer;
  bool is_initialized;
  uint8_t volume_level;

public:
  AudioManager() : mp3Serial(2), is_initialized(false), volume_level(24) {}

  bool begin() {
    pinMode(DF_BUSY_PIN, INPUT_PULLUP);
    
    // Serial2 baudrate DFPlayer standar adalah 9600 baud
    mp3Serial.begin(9600, SERIAL_8N1, DF_RX_PIN, DF_TX_PIN);

    Serial.println("[AUDIO] Memeriksa modul DFPlayer Mini (TX:1, RX:2)...");
    
    // Inisialisasi cepat non-blocking (tanpa reset blocking agar alat langsung siap)
    if (dfplayer.begin(mp3Serial, /*isACK = */false, /*doReset = */false)) {
      is_initialized = true;
      dfplayer.volume(volume_level);
      dfplayer.outputDevice(DFPLAYER_DEVICE_SD);
      Serial.printf("[AUDIO] DFPlayer Mini Terdeteksi & Aktif! Volume: %d/30\n", volume_level);
      playTrack(AUDIO_TRACK_STARTUP);
      return true;
    }

    Serial.println("[AUDIO] Modul DFPlayer belum dicolok / dilewati. Sistem tetap berjalan normal tanpa audio.");
    is_initialized = false;
    return false;
  }

  bool isAvailable() const {
    return is_initialized;
  }

  bool isPlaying() {
    if (!is_initialized) return false;
    return (digitalRead(DF_BUSY_PIN) == LOW);
  }

  void setVolume(uint8_t vol) {
    if (vol > 30) vol = 30;
    volume_level = vol;
    if (is_initialized) {
      dfplayer.volume(volume_level);
    }
  }

  void playTrack(int track_num) {
    if (!is_initialized) {
      Serial.printf("[AUDIO-SIM] Play Track #%d\n", track_num);
      return;
    }
    Serial.printf("[AUDIO] Memutar Track #%d\n", track_num);
    dfplayer.playMp3Folder(track_num);
  }

  // Bunyikan huruf (A-Z) atau angka (0-9)
  void playChar(char c) {
    c = toupper(c);
    int track = 0;
    if (c >= 'A' && c <= 'Z') {
      track = (c - 'A') + 1; // 1 s.d 26
    } else if (c >= '0' && c <= '9') {
      track = (c - '0') + 27; // 27 s.d 36
    } else if (c == ' ') {
      track = AUDIO_TRACK_SPACE;
    }

    if (track > 0) {
      playTrack(track);
    }
  }

  void playModeChange(bool to_braille) {
    playTrack(to_braille ? AUDIO_TRACK_MODE_BRAILLE : AUDIO_TRACK_MODE_AI);
  }

  void playBackspace() {
    playTrack(AUDIO_TRACK_BACKSPACE);
  }

  void playClear() {
    playTrack(AUDIO_TRACK_CLEAR);
  }

  void readSentence(const String &text) {
    if (text.length() == 0) return;
    Serial.printf("[AUDIO] Membaca kalimat: \"%s\"\n", text.c_str());
    playChar(text.charAt(0));
  }
};

extern AudioManager audio;

#endif // AUDIO_MANAGER_H
