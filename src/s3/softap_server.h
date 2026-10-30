/*
 * softap_server.h — ISYARA SoftAP Web Dashboard Module
 * =========================================================
 * ESP32-S3 Master, Framework: Arduino (PlatformIO)
 *
 * Fitur:
 *  - SoftAP SSID "ISYARA-MED-01" (WPA2), IP 192.168.4.1, Port 80
 *  - Dashboard HTML interaktif (dark medical theme) → GET /
 *  - REST API JSON:
 *      GET  /api/status  → status perangkat (mode, baterai, uptime)
 *      GET  /api/log     → 10 event terbaru (ring buffer RAM)
 *      POST /api/message → kirim teks ke layar TFT pasien
 *  - Thread-safe via mutex karena loop() berjalan di Core 1,
 *    WebServer handler berjalan di Core 1 juga (single-thread Arduino).
 *
 * Cara pakai:
 *  1. #include "softap_server.h"
 *  2. Panggil softap_begin() di dalam setup()
 *  3. Panggil softap_handle() di dalam loop()
 *  4. Panggil softap_add_event(source, message) setiap kali ada input baru
 *  5. Baca softap_get_nurse_message() untuk mengambil pesan dari perawat
 *
 * Catatan:
 *  - Tidak memerlukan library eksternal — menggunakan WebServer.h bawaan ESP32.
 *  - Embed dashboard HTML sebagai string PROGMEM (flash, bukan RAM).
 *  - Operasi 100% offline / air-gapped.
 *
 * Lisensi: MIT — Tim ISYARA KSTI 2026
 */

#ifndef SOFTAP_SERVER_H
#define SOFTAP_SERVER_H

// ─── Guard: Aktifkan fitur SoftAP dengan mendefinisikan ENABLE_SOFTAP ────────
// Jika tidak didefinisikan, semua fungsi jadi no-op agar bisa dikompilasi
// tanpa mengubah main.cpp — cukup set di platformio.ini:
//   build_flags = ... -DENABLE_SOFTAP
#ifndef ENABLE_SOFTAP
  // Stub declarations agar main.cpp tetap bisa dikompilasi tanpa fitur ini
  inline void softap_begin() {}
  inline void softap_handle() {}
  inline void softap_add_event(const char* /*src*/, const char* /*msg*/) {}
  inline bool softap_has_nurse_message() { return false; }
  inline String softap_get_nurse_message() { return ""; }
#else

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>

// ─── Konfigurasi SoftAP ─────────────────────────────────────────────────────
#define SOFTAP_SSID     "ISYARA-MED-01"
#define SOFTAP_PASSWORD "isyara123"
#define SOFTAP_CHANNEL  6
#define SOFTAP_PORT     80

// ─── Ring Buffer Event Log (10 entri terbaru disimpan di RAM) ───────────────
#define SOFTAP_LOG_SIZE 10

struct TriageEvent {
  char source[24];      // "AI BISINDO" / "Keyboard Braille"
  char message[64];     // Kata / kalimat yang terdeteksi
  unsigned long millis; // millis() saat event terjadi
};

static TriageEvent  s_log[SOFTAP_LOG_SIZE];
static int          s_log_head  = 0;   // Indeks slot berikutnya
static int          s_log_count = 0;   // Jumlah entri terisi (maks SOFTAP_LOG_SIZE)

// ─── Pesan Masuk dari Perawat → Pasien ──────────────────────────────────────
static String       s_nurse_message = "";
static bool         s_nurse_message_available = false;

// ─── Instance WebServer ──────────────────────────────────────────────────────
static WebServer    s_server(SOFTAP_PORT);

// ─── Deklarasi maju handler ──────────────────────────────────────────────────
static void handle_root();
static void handle_api_status();
static void handle_api_log();
static void handle_api_message();
static void handle_not_found();

// ─── Referensi ke variabel di main.cpp ──────────────────────────────────────
extern DeviceMode current_device_mode;
extern String     kalimat;

// ─── Dashboard HTML (PROGMEM, ~6 KB) ────────────────────────────────────────
// HTML single-file: CSS inline, JS inline, no CDN, kompatibel browser tablet.
static const char DASHBOARD_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ISYARA Dashboard Medis</title>
<style>
  :root {
    --bg:      #0A192F;
    --surface: #112240;
    --card:    #1B3A60;
    --cyan:    #00D8F6;
    --teal:    #0D9488;
    --green:   #10B981;
    --amber:   #F59E0B;
    --red:     #EF4444;
    --text:    #E2E8F0;
    --muted:   #7A94B0;
    --border:  #1E3A5F;
    --radius:  12px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh;
    padding: 0;
  }

  /* ── Header ── */
  header {
    background: var(--surface);
    border-bottom: 2px solid var(--cyan);
    padding: 14px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .logo {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--cyan);
    letter-spacing: 2px;
  }
  .logo span { color: var(--text); font-weight: 300; font-size: 0.9rem; }
  .header-status {
    display: flex;
    gap: 18px;
    align-items: center;
    font-size: 0.82rem;
    color: var(--muted);
  }
  .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--green);
    display: inline-block;
    margin-right: 5px;
    animation: pulse 2s infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

  /* ── Main Grid ── */
  main {
    max-width: 960px;
    margin: 0 auto;
    padding: 24px 20px 40px;
    display: grid;
    grid-template-columns: 1fr;
    gap: 20px;
  }

  /* ── Card Base ── */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 22px;
  }
  .card-title {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .card-title::before {
    content: '';
    display: block;
    width: 3px; height: 14px;
    background: var(--cyan);
    border-radius: 2px;
  }

  /* ── Hero Alert Card ── */
  .hero {
    background: linear-gradient(135deg, #0D2240 0%, #143055 100%);
    border: 1px solid var(--cyan);
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 160px; height: 160px;
    border-radius: 50%;
    background: rgba(0, 216, 246, 0.05);
  }
  .hero-message {
    font-size: 2rem;
    font-weight: 700;
    color: var(--cyan);
    min-height: 56px;
    word-break: break-word;
    line-height: 1.2;
    transition: all 0.4s ease;
  }
  .hero-sub {
    margin-top: 10px;
    font-size: 0.82rem;
    color: var(--muted);
  }
  .hero-badge {
    display: inline-block;
    background: rgba(0,216,246,0.12);
    color: var(--cyan);
    border: 1px solid rgba(0,216,246,0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 12px;
  }
  .btn-ack {
    margin-top: 16px;
    padding: 9px 22px;
    background: transparent;
    border: 1px solid var(--teal);
    color: var(--teal);
    border-radius: 8px;
    font-size: 0.84rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    letter-spacing: 0.5px;
  }
  .btn-ack:hover { background: var(--teal); color: #fff; }

  /* ── Message Box ── */
  .msg-row {
    display: flex;
    gap: 10px;
    margin-top: 4px;
  }
  .msg-input {
    flex: 1;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    padding: 10px 14px;
    font-size: 0.9rem;
    outline: none;
    transition: border 0.2s;
  }
  .msg-input:focus { border-color: var(--cyan); }
  .msg-input::placeholder { color: var(--muted); }
  .btn-send {
    padding: 10px 22px;
    background: var(--cyan);
    color: var(--bg);
    border: none;
    border-radius: 8px;
    font-size: 0.88rem;
    font-weight: 700;
    cursor: pointer;
    transition: opacity 0.2s;
    white-space: nowrap;
  }
  .btn-send:hover { opacity: 0.85; }
  .btn-send:disabled { opacity: 0.4; cursor: not-allowed; }
  .send-status {
    font-size: 0.78rem;
    margin-top: 7px;
    min-height: 18px;
    color: var(--green);
  }

  /* ── Log List ── */
  .log-list { list-style: none; }
  .log-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
  }
  .log-item:last-child { border-bottom: none; }
  .log-icon {
    width: 34px; height: 34px;
    border-radius: 8px;
    background: var(--card);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem;
    flex-shrink: 0;
  }
  .log-icon.ai  { border: 1px solid var(--cyan); color: var(--cyan); }
  .log-icon.br  { border: 1px solid var(--teal); color: var(--teal); }
  .log-icon.nrs { border: 1px solid var(--amber); color: var(--amber); }
  .log-text { flex: 1; min-width: 0; }
  .log-msg {
    font-size: 0.9rem;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .log-meta {
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 2px;
  }
  .log-empty {
    text-align: center;
    color: var(--muted);
    font-size: 0.85rem;
    padding: 18px 0;
  }

  /* ── Footer ── */
  footer {
    text-align: center;
    color: var(--muted);
    font-size: 0.73rem;
    padding: 14px;
    border-top: 1px solid var(--border);
    letter-spacing: 0.5px;
  }
</style>
</head>
<body>

<header>
  <div class="logo">ISYARA <span>Dashboard Medis</span></div>
  <div class="header-status">
    <span><span class="dot"></span>Terhubung</span>
    <span id="h-mode">—</span>
    <span id="h-uptime">—</span>
  </div>
</header>

<main>

  <!-- 1. Hero Alert Card -->
  <div class="card hero">
    <div class="card-title">Pesan Aktif Pasien</div>
    <div class="hero-badge" id="alert-source">Menunggu...</div>
    <div class="hero-message" id="alert-msg">—</div>
    <div class="hero-sub" id="alert-time">Belum ada isyarat yang masuk</div>
    <button class="btn-ack" onclick="ackAlert()">&#10003; Konfirmasi Diterima</button>
  </div>

  <!-- 2. Two-Way Messaging -->
  <div class="card">
    <div class="card-title">Kirim Pesan ke Pasien</div>
    <div class="msg-row">
      <input class="msg-input" id="nurse-msg" type="text"
        placeholder="Ketik pesan untuk ditampilkan di layar TFT pasien..."
        maxlength="60" onkeydown="if(event.key==='Enter')sendMessage()">
      <button class="btn-send" id="btn-send" onclick="sendMessage()">Kirim</button>
    </div>
    <div class="send-status" id="send-status"></div>
  </div>

  <!-- 3. Recent Log -->
  <div class="card">
    <div class="card-title">Log Aktivitas Terbaru</div>
    <ul class="log-list" id="log-list">
      <li class="log-empty">Memuat data...</li>
    </ul>
  </div>

</main>

<footer>ISYARA v2.0 &mdash; SoftAP 192.168.4.1 &mdash; Offline &amp; Air-Gapped</footer>

<script>
// ─── State ───────────────────────────────────────────────────────────────────
let lastAlertMsg = '';
let acknowledged = false;

// ─── Polling Utama (setiap 3 detik) ──────────────────────────────────────────
function refreshAll() {
  fetchStatus();
  fetchLog();
}

// ─── Fetch Status Perangkat ───────────────────────────────────────────────────
function fetchStatus() {
  fetch('/api/status')
    .then(r => r.json())
    .then(d => {
      document.getElementById('h-mode').textContent =
        d.mode === 'AI_BISINDO' ? 'Mode: AI BISINDO' : 'Mode: Braille';
      document.getElementById('h-uptime').textContent = 'Uptime: ' + formatUptime(d.uptime_s);
    })
    .catch(() => {});
}

// ─── Fetch Log Aktivitas ──────────────────────────────────────────────────────
function fetchLog() {
  fetch('/api/log')
    .then(r => r.json())
    .then(data => {
      const events = data.events || [];
      const list = document.getElementById('log-list');

      if (events.length === 0) {
        list.innerHTML = '<li class="log-empty">Belum ada aktivitas.</li>';
        return;
      }

      // Update hero dengan event terbaru
      const newest = events[0];
      if (newest.message !== lastAlertMsg) {
        lastAlertMsg = newest.message;
        acknowledged = false;
        document.getElementById('alert-msg').textContent = newest.message || '—';
        document.getElementById('alert-source').textContent = newest.source || '—';
        document.getElementById('alert-time').textContent =
          'Diterima ' + formatUptime(newest.uptime_s) + ' sejak nyala';
      }

      // Render max 3 log terbaru
      const show = events.slice(0, 3);
      list.innerHTML = show.map(e => {
        const cls  = e.source.includes('Braille') ? 'br' : (e.source.includes('Perawat') ? 'nrs' : 'ai');
        const icon = cls === 'ai' ? 'AI' : (cls === 'br' ? 'BR' : 'RN');
        return `<li class="log-item">
          <div class="log-icon ${cls}">${icon}</div>
          <div class="log-text">
            <div class="log-msg">${escHtml(e.message)}</div>
            <div class="log-meta">${escHtml(e.source)} &bull; ${formatUptime(e.uptime_s)} sejak nyala</div>
          </div>
        </li>`;
      }).join('');
    })
    .catch(() => {});
}

// ─── Kirim Pesan Perawat ke TFT Pasien ───────────────────────────────────────
function sendMessage() {
  const input = document.getElementById('nurse-msg');
  const btn   = document.getElementById('btn-send');
  const status = document.getElementById('send-status');
  const msg   = input.value.trim();
  if (!msg) return;

  btn.disabled = true;
  status.style.color = '#7A94B0';
  status.textContent = 'Mengirim...';

  fetch('/api/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: msg })
  })
  .then(r => r.json())
  .then(d => {
    if (d.ok) {
      status.style.color = '#10B981';
      status.textContent = 'Pesan berhasil dikirim ke layar pasien.';
      input.value = '';
    } else {
      status.style.color = '#EF4444';
      status.textContent = 'Gagal: ' + (d.error || 'Kesalahan tidak diketahui');
    }
  })
  .catch(() => {
    status.style.color = '#EF4444';
    status.textContent = 'Koneksi terputus. Coba lagi.';
  })
  .finally(() => {
    btn.disabled = false;
    setTimeout(() => { status.textContent = ''; }, 4000);
  });
}

// ─── Akui / Dismiss Alert ─────────────────────────────────────────────────────
function ackAlert() {
  acknowledged = true;
  document.getElementById('alert-msg').style.opacity = '0.4';
  document.getElementById('alert-time').textContent = 'Sudah dikonfirmasi oleh perawat.';
}

// ─── Helper ───────────────────────────────────────────────────────────────────
function formatUptime(s) {
  if (s == null) return '—';
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return h + 'j ' + m + 'm';
  if (m > 0) return m + 'm ' + sec + 'd';
  return sec + 'd';
}

function escHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ─── Mulai polling ────────────────────────────────────────────────────────────
refreshAll();
setInterval(refreshAll, 3000);
</script>
</body>
</html>
)rawliteral";

// ─── Implementasi Handler & API ──────────────────────────────────────────────

static void handle_cors_headers() {
  s_server.sendHeader("Access-Control-Allow-Origin", "*");
  s_server.sendHeader("Cache-Control", "no-cache");
}

static void handle_root() {
  handle_cors_headers();
  s_server.send_P(200, "text/html", DASHBOARD_HTML);
}

static void handle_api_status() {
  handle_cors_headers();
  char json[200];
  const char* mode_str = (current_device_mode == MODE_BRAILLE) ? "BRAILLE" : "AI_BISINDO";
  snprintf(json, sizeof(json),
    "{\"ok\":true,\"mode\":\"%s\",\"uptime_s\":%lu,\"ssid\":\"%s\"}",
    mode_str,
    millis() / 1000UL,
    SOFTAP_SSID
  );
  s_server.send(200, "application/json", json);
}

static void handle_api_log() {
  handle_cors_headers();

  // Build JSON array dari ring buffer (urutan terbaru → terlama)
  String json = "{\"ok\":true,\"count\":";
  json += s_log_count;
  json += ",\"events\":[";

  int n = min(s_log_count, SOFTAP_LOG_SIZE);
  for (int i = 0; i < n; i++) {
    // Mulai dari entri terbaru (head - 1, ke belakang)
    int idx = ((s_log_head - 1 - i) + SOFTAP_LOG_SIZE) % SOFTAP_LOG_SIZE;
    const TriageEvent& e = s_log[idx];

    if (i > 0) json += ",";
    json += "{\"source\":\"";
    // Escape karakter kutip dalam source/message
    for (const char* p = e.source; *p; p++) {
      if (*p == '"') json += "\\\""; else json += *p;
    }
    json += "\",\"message\":\"";
    for (const char* p = e.message; *p; p++) {
      if (*p == '"') json += "\\\""; else json += *p;
    }
    json += "\",\"uptime_s\":";
    json += (e.millis / 1000UL);
    json += "}";
  }

  json += "]}";
  s_server.send(200, "application/json", json);
}

static void handle_api_message() {
  handle_cors_headers();

  if (s_server.method() == HTTP_OPTIONS) {
    s_server.send(204);
    return;
  }

  if (!s_server.hasArg("plain")) {
    s_server.send(400, "application/json", "{\"ok\":false,\"error\":\"Body kosong\"}");
    return;
  }

  String body = s_server.arg("plain");

  // Parse JSON sederhana — cari nilai "message":"..."
  int key_pos = body.indexOf("\"message\"");
  if (key_pos < 0) {
    s_server.send(400, "application/json", "{\"ok\":false,\"error\":\"Field message tidak ditemukan\"}");
    return;
  }

  int colon = body.indexOf(':', key_pos + 9);
  int q1    = body.indexOf('"', colon + 1);
  int q2    = body.indexOf('"', q1 + 1);

  if (q1 < 0 || q2 < 0 || q2 <= q1) {
    s_server.send(400, "application/json", "{\"ok\":false,\"error\":\"Format pesan tidak valid\"}");
    return;
  }

  String msg = body.substring(q1 + 1, q2);
  msg.trim();

  if (msg.length() == 0) {
    s_server.send(400, "application/json", "{\"ok\":false,\"error\":\"Pesan tidak boleh kosong\"}");
    return;
  }
  if (msg.length() > 60) {
    msg = msg.substring(0, 60);
  }

  // Simpan pesan untuk di-poll oleh loop() via softap_has_nurse_message()
  s_nurse_message = msg;
  s_nurse_message_available = true;

  // Catat juga sebagai event log
  softap_add_event("Perawat", msg.c_str());

  Serial.printf("[SoftAP] Pesan perawat diterima: \"%s\"\n", msg.c_str());
  s_server.send(200, "application/json", "{\"ok\":true}");
}

static void handle_not_found() {
  handle_cors_headers();
  s_server.send(404, "application/json", "{\"ok\":false,\"error\":\"Endpoint tidak ditemukan\"}");
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Tambahkan event baru ke ring buffer log.
 * Panggil dari main.cpp setiap kali ada input yang dikunci.
 * @param source  "AI BISINDO" / "Keyboard Braille" / "Perawat"
 * @param message Kata / kalimat yang dihasilkan
 */
void softap_add_event(const char* source, const char* message) {
  TriageEvent& e = s_log[s_log_head];
  strncpy(e.source,  source,  sizeof(e.source)  - 1);
  strncpy(e.message, message, sizeof(e.message) - 1);
  e.source[sizeof(e.source) - 1]   = '\0';
  e.message[sizeof(e.message) - 1] = '\0';
  e.millis = millis();

  s_log_head = (s_log_head + 1) % SOFTAP_LOG_SIZE;
  if (s_log_count < SOFTAP_LOG_SIZE) s_log_count++;
}

/**
 * Cek apakah ada pesan baru dari perawat yang belum diproses.
 */
bool softap_has_nurse_message() {
  return s_nurse_message_available;
}

/**
 * Ambil pesan dari perawat dan reset flag.
 * Harus dipanggil setelah softap_has_nurse_message() == true.
 */
String softap_get_nurse_message() {
  s_nurse_message_available = false;
  String tmp = s_nurse_message;
  s_nurse_message = "";
  return tmp;
}

/**
 * Inisialisasi SoftAP dan WebServer.
 * Panggil di dalam setup() setelah periferal lain siap.
 */
void softap_begin() {
  WiFi.softAP(SOFTAP_SSID, SOFTAP_PASSWORD, SOFTAP_CHANNEL);
  IPAddress ip = WiFi.softAPIP();

  Serial.printf("\n[SoftAP] Aktif! SSID: %s\n", SOFTAP_SSID);
  Serial.printf("[SoftAP] IP   : %s\n", ip.toString().c_str());
  Serial.printf("[SoftAP] Buka di browser: http://%s\n", ip.toString().c_str());

  s_server.on("/",            HTTP_GET,  handle_root);
  s_server.on("/api/status",  HTTP_GET,  handle_api_status);
  s_server.on("/api/log",     HTTP_GET,  handle_api_log);
  s_server.on("/api/message", HTTP_POST, handle_api_message);
  s_server.on("/api/message", HTTP_OPTIONS, handle_api_message); // CORS preflight
  s_server.onNotFound(handle_not_found);

  s_server.begin();
  Serial.printf("[SoftAP] WebServer Port %d siap.\n\n", SOFTAP_PORT);
}

/**
 * Proses request HTTP yang masuk.
 * WAJIB dipanggil di setiap iterasi loop() agar non-blocking.
 */
void softap_handle() {
  s_server.handleClient();
}

#endif // ENABLE_SOFTAP
#endif // SOFTAP_SERVER_H

