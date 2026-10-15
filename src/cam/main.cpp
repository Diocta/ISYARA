#include "esp_camera.h"
#include <WiFi.h>
#include <esp_wifi.h>
#include "esp_http_server.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// ==========================================
// WIFI DAN PASSWORD
// ==========================================
const char* ssid = "ayam";
const char* password = "ayam12345678";

// Pin AI-Thinker OV3660
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

httpd_handle_t stream_httpd = NULL;
bool web_active = false;

static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=123456789000000000000987654321";
static const char* _STREAM_BOUNDARY = "\r\n--123456789000000000000987654321\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

// Ukuran frame harus sama dengan input model di ESP32-S3.
#define AI_FRAME_SIZE 9216

// Fungsi untuk mengirim 1 frame gambar AI ke ESP32-S3 ketika diminta (Handshake)
void kirim_frame_ke_s3(camera_fb_t * fb) {
  if (!fb) return;
  if (fb->len != AI_FRAME_SIZE) return;
  Serial.write(0xAA);
  Serial.write(0x55);
  Serial.write(fb->buf, fb->len);
}

// Fungsi untuk melayani live streaming cermin di HP/Browser
static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t * fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t * _jpg_buf = NULL;
  char part_buf[128];

  res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
  if (res != ESP_OK) return res;

  web_active = true;

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      res = ESP_FAIL;
      break;
    }

    // 1. SISTEM HANDSHAKE: Cek apakah ESP32-S3 meminta frame ('C')
    if (Serial.available()) {
      if (Serial.read() == 'C') {
        kirim_frame_ke_s3(fb);
      }
    }

    // 2. TAMPILKAN LIVE VIDEO DI WEB HP (CERMIN)
    bool jpeg_converted = frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
    esp_camera_fb_return(fb);
    fb = NULL;

    if (jpeg_converted) {
      res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
      if (res == ESP_OK) {
        size_t hlen = snprintf(part_buf, sizeof(part_buf), _STREAM_PART, _jpg_buf_len);
        res = httpd_resp_send_chunk(req, part_buf, hlen);
      }
      if (res == ESP_OK) {
        res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
      }
      free(_jpg_buf);
      _jpg_buf = NULL;
    }

    if (res != ESP_OK) break;
  }

  web_active = false;
  return res;
}

// Halaman utama web cermin di layar HP
static esp_err_t index_handler(httpd_req_t *req) {
  const char* html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>"
                     "<title>ISYARA Mirror</title>"
                     "<style>body{background:#121212;color:#fff;text-align:center;font-family:sans-serif;margin:0;padding:20px;}"
                     "img{width:288px;height:288px;image-rendering:pixelated;border:3px solid #00E5FF;border-radius:12px;box-shadow:0 0 20px #00e5ff55;}"
                     "</style></head><body>"
                     "<h2>ISYARA - Cermin Kamera (96x96)</h2>"
                     "<p>Gunakan layar ini untuk memposisikan tangan Anda</p>"
                     "<img src='/stream'>"
                     "</body></html>";
  return httpd_resp_send(req, html, HTTPD_RESP_USE_STRLEN);
}

void startCameraServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;

  httpd_uri_t index_uri = {
    .uri       = "/",
    .method    = HTTP_GET,
    .handler   = index_handler,
    .user_ctx  = NULL
  };
  httpd_uri_t stream_uri = {
    .uri       = "/stream",
    .method    = HTTP_GET,
    .handler   = stream_handler,
    .user_ctx  = NULL
  };

  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &index_uri);
    httpd_register_uri_handler(stream_httpd, &stream_uri);
  }
}

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // Matikan brownout detector

  // Baudrate harus sama dengan ESP32-S3
  Serial.begin(460800);

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  
  // Format Grayscale 96x96 untuk AI Edge Impulse
  config.pixel_format = PIXFORMAT_GRAYSCALE; 
  config.frame_size = FRAMESIZE_96X96;  
  config.jpeg_quality = 15;
  config.fb_count = 2;
  config.grab_mode = CAMERA_GRAB_LATEST;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) return;

  sensor_t * s = esp_camera_sensor_get();
  if (s != NULL) {
    s->set_vflip(s, 1);
    s->set_brightness(s, 1);
    s->set_framesize(s, FRAMESIZE_96X96);
  }

  // Koneksi ke WiFi untuk preview di HP
  WiFi.setTxPower(WIFI_POWER_8_5dBm);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  startCameraServer();
}

void loop() {
  // Jika tidak ada HP yang membuka web stream, tetap respon jika S3 meminta frame ('C')
  if (!web_active) {
    if (Serial.available()) {
      if (Serial.read() == 'C') {
        camera_fb_t * fb = esp_camera_fb_get();
        if (fb) {
          kirim_frame_ke_s3(fb);
          esp_camera_fb_return(fb);
        }
      }
    }
    delay(10);
  } else {
    delay(10);
  }
}
