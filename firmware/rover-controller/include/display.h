// SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
// SPDX-License-Identifier: Apache-2.0

#pragma once

// Passing a name and value is optional. Statuses are cached and rotated through
// the dashboard footer, keeping subsystems independent from the OLED, for example:
// display_update("Camera", "ONLINE");
// display_update("Expression", "happy");
// display_update("Motion", "forward-left");
void display_init();
void display_update(const char* statusName = nullptr,
                    const char* statusValue = nullptr);
