// SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
// SPDX-License-Identifier: Apache-2.0

#include "display.h"

#include <Arduino.h>
#include <U8g2lib.h>
#include <WiFi.h>
#include <Wire.h>
#include <esp_system.h>
#include <esp_wifi.h>

#include <cstdio>
#include <cstring>

namespace {

constexpr std::uint8_t kSdaPin = 8;
constexpr std::uint8_t kSclPin = 3;
constexpr std::uint8_t kFirstI2cAddress = 0x01;
constexpr std::uint8_t kLastI2cAddress = 0x7E;
constexpr std::uint8_t kOledAddressA = 0x3C;
constexpr std::uint8_t kOledAddressB = 0x3D;
constexpr std::uint32_t kSplashDurationMs = 2000;
constexpr std::uint32_t kStatusPageDurationMs = 2000;
constexpr std::uint32_t kExpressionDurationMs = 6000;
constexpr std::uint32_t kSosDurationMs = 10000;
constexpr std::uint32_t kSosFrameIntervalMs = 500;
constexpr std::uint32_t kSleepAfterMs = 60000;
constexpr std::uint32_t kSleepFrameIntervalMs = 1000;
constexpr std::uint32_t kPupilStepIntervalMs = 250;
constexpr std::uint32_t kDizzyFrameIntervalMs = 400;
constexpr std::uint32_t kBlinkDurationMs = 300;
constexpr std::uint32_t kBlinkDelayMinMs = 2500;
constexpr std::uint32_t kBlinkDelayMaxMs = 6000;
constexpr std::uint32_t kPupilDelayMinMs = 1800;
constexpr std::uint32_t kPupilDelayMaxMs = 4200;
constexpr std::size_t kMaxExtraStatuses = 5;

U8G2_SH1106_128X64_NONAME_F_HW_I2C oled(
    U8G2_R0, U8X8_PIN_NONE, kSclPin, kSdaPin);

bool oledReady = false;
std::uint32_t splashStartedMs = 0;
char motorStatus[8] = "READY";
char cameraStatus[8] = "ONLINE";

enum class Motion {
  stopped,
  forward,
  backward,
  left,
  right,
  forwardLeft,
  forwardRight,
  backwardLeft,
  backwardRight,
};

enum class Expression {
  dashboard,
  happy,
  angry,
  sad,
  joy,
  rude,
  tasaTokimi,
  tasaAstronaut,
  sos,
};

Expression activeExpression = Expression::dashboard;
std::uint32_t expressionStartedMs = 0;
std::uint32_t lastExpressionFrameMs = 0;
bool expressionDirty = false;

Motion activeMotion = Motion::stopped;
std::uint32_t lastMotionActivityMs = 0;
std::uint32_t nextBlinkMs = 0;
std::uint32_t blinkUntilMs = 0;
std::uint32_t nextPupilTargetMs = 0;
std::uint32_t lastPupilStepMs = 0;
std::uint32_t lastSleepFrameMs = 0;
std::uint32_t lastMotionFrameMs = 0;
std::int8_t pupilX = 0;
std::int8_t pupilY = 0;
std::int8_t targetPupilX = 0;
std::int8_t targetPupilY = 0;
bool blinkActive = false;
bool faceDirty = true;

struct ExtraStatus {
  char name[10];
  char value[10];
  bool active;
};

ExtraStatus extraStatuses[kMaxExtraStatuses]{};

void drawCentered(const char* text, std::uint8_t baseline) {
  const std::uint8_t width = oled.getStrWidth(text);
  const std::uint8_t x = width < oled.getDisplayWidth()
                             ? (oled.getDisplayWidth() - width) / 2
                             : 0;
  oled.drawStr(x, baseline, text);
}

void drawSplash() {
  oled.clearBuffer();

  oled.setFont(u8g2_font_ncenB08_tr);
  drawCentered("TOKIMI", 15);

  oled.setFont(u8g2_font_6x12_tf);
  drawCentered("ESP32-S3", 36);
  drawCentered("OLED OK", 56);

  oled.sendBuffer();
}

bool deadlineReached(std::uint32_t now, std::uint32_t deadline) {
  return static_cast<std::int32_t>(now - deadline) >= 0;
}

std::uint32_t randomDelay(std::uint32_t minimum, std::uint32_t maximum) {
  return minimum + esp_random() % (maximum - minimum + 1U);
}

void scheduleBlink(std::uint32_t now) {
  nextBlinkMs = now + randomDelay(kBlinkDelayMinMs, kBlinkDelayMaxMs);
}

void schedulePupilTarget(std::uint32_t now) {
  targetPupilX = static_cast<std::int8_t>(esp_random() % 15U) - 7;
  targetPupilY = static_cast<std::int8_t>(esp_random() % 9U) - 4;
  nextPupilTargetMs =
      now + randomDelay(kPupilDelayMinMs, kPupilDelayMaxMs);
}

bool isReverseMotion(Motion motion) {
  return motion == Motion::backward || motion == Motion::backwardLeft ||
         motion == Motion::backwardRight;
}

void drawMotionBrows(bool reverse) {
  if (reverse) {
    oled.drawLine(10, 16, 54, 10);
    oled.drawLine(10, 17, 54, 11);
    oled.drawLine(74, 10, 118, 16);
    oled.drawLine(74, 11, 118, 17);
    return;
  }

  oled.drawLine(10, 10, 54, 16);
  oled.drawLine(10, 11, 54, 17);
  oled.drawLine(74, 16, 118, 10);
  oled.drawLine(74, 17, 118, 11);
}

void drawOpenEyes(std::int8_t offsetX, std::int8_t offsetY, bool focused,
                  bool reverse) {
  oled.clearBuffer();

  if (focused) {
    drawMotionBrows(reverse);
  }

  oled.drawRFrame(7, 17, 51, 36, 10);
  oled.drawRFrame(8, 18, 49, 34, 9);
  oled.drawRFrame(70, 17, 51, 36, 10);
  oled.drawRFrame(71, 18, 49, 34, 9);

  const std::int16_t leftPupilX = 32 + offsetX;
  const std::int16_t rightPupilX = 96 + offsetX;
  const std::int16_t pupilCenterY = 35 + offsetY;
  oled.drawDisc(leftPupilX, pupilCenterY, 7);
  oled.drawDisc(rightPupilX, pupilCenterY, 7);
  oled.setDrawColor(0);
  oled.drawDisc(leftPupilX - 2, pupilCenterY - 2, 2);
  oled.drawDisc(rightPupilX - 2, pupilCenterY - 2, 2);
  oled.setDrawColor(1);

  oled.sendBuffer();
}

void drawClosedEyes(bool focused, bool reverse) {
  oled.clearBuffer();
  if (focused) {
    drawMotionBrows(reverse);
  }

  oled.drawLine(10, 34, 56, 34);
  oled.drawLine(10, 35, 56, 35);
  oled.drawLine(72, 34, 118, 34);
  oled.drawLine(72, 35, 118, 35);
  oled.sendBuffer();
}

void drawSleepingEyes(std::uint32_t phase) {
  oled.clearBuffer();
  oled.drawCircle(33, 29, 15,
                  U8G2_DRAW_LOWER_LEFT | U8G2_DRAW_LOWER_RIGHT);
  oled.drawCircle(33, 29, 14,
                  U8G2_DRAW_LOWER_LEFT | U8G2_DRAW_LOWER_RIGHT);
  oled.drawCircle(95, 29, 15,
                  U8G2_DRAW_LOWER_LEFT | U8G2_DRAW_LOWER_RIGHT);
  oled.drawCircle(95, 29, 14,
                  U8G2_DRAW_LOWER_LEFT | U8G2_DRAW_LOWER_RIGHT);

  oled.setFont(u8g2_font_ncenB08_tr);
  oled.drawStr(104, 15, "Z");
  if ((phase % 2U) != 0U) {
    oled.setFont(u8g2_font_6x12_tf);
    oled.drawStr(115, 28, "z");
  }
  oled.sendBuffer();
}

void motionEyeOffset(Motion motion, std::int8_t& x, std::int8_t& y) {
  x = 0;
  y = 0;
  switch (motion) {
    case Motion::forward:
      y = -6;
      return;
    case Motion::backward:
      y = 6;
      return;
    case Motion::left:
      x = -10;
      return;
    case Motion::right:
      x = 10;
      return;
    case Motion::forwardLeft:
      x = -8;
      y = -6;
      return;
    case Motion::forwardRight:
      x = 8;
      y = -6;
      return;
    case Motion::backwardLeft:
      x = -8;
      y = 6;
      return;
    case Motion::backwardRight:
      x = 8;
      y = 6;
      return;
    case Motion::stopped:
    default:
      return;
  }
}

struct SpiralPoint {
  std::int8_t x;
  std::int8_t y;
};

constexpr SpiralPoint kSpiralPoints[] = {
    {15, 0},  {14, 6},  {10, 11}, {4, 14},   {-3, 14}, {-9, 11},
    {-13, 6}, {-14, 0}, {-12, -6}, {-8, -10}, {-2, -12}, {4, -10},
    {8, -6},  {9, 0},   {7, 5},    {2, 7},    {-3, 6},  {-6, 2},
    {-5, -2}, {-2, -4}, {2, -3},   {3, 0},    {1, 2},   {0, 0},
};

void rotateSpiralPoint(const SpiralPoint& point, std::uint8_t phase,
                       std::int16_t& x, std::int16_t& y) {
  switch (phase % 4U) {
    case 1:
      x = -point.y;
      y = point.x;
      return;
    case 2:
      x = -point.x;
      y = -point.y;
      return;
    case 3:
      x = point.y;
      y = -point.x;
      return;
    case 0:
    default:
      x = point.x;
      y = point.y;
      return;
  }
}

void drawSpiralEye(std::int16_t centerX, std::int16_t centerY,
                   std::uint8_t phase) {
  oled.drawCircle(centerX, centerY, 19);

  bool firstPoint = true;
  std::int16_t previousX = 0;
  std::int16_t previousY = 0;
  for (const SpiralPoint& point : kSpiralPoints) {
    std::int16_t rotatedX = 0;
    std::int16_t rotatedY = 0;
    rotateSpiralPoint(point, phase, rotatedX, rotatedY);
    const std::int16_t x = centerX + rotatedX;
    const std::int16_t y = centerY + rotatedY;
    if (!firstPoint) {
      oled.drawLine(previousX, previousY, x, y);
    }
    firstPoint = false;
    previousX = x;
    previousY = y;
  }

  oled.drawDisc(centerX, centerY, 2);
}

void drawDizzyEyes(std::uint32_t now) {
  std::uint8_t phase =
      static_cast<std::uint8_t>((now / kDizzyFrameIntervalMs) % 4U);
  if (activeMotion == Motion::left) {
    phase = static_cast<std::uint8_t>((4U - phase) % 4U);
  }

  oled.clearBuffer();
  drawSpiralEye(34, 32, phase);
  drawSpiralEye(94, 32, phase);
  oled.sendBuffer();
}

void drawMotionEyes(std::uint32_t now) {
  if (activeMotion == Motion::left || activeMotion == Motion::right) {
    drawDizzyEyes(now);
    return;
  }

  if (isReverseMotion(activeMotion)) {
    std::int8_t x = 0;
    if (activeMotion == Motion::backwardLeft) {
      x = -6;
    } else if (activeMotion == Motion::backwardRight) {
      x = 6;
    }

    oled.clearBuffer();
    oled.drawCircle(34, 30, 16);
    oled.drawCircle(34, 30, 15);
    oled.drawCircle(94, 30, 16);
    oled.drawCircle(94, 30, 15);
    oled.drawCircle(34 + x, 33, 7);
    oled.drawCircle(94 + x, 33, 7);
    oled.drawDisc(34 + x, 33, 3);
    oled.drawDisc(94 + x, 33, 3);
    oled.drawHLine(52, 54, 25);
    oled.drawHLine(52, 55, 25);
    oled.sendBuffer();
    return;
  }

  std::int8_t x = 0;
  std::int8_t y = 0;
  motionEyeOffset(activeMotion, x, y);
  drawOpenEyes(x, y, true, isReverseMotion(activeMotion));
}

void updateDefaultFace(std::uint32_t now) {
  if (activeMotion != Motion::stopped) {
    const bool dizzyFrameDue =
        (activeMotion == Motion::left || activeMotion == Motion::right) &&
        now - lastMotionFrameMs >= kDizzyFrameIntervalMs;
    if (faceDirty || dizzyFrameDue) {
      faceDirty = false;
      lastMotionFrameMs = now;
      drawMotionEyes(now);
    }
    return;
  }

  if (now - lastMotionActivityMs >= kSleepAfterMs) {
    if (faceDirty || lastSleepFrameMs == 0 ||
        now - lastSleepFrameMs >= kSleepFrameIntervalMs) {
      faceDirty = false;
      lastSleepFrameMs = now;
      drawSleepingEyes(now / kSleepFrameIntervalMs);
    }
    return;
  }

  if (!blinkActive && deadlineReached(now, nextBlinkMs)) {
    blinkActive = true;
    blinkUntilMs = now + kBlinkDurationMs;
    faceDirty = true;
  } else if (blinkActive && deadlineReached(now, blinkUntilMs)) {
    blinkActive = false;
    scheduleBlink(now);
    faceDirty = true;
  }

  if (deadlineReached(now, nextPupilTargetMs)) {
    schedulePupilTarget(now);
  }

  if (now - lastPupilStepMs >= kPupilStepIntervalMs) {
    lastPupilStepMs = now;
    if (pupilX != targetPupilX) {
      pupilX += pupilX < targetPupilX ? 1 : -1;
      faceDirty = true;
    }
    if (pupilY != targetPupilY) {
      pupilY += pupilY < targetPupilY ? 1 : -1;
      faceDirty = true;
    }
  }

  if (faceDirty) {
    faceDirty = false;
    if (blinkActive) {
      drawClosedEyes(false, false);
    } else {
      drawOpenEyes(pupilX, pupilY, false, false);
    }
  }
}

void drawExpressionHeader(const char* label) {
  oled.setFont(u8g2_font_ncenB08_tr);
  drawCentered(label, 10);
  oled.drawHLine(0, 12, oled.getDisplayWidth());
}

void drawHappy() {
  oled.clearBuffer();
  drawExpressionHeader("HAPPY");

  oled.drawCircle(35, 35, 11,
                  U8G2_DRAW_UPPER_LEFT | U8G2_DRAW_UPPER_RIGHT);
  oled.drawCircle(35, 35, 10,
                  U8G2_DRAW_UPPER_LEFT | U8G2_DRAW_UPPER_RIGHT);
  oled.drawCircle(93, 35, 11,
                  U8G2_DRAW_UPPER_LEFT | U8G2_DRAW_UPPER_RIGHT);
  oled.drawCircle(93, 35, 10,
                  U8G2_DRAW_UPPER_LEFT | U8G2_DRAW_UPPER_RIGHT);
  oled.drawCircle(64, 43, 11,
                  U8G2_DRAW_LOWER_LEFT | U8G2_DRAW_LOWER_RIGHT);
  oled.drawCircle(64, 43, 10,
                  U8G2_DRAW_LOWER_LEFT | U8G2_DRAW_LOWER_RIGHT);

  oled.sendBuffer();
}

void drawAngry() {
  oled.clearBuffer();
  drawExpressionHeader("ANGRY");

  oled.drawLine(18, 18, 49, 27);
  oled.drawLine(18, 19, 49, 28);
  oled.drawLine(79, 27, 110, 18);
  oled.drawLine(79, 28, 110, 19);
  oled.drawCircle(38, 38, 8);
  oled.drawCircle(90, 38, 8);
  oled.drawDisc(41, 39, 3);
  oled.drawDisc(87, 39, 3);
  oled.drawCircle(64, 62, 11,
                  U8G2_DRAW_UPPER_LEFT | U8G2_DRAW_UPPER_RIGHT);
  oled.drawCircle(64, 62, 10,
                  U8G2_DRAW_UPPER_LEFT | U8G2_DRAW_UPPER_RIGHT);

  oled.sendBuffer();
}

void drawSad() {
  oled.clearBuffer();
  drawExpressionHeader("SAD");

  oled.drawLine(19, 27, 48, 18);
  oled.drawLine(19, 28, 48, 19);
  oled.drawLine(80, 18, 109, 27);
  oled.drawLine(80, 19, 109, 28);
  oled.drawCircle(37, 38, 7);
  oled.drawCircle(91, 38, 7);
  oled.drawDisc(37, 40, 2);
  oled.drawDisc(91, 40, 2);
  oled.drawLine(30, 47, 28, 54);
  oled.drawLine(29, 47, 27, 54);
  oled.drawCircle(64, 63, 11,
                  U8G2_DRAW_UPPER_LEFT | U8G2_DRAW_UPPER_RIGHT);
  oled.drawCircle(64, 63, 10,
                  U8G2_DRAW_UPPER_LEFT | U8G2_DRAW_UPPER_RIGHT);

  oled.sendBuffer();
}

void drawJoy() {
  oled.clearBuffer();
  drawExpressionHeader("JOY");

  oled.drawCircle(35, 36, 11);
  oled.drawCircle(93, 36, 11);
  oled.drawDisc(35, 36, 6);
  oled.drawDisc(93, 36, 6);
  oled.setDrawColor(0);
  oled.drawDisc(32, 33, 2);
  oled.drawDisc(90, 33, 2);
  oled.setDrawColor(1);
  oled.drawDisc(64, 54, 9);
  oled.setDrawColor(0);
  oled.drawBox(57, 48, 14, 4);
  oled.setDrawColor(1);
  oled.drawLine(15, 46, 24, 43);
  oled.drawLine(104, 43, 113, 46);

  oled.sendBuffer();
}

void drawRude() {
  oled.clearBuffer();
  drawExpressionHeader("FUCK");

  // A compact raised-middle-finger silhouette for the 128x64 display.
  oled.drawRBox(58, 15, 12, 39, 4);
  oled.drawRBox(46, 29, 13, 27, 4);
  oled.drawRBox(69, 29, 13, 27, 4);
  oled.drawRBox(81, 35, 12, 22, 4);
  oled.drawRBox(42, 45, 51, 19, 5);
  oled.drawTriangle(43, 47, 29, 39, 35, 57);

  oled.setDrawColor(0);
  oled.drawVLine(58, 31, 14);
  oled.drawVLine(70, 31, 14);
  oled.drawVLine(82, 37, 9);
  oled.setDrawColor(1);

  oled.sendBuffer();
}

void drawTasaCollaboration(const char* partner) {
  oled.clearBuffer();

  oled.drawPixel(8, 8);
  oled.drawHLine(5, 8, 7);
  oled.drawVLine(8, 5, 7);
  oled.drawPixel(119, 13);
  oled.drawHLine(116, 13, 7);
  oled.drawVLine(119, 10, 7);
  oled.drawPixel(14, 52);
  oled.drawPixel(113, 55);

  oled.setFont(u8g2_font_ncenB14_tr);
  drawCentered("TASA", 20);
  oled.setFont(u8g2_font_6x12_tf);
  drawCentered("feat", 37);
  oled.setFont(u8g2_font_ncenB08_tr);
  drawCentered(partner, 57);

  oled.sendBuffer();
}

void drawSos(bool inverted) {
  oled.clearBuffer();
  if (inverted) {
    oled.drawBox(0, 0, oled.getDisplayWidth(), oled.getDisplayHeight());
    oled.setDrawColor(0);
  }

  oled.drawFrame(0, 0, oled.getDisplayWidth(), oled.getDisplayHeight());
  oled.setFont(u8g2_font_ncenB18_tr);
  drawCentered("SOS", 38);
  oled.setFont(u8g2_font_6x12_tf);
  drawCentered("OLED ALERT", 57);
  oled.setDrawColor(1);
  oled.sendBuffer();
}

void drawExpression(Expression expression, std::uint32_t now) {
  switch (expression) {
    case Expression::happy:
      drawHappy();
      return;
    case Expression::angry:
      drawAngry();
      return;
    case Expression::sad:
      drawSad();
      return;
    case Expression::joy:
      drawJoy();
      return;
    case Expression::rude:
      drawRude();
      return;
    case Expression::tasaTokimi:
      drawTasaCollaboration("TOKIMI");
      return;
    case Expression::tasaAstronaut:
      drawTasaCollaboration("ASTRONAUT");
      return;
    case Expression::sos:
      drawSos(((now / kSosFrameIntervalMs) % 2U) != 0U);
      return;
    case Expression::dashboard:
    default:
      return;
  }
}

bool isAccessPointActive() {
  const wifi_mode_t mode = WiFi.getMode();
  return mode == WIFI_MODE_AP || mode == WIFI_MODE_APSTA;
}

bool readAccessPointRssi(std::int32_t& rssi) {
  wifi_sta_list_t stations{};
  if (esp_wifi_ap_get_sta_list(&stations) != ESP_OK || stations.num == 0) {
    return false;
  }

  rssi = stations.sta[0].rssi;
  return true;
}

void formatUptime(char* output, std::size_t outputSize) {
  const std::uint32_t totalSeconds = millis() / 1000U;
  if (totalSeconds < 3600U) {
    std::snprintf(output, outputSize, "Up:%lus",
                  static_cast<unsigned long>(totalSeconds));
    return;
  }

  if (totalSeconds < 86400U) {
    std::snprintf(output, outputSize, "Up:%luh%02lum",
                  static_cast<unsigned long>(totalSeconds / 3600U),
                  static_cast<unsigned long>((totalSeconds / 60U) % 60U));
    return;
  }

  std::snprintf(output, outputSize, "Up:%lud%02luh",
                static_cast<unsigned long>(totalSeconds / 86400U),
                static_cast<unsigned long>((totalSeconds / 3600U) % 24U));
}

std::size_t extraStatusCount() {
  std::size_t count = 0;
  for (const ExtraStatus& status : extraStatuses) {
    if (status.active) {
      ++count;
    }
  }
  return count;
}

void drawSubsystemStatus() {
  char line[32];
  const std::size_t extraCount = extraStatusCount();
  const std::size_t page =
      (millis() / kStatusPageDurationMs) % (extraCount + 1U);

  if (page == 0) {
    std::snprintf(line, sizeof(line), "M:%.5s Camera:%.6s", motorStatus,
                  cameraStatus);
    oled.drawStr(0, 62, line);
    return;
  }

  std::size_t activeIndex = 0;
  for (const ExtraStatus& status : extraStatuses) {
    if (!status.active) {
      continue;
    }

    ++activeIndex;
    if (activeIndex == page) {
      std::snprintf(line, sizeof(line), "%.9s: %.9s", status.name,
                    status.value);
      oled.drawStr(0, 62, line);
      return;
    }
  }
}

void drawDashboard() {
  char line[32];
  char uptime[16];
  const bool stationConnected = WiFi.status() == WL_CONNECTED;
  const bool accessPointActive = isAccessPointActive();
  const std::uint8_t accessPointClients =
      accessPointActive ? WiFi.softAPgetStationNum() : 0;

  const char* wifiStatus = "Offline";
  if (stationConnected || accessPointClients > 0) {
    wifiStatus = "Connected";
  } else if (accessPointActive) {
    wifiStatus = "AP Ready";
  }

  IPAddress ip;
  if (stationConnected) {
    ip = WiFi.localIP();
  } else if (accessPointActive) {
    ip = WiFi.softAPIP();
  }

  std::int32_t rssi = 0;
  bool hasRssi = false;
  if (stationConnected) {
    rssi = WiFi.RSSI();
    hasRssi = true;
  } else if (accessPointClients > 0) {
    hasRssi = readAccessPointRssi(rssi);
  }

  oled.clearBuffer();
  oled.setFont(u8g2_font_ncenB08_tr);
  drawCentered("TOKIMI ROVER", 9);
  oled.drawHLine(0, 11, oled.getDisplayWidth());

  oled.setFont(u8g2_font_6x12_tf);
  std::snprintf(line, sizeof(line), "WiFi:%s", wifiStatus);
  oled.drawStr(0, 21, line);

  if (hasRssi) {
    std::snprintf(line, sizeof(line), "RSSI:%ld dBm",
                  static_cast<long>(rssi));
  } else {
    std::snprintf(line, sizeof(line), "RSSI:N/A");
  }
  oled.drawStr(0, 31, line);

  std::snprintf(line, sizeof(line), "IP:%u.%u.%u.%u", ip[0], ip[1], ip[2],
                ip[3]);
  oled.drawStr(0, 41, line);

  formatUptime(uptime, sizeof(uptime));
  std::snprintf(line, sizeof(line), "Heap:%luKB %s",
                static_cast<unsigned long>(ESP.getFreeHeap() / 1024U),
                uptime);
  oled.drawStr(0, 51, line);

  drawSubsystemStatus();

  oled.sendBuffer();
}

void copyStatus(char* destination, std::size_t destinationSize,
                const char* value) {
  if (value == nullptr || destinationSize == 0) {
    return;
  }

  std::strncpy(destination, value, destinationSize - 1);
  destination[destinationSize - 1] = '\0';
}

void setExpression(const char* value) {
  Expression expression = Expression::dashboard;
  if (std::strcmp(value, "happy") == 0) {
    expression = Expression::happy;
  } else if (std::strcmp(value, "angry") == 0) {
    expression = Expression::angry;
  } else if (std::strcmp(value, "sad") == 0) {
    expression = Expression::sad;
  } else if (std::strcmp(value, "joy") == 0) {
    expression = Expression::joy;
  } else if (std::strcmp(value, "rude") == 0) {
    expression = Expression::rude;
  } else if (std::strcmp(value, "tasa-tokimi") == 0) {
    expression = Expression::tasaTokimi;
  } else if (std::strcmp(value, "tasa-astronaut") == 0) {
    expression = Expression::tasaAstronaut;
  } else if (std::strcmp(value, "sos") == 0) {
    expression = Expression::sos;
  } else if (std::strcmp(value, "dashboard") != 0) {
    return;
  }

  activeExpression = expression;
  expressionStartedMs = millis();
  lastExpressionFrameMs = 0;
  expressionDirty = true;
  lastMotionActivityMs = expressionStartedMs;
  lastSleepFrameMs = 0;
  faceDirty = true;
}

void setMotion(const char* value) {
  Motion motion = Motion::stopped;
  if (std::strcmp(value, "forward") == 0) {
    motion = Motion::forward;
  } else if (std::strcmp(value, "backward") == 0) {
    motion = Motion::backward;
  } else if (std::strcmp(value, "left") == 0) {
    motion = Motion::left;
  } else if (std::strcmp(value, "right") == 0) {
    motion = Motion::right;
  } else if (std::strcmp(value, "forward-left") == 0) {
    motion = Motion::forwardLeft;
  } else if (std::strcmp(value, "forward-right") == 0) {
    motion = Motion::forwardRight;
  } else if (std::strcmp(value, "backward-left") == 0) {
    motion = Motion::backwardLeft;
  } else if (std::strcmp(value, "backward-right") == 0) {
    motion = Motion::backwardRight;
  } else if (std::strcmp(value, "stopped") != 0 &&
             std::strcmp(value, "stop") != 0) {
    return;
  }

  const std::uint32_t now = millis();
  if (motion != Motion::stopped) {
    lastMotionActivityMs = now;
  }

  if (motion == activeMotion) {
    return;
  }

  activeMotion = motion;
  faceDirty = true;
  blinkActive = false;
  lastSleepFrameMs = 0;
  lastMotionFrameMs = 0;

  if (motion == Motion::stopped) {
    lastMotionActivityMs = now;
    targetPupilX = 0;
    targetPupilY = 0;
    scheduleBlink(now);
    schedulePupilTarget(now);
  }
}

void storeStatus(const char* name, const char* value) {
  if (name == nullptr || value == nullptr) {
    return;
  }

  if (std::strcmp(name, "Expression") == 0) {
    setExpression(value);
  } else if (std::strcmp(name, "Motion") == 0) {
    setMotion(value);
  } else if (std::strcmp(name, "Motor") == 0) {
    copyStatus(motorStatus, sizeof(motorStatus), value);
  } else if (std::strcmp(name, "Camera") == 0) {
    copyStatus(cameraStatus, sizeof(cameraStatus), value);
  } else {
    for (ExtraStatus& status : extraStatuses) {
      if (status.active && std::strcmp(status.name, name) == 0) {
        copyStatus(status.value, sizeof(status.value), value);
        return;
      }
    }

    for (ExtraStatus& status : extraStatuses) {
      if (!status.active) {
        copyStatus(status.name, sizeof(status.name), name);
        copyStatus(status.value, sizeof(status.value), value);
        status.active = true;
        return;
      }
    }
  }
}

}  // namespace

void display_init() {
  Serial.println("OLED init...");
  Serial.println("Wire.begin(8,3)");
  Wire.begin(kSdaPin, kSclPin);

  Serial.println("Scanning I2C...");
  std::uint8_t detectedCount = 0;
  std::uint8_t oledAddress = 0;

  for (std::uint8_t address = kFirstI2cAddress;
       address <= kLastI2cAddress; ++address) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) {
      ++detectedCount;
      Serial.printf("Found 0x%02X\n", address);
      if (address == kOledAddressA || address == kOledAddressB) {
        oledAddress = address;
      }
    }
  }

  if (detectedCount == 0) {
    Serial.println("OLED ERROR: no I2C devices detected");
    return;
  }

  if (oledAddress == 0) {
    Serial.println("OLED ERROR: SH1106 not found at 0x3C or 0x3D");
    return;
  }

  Wire.end();
  Serial.println("Initializing SH1106...");
  oled.setI2CAddress(static_cast<std::uint8_t>(oledAddress << 1U));
  oled.setBusClock(100000U);
  Serial.println("U8g2 init at 100kHz...");
  oled.initDisplay();
  Serial.println("SH1106 initialized; clearing display...");
  oled.clearDisplay();
  Serial.println("SH1106 cleared; enabling display...");
  oled.setPowerSave(0);
  drawSplash();

  oledReady = true;
  splashStartedMs = millis();
  lastMotionActivityMs = splashStartedMs;
  lastPupilStepMs = splashStartedMs;
  scheduleBlink(splashStartedMs);
  schedulePupilTarget(splashStartedMs);
  faceDirty = true;
  Serial.println("OLED Ready");
}

void display_update(const char* statusName, const char* statusValue) {
  storeStatus(statusName, statusValue);

  if (!oledReady) {
    return;
  }

  const std::uint32_t now = millis();
  if (now - splashStartedMs < kSplashDurationMs) {
    return;
  }

  if (activeExpression != Expression::dashboard) {
    const std::uint32_t duration = activeExpression == Expression::sos
                                       ? kSosDurationMs
                                       : kExpressionDurationMs;
    if (now - expressionStartedMs >= duration) {
      activeExpression = Expression::dashboard;
      expressionDirty = false;
      faceDirty = true;
      updateDefaultFace(now);
      return;
    }

    const bool animatedFrameDue =
        activeExpression == Expression::sos &&
        now - lastExpressionFrameMs >= kSosFrameIntervalMs;
    if (expressionDirty || animatedFrameDue) {
      expressionDirty = false;
      lastExpressionFrameMs = now;
      drawExpression(activeExpression, now);
    }
    return;
  }

  if (expressionDirty) {
    expressionDirty = false;
    faceDirty = true;
  }

  updateDefaultFace(now);
}
