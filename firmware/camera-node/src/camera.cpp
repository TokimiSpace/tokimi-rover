// SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
// SPDX-License-Identifier: Apache-2.0

#include "camera.h"

#include <esp_camera.h>
#include <esp_err.h>

namespace TokimiCamera {
namespace {

// GOOUUU ESP32-S3-CAM camera connector mapping. This is intentionally not the
// AI Thinker ESP32-CAM mapping.
constexpr int kPinPwdn = -1;
constexpr int kPinReset = -1;
constexpr int kPinXclk = 15;
constexpr int kPinSiod = 4;
constexpr int kPinSioc = 5;
constexpr int kPinD0 = 11;
constexpr int kPinD1 = 9;
constexpr int kPinD2 = 8;
constexpr int kPinD3 = 10;
constexpr int kPinD4 = 12;
constexpr int kPinD5 = 18;
constexpr int kPinD6 = 17;
constexpr int kPinD7 = 16;
constexpr int kPinVsync = 6;
constexpr int kPinHref = 7;
constexpr int kPinPclk = 13;

volatile bool online = false;
char errorMessage[128] = "camera has not been initialized";
portMUX_TYPE sequenceMux = portMUX_INITIALIZER_UNLOCKED;
uint32_t frameSequence = 0;

void setError(const char* message) {
  strlcpy(errorMessage, message, sizeof(errorMessage));
}

}  // namespace

bool begin() {
  if (online) {
    return true;
  }

  Serial.println("[camera] initializing OV3660");
  Serial.println(
      "[camera] pins: XCLK=15 PCLK=13 VSYNC=6 HREF=7 SDA=4 SCL=5");
  Serial.println(
      "[camera] data: D0=11 D1=9 D2=8 D3=10 D4=12 D5=18 D6=17 D7=16");

  const bool hasPsram = psramFound();
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = kPinD0;
  config.pin_d1 = kPinD1;
  config.pin_d2 = kPinD2;
  config.pin_d3 = kPinD3;
  config.pin_d4 = kPinD4;
  config.pin_d5 = kPinD5;
  config.pin_d6 = kPinD6;
  config.pin_d7 = kPinD7;
  config.pin_xclk = kPinXclk;
  config.pin_pclk = kPinPclk;
  config.pin_vsync = kPinVsync;
  config.pin_href = kPinHref;
  config.pin_sccb_sda = kPinSiod;
  config.pin_sccb_scl = kPinSioc;
  config.pin_pwdn = kPinPwdn;
  config.pin_reset = kPinReset;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_HVGA;
  config.jpeg_quality = kJpegQuality;
  config.fb_count = hasPsram ? 2 : 1;
  config.fb_location =
      hasPsram ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  config.grab_mode =
      hasPsram ? CAMERA_GRAB_LATEST : CAMERA_GRAB_WHEN_EMPTY;

  Serial.printf(
      "[camera] format=JPEG resolution=%ux%u quality=%u XCLK=%u MHz buffers=%u "
      "location=%s grab=%s\n",
      kWidth, kHeight, kJpegQuality, config.xclk_freq_hz / 1000000,
      config.fb_count, hasPsram ? "PSRAM" : "DRAM",
      hasPsram ? "LATEST" : "WHEN_EMPTY");

  const esp_err_t result = esp_camera_init(&config);
  if (result != ESP_OK) {
    snprintf(errorMessage, sizeof(errorMessage),
             "esp_camera_init failed: %s (0x%08x)", esp_err_to_name(result),
             static_cast<unsigned int>(result));
    Serial.printf("[camera] ERROR: %s\n", errorMessage);
    Serial.println("[camera] camera remains offline; automatic reboot disabled");
    return false;
  }

  sensor_t* sensor = esp_camera_sensor_get();
  if (sensor == nullptr) {
    setError("driver initialized but sensor handle is null");
    Serial.printf("[camera] ERROR: %s\n", errorMessage);
    esp_camera_deinit();
    return false;
  }

  Serial.printf("[camera] detected sensor PID=0x%04x\n", sensor->id.PID);
  if (sensor->id.PID != OV3660_PID) {
    snprintf(errorMessage, sizeof(errorMessage),
             "unexpected sensor PID 0x%04x; OV3660 expected (0x%04x)",
             sensor->id.PID, OV3660_PID);
    Serial.printf("[camera] ERROR: %s\n", errorMessage);
    esp_camera_deinit();
    return false;
  }

  const int frameResult = sensor->set_framesize(sensor, FRAMESIZE_HVGA);
  const int qualityResult = sensor->set_quality(sensor, kJpegQuality);
  if (frameResult != 0 || qualityResult != 0) {
    snprintf(errorMessage, sizeof(errorMessage),
             "OV3660 settings failed: framesize=%d quality=%d", frameResult,
             qualityResult);
    Serial.printf("[camera] ERROR: %s\n", errorMessage);
    esp_camera_deinit();
    return false;
  }

  camera_fb_t* firstFrame = esp_camera_fb_get();
  if (firstFrame == nullptr) {
    setError("OV3660 initialized but first JPEG capture failed");
    Serial.printf("[camera] ERROR: %s\n", errorMessage);
    esp_camera_deinit();
    return false;
  }

  const bool firstFrameValid = firstFrame->format == PIXFORMAT_JPEG &&
                               firstFrame->width == kWidth &&
                               firstFrame->height == kHeight;
  if (!firstFrameValid) {
    snprintf(errorMessage, sizeof(errorMessage),
             "unexpected first frame: format=%d size=%ux%u",
             firstFrame->format, firstFrame->width, firstFrame->height);
    Serial.printf("[camera] ERROR: %s\n", errorMessage);
    esp_camera_fb_return(firstFrame);
    esp_camera_deinit();
    return false;
  }

  Serial.printf("[camera] first JPEG captured: %u bytes\n", firstFrame->len);
  esp_camera_fb_return(firstFrame);

  online = true;
  setError("none");
  Serial.printf("[camera] OV3660 online at %ux%u JPEG quality %u, zero-copy HTTP path\n",
                kWidth, kHeight, kJpegQuality);
  return true;
}

bool isOnline() {
  return online;
}

const char* lastError() {
  return errorMessage;
}

const char* sensorName() {
  return online ? "OV3660" : "unavailable";
}

bool acquireJpeg(JpegFrame* output) {
  if (output == nullptr || !online) {
    return false;
  }

  camera_fb_t* frame = esp_camera_fb_get();
  if (frame == nullptr || frame->buf == nullptr || frame->len == 0) {
    if (frame != nullptr) {
      esp_camera_fb_return(frame);
    }
    return false;
  }

  portENTER_CRITICAL(&sequenceMux);
  const uint32_t sequence = ++frameSequence;
  portEXIT_CRITICAL(&sequenceMux);

  output->data = frame->buf;
  output->length = frame->len;
  output->sequence = sequence;
  output->capturedAtMs = millis();
  output->driverFrame = frame;
  return true;
}

bool copyLatestJpeg(JpegFrame* output, uint32_t timeoutMs) {
  (void)timeoutMs;
  return acquireJpeg(output);
}

void releaseJpeg(JpegFrame* frame) {
  if (frame == nullptr) {
    return;
  }
  if (frame->driverFrame != nullptr) {
    esp_camera_fb_return(static_cast<camera_fb_t*>(frame->driverFrame));
  }
  *frame = {};
}

}  // namespace TokimiCamera
