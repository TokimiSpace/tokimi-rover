// SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
// SPDX-License-Identifier: Apache-2.0

#include <Arduino.h>
#include <esp_heap_caps.h>
#include <esp_system.h>

#include "camera.h"
#include "web.h"

namespace {

constexpr uint32_t kLogIntervalMs = 10000;
uint32_t lastLogMs = 0;

const char* resetReasonName(esp_reset_reason_t reason) {
  switch (reason) {
    case ESP_RST_POWERON:
      return "power-on";
    case ESP_RST_EXT:
      return "external reset";
    case ESP_RST_SW:
      return "software reset";
    case ESP_RST_PANIC:
      return "exception/panic";
    case ESP_RST_INT_WDT:
      return "interrupt watchdog";
    case ESP_RST_TASK_WDT:
      return "task watchdog";
    case ESP_RST_WDT:
      return "other watchdog";
    case ESP_RST_DEEPSLEEP:
      return "deep sleep";
    case ESP_RST_BROWNOUT:
      return "brownout";
    case ESP_RST_SDIO:
      return "SDIO";
    default:
      return "unknown";
  }
}

void logMemory() {
  const uint32_t largestInternal = heap_caps_get_largest_free_block(
      MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
  Serial.printf(
      "[memory] heap free=%u bytes, minimum=%u bytes, largest=%u bytes\n",
      ESP.getFreeHeap(), ESP.getMinFreeHeap(), largestInternal);
  if (psramFound()) {
    const uint32_t largestPsram =
        heap_caps_get_largest_free_block(MALLOC_CAP_SPIRAM);
    Serial.printf(
        "[memory] PSRAM detected: total=%u bytes, free=%u bytes, "
        "largest=%u bytes\n",
        ESP.getPsramSize(), ESP.getFreePsram(), largestPsram);
  } else {
    Serial.println("[memory] ERROR: PSRAM was not detected");
  }
}

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(1200);

  Serial.println();
  Serial.println("==================================================");
  Serial.println("Tokimi Ground Support Rover - Camera board");
  Serial.println("Stage 5: camera Web UI");
  Serial.println("==================================================");
  Serial.printf("[boot] reset reason: %s (%d)\n",
                resetReasonName(esp_reset_reason()), esp_reset_reason());
  Serial.printf("[boot] chip=%s revision=%u cores=%u CPU=%u MHz\n",
                ESP.getChipModel(), ESP.getChipRevision(), ESP.getChipCores(),
                ESP.getCpuFreqMHz());
  Serial.printf("[boot] flash=%u bytes, sketch=%u bytes\n",
                ESP.getFlashChipSize(), ESP.getSketchSize());
  logMemory();

  if (TokimiCamera::begin()) {
    Serial.println("[boot] camera ready");
  } else {
    Serial.printf("[boot] Stage 2 camera unavailable: %s\n",
                  TokimiCamera::lastError());
    Serial.println("[boot] firmware will remain running for diagnostics");
  }

  if (TokimiWeb::begin()) {
    Serial.println("[boot] Stage 5 ready - camera Web UI available");
  } else {
    Serial.printf("[boot] web unavailable: %s\n", TokimiWeb::lastError());
  }
}

void loop() {
  TokimiWeb::maintain();
  const uint32_t now = millis();
  if (now - lastLogMs >= kLogIntervalMs) {
    lastLogMs = now;
    Serial.printf("[health] uptime=%lu ms\n", static_cast<unsigned long>(now));
    logMemory();
  }
  delay(10);
}
