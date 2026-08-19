// SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstdint>

#if __has_include("local_config.h")
#include "local_config.h"
#define TOKIMI_ROVER_LOCAL_CONFIG_PRESENT 1
#else
#error "Missing include/local_config.h. Copy include/local_config.example.h to include/local_config.h, then set unique Wi-Fi credentials before building."
#define TOKIMI_ROVER_AP_SSID ""
#define TOKIMI_ROVER_AP_PASSWORD ""
#endif

#ifndef TOKIMI_ROVER_AP_SSID
#error "TOKIMI_ROVER_AP_SSID must be defined in include/local_config.h."
#define TOKIMI_ROVER_AP_SSID ""
#define TOKIMI_ROVER_LOCAL_CONFIG_INVALID 1
#endif

#ifndef TOKIMI_ROVER_AP_PASSWORD
#error "TOKIMI_ROVER_AP_PASSWORD must be defined in include/local_config.h."
#define TOKIMI_ROVER_AP_PASSWORD ""
#define TOKIMI_ROVER_LOCAL_CONFIG_INVALID 1
#endif

namespace config {

constexpr std::uint32_t serialBaud = 115200;
constexpr std::uint8_t motorPwmPin = 5;
constexpr std::uint8_t motorIn1Pin = 6;
constexpr std::uint8_t motorIn2Pin = 7;
constexpr std::uint8_t motorStandbyPin = 15;
constexpr std::uint8_t motorPwmChannel = 0;
constexpr std::uint8_t motorBPwmPin = 16;
constexpr std::uint8_t motorBIn1Pin = 17;
constexpr std::uint8_t motorBIn2Pin = 18;
constexpr std::uint8_t motorBPwmChannel = 1;
constexpr std::uint32_t motorPwmFrequencyHz = 20000;
constexpr std::uint8_t motorPwmResolutionBits = 8;
constexpr std::uint8_t motorPwmSafetyCapPercent = 80;
constexpr std::uint8_t defaultSpeedPercent = 30;
constexpr std::uint32_t motorCommandTimeoutMs = 750;
constexpr char apSsid[] = TOKIMI_ROVER_AP_SSID;
constexpr char apPassword[] = TOKIMI_ROVER_AP_PASSWORD;

#if defined(TOKIMI_ROVER_LOCAL_CONFIG_PRESENT) && \
    !defined(TOKIMI_ROVER_LOCAL_CONFIG_INVALID)
static_assert(sizeof(apSsid) > 1 && sizeof(apSsid) <= 33,
              "Wi-Fi AP SSID must contain 1 to 32 bytes.");
static_assert(sizeof(apPassword) >= 9 && sizeof(apPassword) <= 64,
              "Wi-Fi AP password must contain 8 to 63 bytes.");
#endif

}  // namespace config

#undef TOKIMI_ROVER_LOCAL_CONFIG_PRESENT
#undef TOKIMI_ROVER_LOCAL_CONFIG_INVALID
