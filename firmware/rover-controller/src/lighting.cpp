// SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
// SPDX-License-Identifier: Apache-2.0

#include "lighting.h"

#include <Arduino.h>
#include <FastLED.h>

#include <cstring>

#define LED_PIN 4
#define NUM_LEDS 32

namespace {

constexpr std::uint8_t kBrightness = 40;
constexpr std::uint8_t kFrontFirst = 0;
constexpr std::uint8_t kFrontLast = 7;
constexpr std::uint8_t kCenterFirst = 8;
constexpr std::uint8_t kCenterLast = 23;
constexpr std::uint8_t kRearFirst = 24;
constexpr std::uint8_t kRearLast = 31;
constexpr std::uint32_t kDiagnosticStepMs = 500;
constexpr std::uint32_t kFrameIntervalMs = 33;

CRGB leds[NUM_LEDS];

enum class DiagnosticStep {
  red,
  green,
  blue,
  white,
  off,
  complete,
};

enum class LightingState {
  ready,
  search,
  recover,
  error,
};

DiagnosticStep diagnosticStep = DiagnosticStep::red;
LightingState lightingState = LightingState::ready;
std::uint32_t diagnosticStepStartedMs = 0;
std::uint32_t lastFrameMs = 0;
bool masterEnabled = true;
bool frontEnabled = true;
bool centerEnabled = true;
bool rearEnabled = true;
bool forceRender = true;

void fillZone(std::uint8_t first, std::uint8_t last, const CRGB& color) {
  for (std::uint8_t index = first; index <= last; ++index) {
    leds[index] = color;
  }
}

void applyZoneMask() {
  if (!masterEnabled) {
    FastLED.clear();
    return;
  }

  if (!frontEnabled) {
    fillZone(kFrontFirst, kFrontLast, CRGB::Black);
  }
  if (!centerEnabled) {
    fillZone(kCenterFirst, kCenterLast, CRGB::Black);
  }
  if (!rearEnabled) {
    fillZone(kRearFirst, kRearLast, CRGB::Black);
  }
}

void renderReady(std::uint32_t now) {
  FastLED.clear();
  fillZone(kFrontFirst, kFrontLast, CRGB::White);

  const std::uint8_t breath =
      35U + scale8(sin8(static_cast<std::uint8_t>(now / 8U)), 220U);
  fillZone(kCenterFirst, kCenterLast, CRGB(0, 0, breath));
  fillZone(kRearFirst, kRearLast, CRGB::Red);
}

void renderSearch(std::uint32_t now) {
  FastLED.clear();
  fillZone(kFrontFirst, kFrontLast, CRGB::White);
  fillZone(kCenterFirst, kCenterLast, CRGB(0, 0, 20));
  const std::uint8_t position =
      kCenterFirst + (now / 90U) % (kCenterLast - kCenterFirst + 1U);
  leds[position] = CRGB::Blue;
  fillZone(kRearFirst, kRearLast, CRGB::Red);
}

void renderRecover(std::uint32_t now) {
  FastLED.clear();
  const std::uint8_t pulse =
      30U + scale8(sin8(static_cast<std::uint8_t>(now / 4U)), 225U);
  fillZone(kFrontFirst, kFrontLast, CRGB::White);
  fillZone(kCenterFirst, kCenterLast, CRGB(pulse, pulse / 3U, 0));
  fillZone(kRearFirst, kRearLast, CRGB(pulse, pulse / 4U, 0));
}

void renderError(std::uint32_t now) {
  FastLED.clear();
  if ((now / 500U) % 2U == 0U) {
    fill_solid(leds, NUM_LEDS, CRGB::Red);
  }
}

void renderLighting(std::uint32_t now) {
  switch (lightingState) {
    case LightingState::search:
      renderSearch(now);
      break;
    case LightingState::recover:
      renderRecover(now);
      break;
    case LightingState::error:
      renderError(now);
      break;
    case LightingState::ready:
    default:
      renderReady(now);
      break;
  }

  applyZoneMask();
  FastLED.show();
}

void showDiagnosticStep(DiagnosticStep step) {
  switch (step) {
    case DiagnosticStep::red:
      fill_solid(leds, NUM_LEDS, CRGB::Red);
      break;
    case DiagnosticStep::green:
      fill_solid(leds, NUM_LEDS, CRGB::Green);
      break;
    case DiagnosticStep::blue:
      fill_solid(leds, NUM_LEDS, CRGB::Blue);
      break;
    case DiagnosticStep::white:
      fill_solid(leds, NUM_LEDS, CRGB::White);
      break;
    case DiagnosticStep::off:
      FastLED.clear();
      break;
    case DiagnosticStep::complete:
      forceRender = true;
      return;
  }

  FastLED.show();
}

void advanceDiagnostic(std::uint32_t now) {
  switch (diagnosticStep) {
    case DiagnosticStep::red:
      diagnosticStep = DiagnosticStep::green;
      break;
    case DiagnosticStep::green:
      diagnosticStep = DiagnosticStep::blue;
      break;
    case DiagnosticStep::blue:
      diagnosticStep = DiagnosticStep::white;
      break;
    case DiagnosticStep::white:
      diagnosticStep = DiagnosticStep::off;
      break;
    case DiagnosticStep::off:
      diagnosticStep = DiagnosticStep::complete;
      break;
    case DiagnosticStep::complete:
      return;
  }

  diagnosticStepStartedMs = now;
  showDiagnosticStep(diagnosticStep);
}

void toggleZone(bool& zoneEnabled) {
  zoneEnabled = !zoneEnabled;

  if (zoneEnabled) {
    masterEnabled = true;
  } else if (!frontEnabled && !centerEnabled && !rearEnabled) {
    masterEnabled = false;
  }
}

void applyCommand(const char* command) {
  if (command == nullptr) {
    return;
  }

  if (std::strcmp(command, "READY") == 0) {
    lightingState = LightingState::ready;
  } else if (std::strcmp(command, "SEARCH") == 0) {
    lightingState = LightingState::search;
  } else if (std::strcmp(command, "RECOVER") == 0) {
    lightingState = LightingState::recover;
  } else if (std::strcmp(command, "ERROR") == 0) {
    lightingState = LightingState::error;
  } else if (std::strcmp(command, "TOGGLE_ALL") == 0) {
    const bool enableAll = !masterEnabled;
    masterEnabled = enableAll;
    frontEnabled = enableAll;
    centerEnabled = enableAll;
    rearEnabled = enableAll;
  } else if (std::strcmp(command, "TOGGLE_FRONT") == 0) {
    toggleZone(frontEnabled);
  } else if (std::strcmp(command, "TOGGLE_CENTER") == 0) {
    toggleZone(centerEnabled);
  } else if (std::strcmp(command, "TOGGLE_REAR") == 0) {
    toggleZone(rearEnabled);
  } else if (std::strcmp(command, "ON") == 0) {
    masterEnabled = true;
    frontEnabled = true;
    centerEnabled = true;
    rearEnabled = true;
  } else if (std::strcmp(command, "OFF") == 0) {
    masterEnabled = false;
    frontEnabled = false;
    centerEnabled = false;
    rearEnabled = false;
  } else {
    return;
  }

  forceRender = true;
  Serial.printf("lighting command=%s\n", command);
}

}  // namespace

void lighting_init() {
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(kBrightness);
  FastLED.clear();

  Serial.println("FastLED initialized");
  Serial.println("GPIO4 OK");
  Serial.printf("LED Count = %u\n", NUM_LEDS);
  Serial.printf("Brightness = %u\n", kBrightness);

  diagnosticStep = DiagnosticStep::red;
  diagnosticStepStartedMs = millis();
  showDiagnosticStep(diagnosticStep);
}

void lighting_update(const char* command) {
  applyCommand(command);

  const std::uint32_t now = millis();
  if (diagnosticStep != DiagnosticStep::complete) {
    if (now - diagnosticStepStartedMs >= kDiagnosticStepMs) {
      advanceDiagnostic(now);
    }
    return;
  }

  if (!forceRender && !masterEnabled) {
    return;
  }

  if (!forceRender && now - lastFrameMs < kFrameIntervalMs) {
    return;
  }

  forceRender = false;
  lastFrameMs = now;
  renderLighting(now);
}
