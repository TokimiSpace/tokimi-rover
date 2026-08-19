// SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
// SPDX-License-Identifier: Apache-2.0

#include <Arduino.h>
#include <WebServer.h>
#include <WiFi.h>

#include "config.h"
#include "display.h"
#include "lighting.h"
#include "web_page.h"

namespace {

WebServer server(80);

enum class MotorState {
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

MotorState motorState = MotorState::stopped;
std::uint8_t requestedSpeedPercent = config::defaultSpeedPercent;
std::uint32_t lastMotorCommandMs = 0;

const char* motorStateName(MotorState state) {
  switch (state) {
    case MotorState::forward:
      return "forward";
    case MotorState::backward:
      return "backward";
    case MotorState::left:
      return "left";
    case MotorState::right:
      return "right";
    case MotorState::forwardLeft:
      return "forward-left";
    case MotorState::forwardRight:
      return "forward-right";
    case MotorState::backwardLeft:
      return "backward-left";
    case MotorState::backwardRight:
      return "backward-right";
    case MotorState::stopped:
    default:
      return "stopped";
  }
}

std::uint8_t motorDuty() {
  const std::uint16_t maximumDuty =
      ((1U << config::motorPwmResolutionBits) - 1U) *
      config::motorPwmSafetyCapPercent / 100U;
  return static_cast<std::uint8_t>(
      maximumDuty * requestedSpeedPercent / 100U);
}

std::uint8_t innerMotorDuty() {
  return static_cast<std::uint8_t>(motorDuty() * 40U / 100U);
}

void motorDuties(MotorState direction, std::uint8_t& motorADuty,
                 std::uint8_t& motorBDuty) {
  motorADuty = motorDuty();
  motorBDuty = motorDuty();
  if (direction == MotorState::forwardLeft ||
      direction == MotorState::backwardLeft) {
    motorADuty = innerMotorDuty();
  } else if (direction == MotorState::forwardRight ||
             direction == MotorState::backwardRight) {
    motorBDuty = innerMotorDuty();
  }
}

void setMotorOutputsStopped() {
  ledcWrite(config::motorPwmChannel, 0);
  ledcWrite(config::motorBPwmChannel, 0);
  digitalWrite(config::motorIn1Pin, LOW);
  digitalWrite(config::motorIn2Pin, LOW);
  digitalWrite(config::motorBIn1Pin, LOW);
  digitalWrite(config::motorBIn2Pin, LOW);
  digitalWrite(config::motorStandbyPin, LOW);
}

void stopMotor(const char* reason) {
  setMotorOutputsStopped();
  motorState = MotorState::stopped;
  Serial.printf(
      "drive=stopped reason=%s requested-speed=%u%% PWMA=0 PWMB=0 "
      "AIN1=0 AIN2=0 BIN1=0 BIN2=0 STBY=0\n",
      reason, requestedSpeedPercent);
}

void driveMotor(MotorState direction) {
  setMotorOutputsStopped();

  if (requestedSpeedPercent == 0) {
    stopMotor("speed-zero");
    return;
  }

  const bool forwardArc = direction == MotorState::forwardLeft ||
                          direction == MotorState::forwardRight;
  const bool backwardArc = direction == MotorState::backwardLeft ||
                           direction == MotorState::backwardRight;
  const bool motorAForward = direction == MotorState::forward ||
                             direction == MotorState::right || forwardArc;
  const bool motorABackward = direction == MotorState::backward ||
                              direction == MotorState::left || backwardArc;
  const bool motorBForward = direction == MotorState::forward ||
                             direction == MotorState::left || forwardArc;
  const bool motorBBackward = direction == MotorState::backward ||
                              direction == MotorState::right || backwardArc;

  std::uint8_t motorADuty = 0;
  std::uint8_t motorBDuty = 0;
  motorDuties(direction, motorADuty, motorBDuty);

  digitalWrite(config::motorIn1Pin, motorAForward ? HIGH : LOW);
  digitalWrite(config::motorIn2Pin, motorABackward ? HIGH : LOW);
  digitalWrite(config::motorBIn1Pin, motorBForward ? HIGH : LOW);
  digitalWrite(config::motorBIn2Pin, motorBBackward ? HIGH : LOW);

  digitalWrite(config::motorStandbyPin, HIGH);
  ledcWrite(config::motorPwmChannel, motorADuty);
  ledcWrite(config::motorBPwmChannel, motorBDuty);
  motorState = direction;
  lastMotorCommandMs = millis();
  Serial.printf(
      "drive=%s requested-speed=%u%% physical-cap=%u%% "
      "PWMA=%u/255 PWMB=%u/255 AIN1=%u AIN2=%u BIN1=%u BIN2=%u STBY=1\n",
      motorStateName(motorState), requestedSpeedPercent,
      config::motorPwmSafetyCapPercent, motorADuty, motorBDuty,
      motorAForward ? 1U : 0U, motorABackward ? 1U : 0U,
      motorBForward ? 1U : 0U, motorBBackward ? 1U : 0U);
}

bool isValidCommand(const String& command) {
  return command == "forward" || command == "backward" ||
         command == "left" || command == "right" ||
         command == "forward-left" || command == "forward-right" ||
         command == "backward-left" || command == "backward-right" ||
         command == "stop";
}

bool isValidExpression(const String& expression) {
  return expression == "sos" || expression == "happy" ||
         expression == "angry" || expression == "sad" ||
         expression == "joy" || expression == "rude" ||
         expression == "tasa-tokimi" ||
         expression == "tasa-astronaut" ||
         expression == "dashboard";
}

void handleRoot() {
  server.send(200, "text/html", web::controlPage);
}

void handleCommand() {
  if (!server.hasArg("value")) {
    stopMotor("missing-command");
    server.send(400, "text/plain", "missing command");
    return;
  }

  const String command = server.arg("value");
  if (!isValidCommand(command)) {
    stopMotor("invalid-command");
    server.send(400, "text/plain", "invalid command");
    return;
  }

  Serial.printf("command=%s\n", command.c_str());

  if (command == "forward") {
    driveMotor(MotorState::forward);
    server.send(200, "text/plain", "Robot forward");
    return;
  }

  if (command == "backward") {
    driveMotor(MotorState::backward);
    server.send(200, "text/plain", "Robot backward");
    return;
  }

  if (command == "stop") {
    stopMotor("web-stop");
    server.send(200, "text/plain", "Robot stopped");
    return;
  }

  if (command == "left") {
    driveMotor(MotorState::left);
    server.send(200, "text/plain", "Robot turning left");
    return;
  }


  if (command == "forward-left") {
    driveMotor(MotorState::forwardLeft);
    server.send(200, "text/plain", "Robot forward-left");
    return;
  }

  if (command == "forward-right") {
    driveMotor(MotorState::forwardRight);
    server.send(200, "text/plain", "Robot forward-right");
    return;
  }

  if (command == "backward-left") {
    driveMotor(MotorState::backwardLeft);
    server.send(200, "text/plain", "Robot backward-left");
    return;
  }

  if (command == "backward-right") {
    driveMotor(MotorState::backwardRight);
    server.send(200, "text/plain", "Robot backward-right");
    return;
  }

  driveMotor(MotorState::right);
  server.send(200, "text/plain", "Robot turning right");
}

void handleSpeed() {
  if (!server.hasArg("value")) {
    stopMotor("missing-speed");
    server.send(400, "text/plain", "missing speed");
    return;
  }

  const String value = server.arg("value");
  char* end = nullptr;
  const long speed = strtol(value.c_str(), &end, 10);

  if (*end != '\0' || speed < 0 || speed > 100) {
    stopMotor("invalid-speed");
    server.send(400, "text/plain", "invalid speed");
    return;
  }

  requestedSpeedPercent = static_cast<std::uint8_t>(speed);
  Serial.printf("speed=%u%% safety-cap=%u%%\n", requestedSpeedPercent,
                config::motorPwmSafetyCapPercent);

  if (requestedSpeedPercent == 0) {
    stopMotor("speed-zero");
  } else if (motorState != MotorState::stopped) {
    std::uint8_t motorADuty = 0;
    std::uint8_t motorBDuty = 0;
    motorDuties(motorState, motorADuty, motorBDuty);
    ledcWrite(config::motorPwmChannel, motorADuty);
    ledcWrite(config::motorBPwmChannel, motorBDuty);
    lastMotorCommandMs = millis();
    Serial.printf(
        "drive=%s speed-update PWMA=%u/255 PWMB=%u/255 STBY=1\n",
        motorStateName(motorState), motorADuty, motorBDuty);
  }

  server.send(200, "text/plain",
              "speed=" + String(requestedSpeedPercent) + "% (" +
                  String(config::motorPwmSafetyCapPercent) + "% cap)");
}

void handleLed() {
  if (!server.hasArg("state")) {
    server.send(400, "text/plain", "missing lighting command");
    return;
  }

  const String state = server.arg("state");
  const char* command = nullptr;
  if (state == "toggle-all") {
    command = "TOGGLE_ALL";
  } else if (state == "toggle-front") {
    command = "TOGGLE_FRONT";
  } else if (state == "toggle-center") {
    command = "TOGGLE_CENTER";
  } else if (state == "toggle-rear") {
    command = "TOGGLE_REAR";
  } else {
    server.send(400, "text/plain", "invalid lighting command");
    return;
  }

  lighting_update(command);
  server.send(200, "text/plain", "Lighting: " + state);
}

void handleExpression() {
  if (!server.hasArg("value")) {
    server.send(400, "text/plain", "missing expression");
    return;
  }

  const String expression = server.arg("value");
  if (!isValidExpression(expression)) {
    server.send(400, "text/plain", "invalid expression");
    return;
  }

  display_update("Expression", expression.c_str());
  Serial.printf("oled-expression=%s\n", expression.c_str());
  server.send(200, "text/plain", "OLED expression: " + expression);
}

void handleNotFound() {
  stopMotor("not-found");
  server.send(404, "text/plain", "not found");
}

}  // namespace

void setup() {
  Serial.begin(config::serialBaud);

  pinMode(config::motorPwmPin, OUTPUT);
  pinMode(config::motorIn1Pin, OUTPUT);
  pinMode(config::motorIn2Pin, OUTPUT);
  pinMode(config::motorBPwmPin, OUTPUT);
  pinMode(config::motorBIn1Pin, OUTPUT);
  pinMode(config::motorBIn2Pin, OUTPUT);
  pinMode(config::motorStandbyPin, OUTPUT);
  digitalWrite(config::motorIn1Pin, LOW);
  digitalWrite(config::motorIn2Pin, LOW);
  digitalWrite(config::motorBIn1Pin, LOW);
  digitalWrite(config::motorBIn2Pin, LOW);
  digitalWrite(config::motorStandbyPin, LOW);
  ledcSetup(config::motorPwmChannel, config::motorPwmFrequencyHz,
            config::motorPwmResolutionBits);
  ledcAttachPin(config::motorPwmPin, config::motorPwmChannel);
  ledcSetup(config::motorBPwmChannel, config::motorPwmFrequencyHz,
            config::motorPwmResolutionBits);
  ledcAttachPin(config::motorBPwmPin, config::motorBPwmChannel);
  stopMotor("boot");
  lighting_init();
  display_init();

  const std::uint32_t startupPauseStartedMs = millis();
  while (millis() - startupPauseStartedMs < 1000U) {
    lighting_update();
    delay(2);
  }

  Serial.println(
      "GPIO4=WS2812B GPIO5=PWMA GPIO6=AIN1 GPIO7=AIN2 GPIO15=STBY "
      "GPIO16=PWMB GPIO17=BIN1 GPIO18=BIN2");
  Serial.printf("PWM=%luHz resolution=%ubit safety-cap=%u%% timeout=%lums\n",
                config::motorPwmFrequencyHz,
                config::motorPwmResolutionBits,
                config::motorPwmSafetyCapPercent,
                config::motorCommandTimeoutMs);

  Serial.println("starting Wi-Fi access point");
  if (!WiFi.softAP(config::apSsid, config::apPassword)) {
    Serial.println("failed to start access point");
    stopMotor("wifi-start-failed");
    return;
  }

  server.on("/", HTTP_GET, handleRoot);
  server.on("/api/command", HTTP_POST, handleCommand);
  server.on("/api/speed", HTTP_POST, handleSpeed);
  server.on("/api/led", HTTP_POST, handleLed);
  server.on("/api/expression", HTTP_POST, handleExpression);
  server.onNotFound(handleNotFound);
  server.begin();

  Serial.printf("SSID: %s\n", config::apSsid);
  Serial.printf("Web UI: http://%s\n", WiFi.softAPIP().toString().c_str());
  Serial.println("motor ready; waiting in STOP");
}

void loop() {
  server.handleClient();

  if (motorState != MotorState::stopped &&
      WiFi.softAPgetStationNum() == 0) {
    Serial.println("event=wifi-client-loss action=stop");
    stopMotor("no-wifi-client");
  }

  if (motorState != MotorState::stopped &&
      millis() - lastMotorCommandMs > config::motorCommandTimeoutMs) {
    Serial.println("event=watchdog-timeout action=stop");
    stopMotor("command-timeout");
  }

  lighting_update();
  display_update("Motion", motorStateName(motorState));
  delay(2);
}
