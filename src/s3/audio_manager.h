#ifndef AUDIO_MANAGER_H
#define AUDIO_MANAGER_H

#include <Arduino.h>
#include <DFRobotDFPlayerMini.h>
#include "word_dictionary.h"

// =============================================================================
// ISYARA - Audio Feedback Manager (DFPlayer Mini + Speaker 4Ω 3W)
// Menggunakan HardwareSerial (Serial2) pada ESP32-S3
// =============================================================================

// Pinout HardwareSerial2 ESP32-S3 ke DFPlayer Mini
#define DF_TX_PIN   1
#define DF_RX_PIN   2
#define DF_BUSY_PIN 42

// Daftar Nomor Trek MP3 pada MicroSD (Folder /mp3/0001.mp3 dst)
#define AUDIO_TRACK_SPACE        40  // Suara "Spasi"
#define AUDIO_TRACK_BACKSPACE    41  // Suara "Hapus"
#define AUDIO_TRACK_CLEAR        42  // Suara "Hapus Semua"
#define AUDIO_TRACK_MODE_AI      50  // Suara "Mode Bahasa Isyarat Aktif"
#define AUDIO_TRACK_MODE_BRAILLE 51  // Suara "Mode Keyboard Braille Aktif"
#define AUDIO_TRACK_STARTUP      99  // Suara "Sistem ISYARA Siap"

class AudioManager {
private:
  HardwareSerial mp3Serial;
  DFRobotDFPlayerMini dfplayer;
  bool is_initialized;
  uint8_t volume_level;

public:
  AudioManager() : mp3Serial(2), is_initialized(false), volume_level(25) {}

  bool begin() {
    pinMode(DF_BUSY_PIN, INPUT_PULLUP);
    
    // Serial2 baudrate DFPlayer standar adalah 9600 baud
    mp3Serial.begin(9600, SERIAL_8N1, DF_RX_PIN, DF_TX_PIN);

    Serial.println("[AUDIO] Memeriksa modul DFPlayer Mini (TX:1, RX:2)...");
    
    // Inisialisasi cepat non-blocking
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
      Serial.printf("[AUDIO-SIM] Play Track #%04d\n", track_num);
      return;
    }
    Serial.printf("[AUDIO] Memutar Track #%04d\n", track_num);
    dfplayer.playMp3Folder(track_num);
  }

  // Putar track dan tunggu hingga audio selesai berbunyi (dengan proteksi timeout)
  void playAndWait(int track_num, unsigned long fallback_ms = 700) {
    if (!is_initialized) {
      Serial.printf("[AUDIO-SIM-WAIT] Play Track #%04d\n", track_num);
      delay(300);
      return;
    }
    playTrack(track_num);
    delay(100); // Beri waktu modul mengubah pin BUSY ke LOW

    // Jika pin BUSY aktif LOW, tunggu sampai selesai bicara
    if (digitalRead(DF_BUSY_PIN) == LOW) {
      unsigned long start = millis();
      while (digitalRead(DF_BUSY_PIN) == LOW && (millis() - start < 4500)) {
        delay(15);
        yield();
      }
    } else {
      // Fallback jika pin BUSY belum disambung kabel jumper
      delay(fallback_ms);
    }
    delay(120); // Jeda antar kata/huruf
  }

  // Dapatkan nomor track untuk satu karakter
  int getCharTrack(char c) {
    c = toupper(c);
    if (c >= 'A' && c <= 'Z') {
      return (c - 'A') + 1; // 1 s.d 26
    } else if (c >= '0' && c <= '9') {
      return (c - '0') + 27; // 27 s.d 36
    } else if (c == ' ') {
      return AUDIO_TRACK_SPACE;
    }
    return 0;
  }

  // Bunyikan huruf (A-Z) atau angka (0-9) - Non blocking (untuk pengetikan live)
  void playChar(char c) {
    int track = getCharTrack(c);
    if (track > 0) {
      playTrack(track);
    }
  }

  // Bunyikan huruf dengan menunggu (untuk mode eja)
  void playCharAndWait(char c) {
    int track = getCharTrack(c);
    if (track > 0) {
      playAndWait(track, 500);
    }
  }

  // Bunyikan kata penuh langsung dari kamus audio kosa kata (Non-blocking)
  void playWord(const String &word) {
    int track = cariTrackKata(word);
    if (track > 0) {
      playTrack(track);
    } else {
      // Jika kata belum ada di kamus audio, bunyikan huruf pertamanya
      if (word.length() > 0) {
        playChar(word.charAt(0));
      }
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

  // =============================================================================
  // Smart TTS Sentence Reader:
  // Membaca frasa/kata jika ada di kamus, atau mengeja jika nama/singkatan
  // =============================================================================
  void readSentence(const String &raw_text) {
    String text = raw_text;
    text.trim();
    if (text.length() == 0) return;

    Serial.printf("[AUDIO] Membaca kalimat: \"%s\"\n", text.c_str());

    int start_idx = 0;
    int len = text.length();

    while (start_idx < len) {
      // Abaikan spasi berlebih
      while (start_idx < len && text.charAt(start_idx) == ' ') {
        start_idx++;
      }
      if (start_idx >= len) break;

      // 1. Coba cocokkan dengan frasa multi-kata terlebih dahulu (misal: "TERIMA KASIH")
      bool phrase_found = false;
      String sisa_teks = text.substring(start_idx);
      sisa_teks.toUpperCase();

      for (size_t i = 0; i < TOTAL_WORDS; i++) {
        String phrase = WORD_DICTIONARY[i].phrase;
        if (sisa_teks.startsWith(phrase)) {
          int p_len = phrase.length();
          if (sisa_teks.length() == p_len || sisa_teks.charAt(p_len) == ' ') {
            Serial.printf("[AUDIO-TTS] Frasa Ditemukan: \"%s\" (Track #%04d)\n",
                          phrase.c_str(), WORD_DICTIONARY[i].track);
            playAndWait(WORD_DICTIONARY[i].track, 1200);
            start_idx += p_len;
            phrase_found = true;
            break;
          }
        }
      }

      if (phrase_found) continue;

      // 2. Ambil 1 kata tunggal hingga spasi berikutnya
      int next_space = text.indexOf(' ', start_idx);
      String word = (next_space == -1) ? text.substring(start_idx) : text.substring(start_idx, next_space);
      start_idx = (next_space == -1) ? len : next_space + 1;

      word.trim();
      if (word.length() == 0) continue;

      // 3. Cek apakah kata tunggal ada di kamus kosa kata
      int track = cariTrackKata(word);
      if (track > 0) {
        Serial.printf("[AUDIO-TTS] Kata Dikenal: \"%s\" (Track #%04d)\n", word.c_str(), track);
        playAndWait(track, 900);
      } else {
        // 4. Jika kata tidak dikenal (nama orang / singkatan / huruf acak), eja per huruf!
        Serial.printf("[AUDIO-TTS] Kata Tidak Dikenal, Mengeja: \"%s\"\n", word.c_str());
        for (size_t k = 0; k < word.length(); k++) {
          char c = word.charAt(k);
          playCharAndWait(c);
        }
      }
      delay(150); // Jeda halus antar kata
    }

    Serial.println("[AUDIO] Selesai membaca kalimat.");
  }
};

extern AudioManager audio;

#endif // AUDIO_MANAGER_H
