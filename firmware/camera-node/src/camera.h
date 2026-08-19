// SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <Arduino.h>

namespace TokimiCamera {

constexpr uint16_t kWidth = 480;
constexpr uint16_t kHeight = 320;
constexpr uint8_t kJpegQuality = 18;
constexpr uint8_t kTargetFps = 10;

struct JpegFrame {
  uint8_t* data = nullptr;
  size_t length = 0;
  uint32_t sequence = 0;
  uint32_t capturedAtMs = 0;
  void* driverFrame = nullptr;
};

bool begin();
bool isOnline();
const char* lastError();
const char* sensorName();

// Borrows a JPEG directly from the camera driver without allocating or copying.
// Every successful acquireJpeg() call must be paired with releaseJpeg().
bool acquireJpeg(JpegFrame* output);
// Compatibility alias used by the existing HTTP handlers.
bool copyLatestJpeg(JpegFrame* output, uint32_t timeoutMs);
void releaseJpeg(JpegFrame* frame);

}  // namespace TokimiCamera
