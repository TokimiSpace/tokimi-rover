# Project Context

## Hardware

- Board: ESP32-S3-WROOM-1-N16R8
- MCU: ESP32-S3
- Framework: Arduino
- IDE: PlatformIO
- OS: macOS
- Motor Driver: TB6612FNG
- Motors: 4 TT DC Motors
- Power: 2x18650 battery pack
- Chassis: 4WD smart car
- Test equipment: Digital multimeter

## Development Style

- Use PlatformIO and clean C++17.
- Keep configuration separate from application logic.
- Make small, incremental changes.
- Complete and verify one task at a time.
- Verify hardware before wiring or powering it.
- Explain each GPIO assignment and wiring change.
- Inspect hardware identity only when troubleshooting requires it.

## Roadmap

1. Verify the ESP32-S3, built-in LED, and Serial Monitor.
2. Read GPIO using an external LED and push button.
3. Connect the TB6612FNG and drive one motor.
4. Drive two motor channels.
5. Assemble the 4WD chassis.
6. Drive the complete 4WD car with PWM and emergency stop.
7. Add a simple Wi-Fi control web page.

Advanced AI, camera, ROS, MQTT, and OTA features are outside the current scope.
