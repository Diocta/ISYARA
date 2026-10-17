#include <Arduino.h>
#include "esp_camera.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// =============================================================================
// ISYARA - ESP32-CAM Slave Firmware (OV3660)
// Mengirim 1 frame citra 96x96 Grayscale (9216 bytes) ke ESP32-S3 via UART
// Baudrate: 460800 baud | Trigger: karakter 'C' dari Master
// =============================================================================

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

// Ukuran frame harus sama dengan input model Edge Impulse di ESP32-S3
#define AI_FRAME_SIZE 9216

// Kirim 1 frame ke ESP32-S3 ketika diminta (Handshake [0xAA, 0x55] + data)
void kirim_frame_ke_s3(camera_fb_t * fb) {
  if (!fb) return;
  if (fb->len != AI_FRAME_SIZE) return;
  Serial.write(0xAA);
  Serial.write(0x55);
  Serial.write(fb->buf, fb->len);
}

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // Matikan brownout detector

  // Baudrate komunikasi UART ke ESP32-S3 Master
  Serial.begin(460800);

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;

  // Format Grayscale 96x96 untuk AI Edge Impulse
  config.pixel_format = PIXFORMAT_GRAYSCALE;
  config.frame_size   = FRAMESIZE_96X96;
  config.jpeg_quality = 15;
  config.fb_count     = 2;
  config.grab_mode    = CAMERA_GRAB_LATEST;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) return;

  sensor_t * s = esp_camera_sensor_get();
  if (s != NULL) {
    s->set_vflip(s, 1);
    s->set_hmirror(s, 0);       // Normal (sesuai arah tangan asli)
    s->set_brightness(s, 1);    // Kecerahan optimal (+1)
    s->set_contrast(s, 2);      // Naikkan kontras (+2) agar siluet kontur jari tegas
    s->set_sharpness(s, 2);     // Pertajam garis tepi jari (+2)
    s->set_whitebal(s, 1);      // Auto White Balance aktif
    s->set_awb_gain(s, 1);      // AWB Gain aktif
    s->set_exposure_ctrl(s, 1); // Auto Exposure Control aktif
    s->set_gainceiling(s, (gainceiling_t)2); // Batasi gain agar tidak muncul bintik noise
    s->set_framesize(s, FRAMESIZE_96X96);
  }
}

void loop() {
  // Hanya ambil frame dan kirim saat ESP32-S3 mengirimkan karakter trigger 'C'
  if (Serial.available()) {
    int cmd = Serial.read();
    if (cmd == 'C') {
      camera_fb_t * fb = esp_camera_fb_get();
      if (fb) {
        kirim_frame_ke_s3(fb);
        esp_camera_fb_return(fb);
      }
    }
  } else {
    // KUNCI PENDINGIN CPU & ANTI-OVERHEAT:
    // Saat ESP32-S3 berada pada Mode Braille atau tidak meminta frame,
    // biarkan CPU masuk ke mode idle selama 15ms. Beban CPU turun ke <1% dan suhu tetap dingin!
    vTaskDelay(pdMS_TO_TICKS(15));
  }
}
