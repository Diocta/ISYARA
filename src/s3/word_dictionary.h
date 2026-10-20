#ifndef WORD_DICTIONARY_H
#define WORD_DICTIONARY_H

#include <Arduino.h>

struct WordEntry {
  const char* phrase;
  int track;
};

// =============================================================================
// ISYARA - Kamus Kosa Kata Cerdas Bahasa Indonesia (Track 101 - 170)
// =============================================================================
const WordEntry WORD_DICTIONARY[] = {
  // Frasa multi-kata (dicek lebih dulu)
  {"TERIMA KASIH", 112},
  {"SAMA-SAMA",    113},
  {"SAMA SAMA",    113},
  {"SELAMAT PAGI", 116},
  {"SELAMAT SIANG",117},
  {"SELAMAT MALAM",118},
  {"RUMAH SAKIT",  132},
  {"KAMAR MANDI",  158},

  // Kata tunggal
  {"SAYA",    101},
  {"KAMU",    102},
  {"DIA",     103},
  {"KITA",    104},
  {"KAMI",    105},
  {"MEREKA",  106},
  {"MAKAN",   107},
  {"MINUM",   108},
  {"MAU",     109},
  {"BISA",    110},
  {"TOLONG",  111},
  {"HALO",    114},
  {"HAI",     115},
  {"APA",     119},
  {"SIAPA",   120},
  {"DIMANA",  121},
  {"KAPAN",   122},
  {"KENAPA",  123},
  {"BAGAIMANA", 124},
  {"YA",      125},
  {"TIDAK",   126},
  {"BUKAN",   127},
  {"ADA",     128},
  {"SAKIT",   129},
  {"DOKTER",  130},
  {"OBAT",    131},
  {"NAMA",    133},
  {"BANTU",   134},
  {"SUKA",    135},
  {"PERGI",   136},
  {"PULANG",  137},
  {"RUMAH",   138},
  {"SEKOLAH", 139},
  {"TEMAN",   140},
  {"SENANG",  141},
  {"SEDIH",   142},
  {"LAPAR",   143},
  {"HAUS",    144},
  {"DAN",     145},
  {"ATAU",    146},
  {"DI",      147},
  {"KE",      148},
  {"DARI",    149},
  {"INI",     150},
  {"ITU",     151},
  {"BAIK",    152},
  {"SEHAT",   153},
  {"BELAJAR", 154},
  {"TIDUR",   155},
  {"PERMISI", 156},
  {"MAAF",    157},
  {"TOILET",  159},
  {"AIR",     160},
  {"NASI",    161},
  {"ROTI",    162},
  {"DUDUK",   163},
  {"BERDIRI", 164},
  {"JALAN",   165},
  {"MELIHAT", 166},
  {"MENDENGAR", 167},
  {"BICARA",  168},
  {"TULIS",   169},
  {"BACA",    170}
};

const size_t TOTAL_WORDS = sizeof(WORD_DICTIONARY) / sizeof(WORD_DICTIONARY[0]);

// Fungsi pencarian kosa kata
inline int cariTrackKata(const String &target) {
  String upper = target;
  upper.toUpperCase();
  upper.trim();

  for (size_t i = 0; i < TOTAL_WORDS; i++) {
    if (upper.equals(WORD_DICTIONARY[i].phrase)) {
      return WORD_DICTIONARY[i].track;
    }
  }
  return -1; // Tidak ditemukan (nanti dieja per huruf)
}

#endif // WORD_DICTIONARY_H

