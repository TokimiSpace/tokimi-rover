// SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
// SPDX-License-Identifier: Apache-2.0

#pragma once

// Commands are optional. Supported future states are READY, SEARCH, RECOVER,
// and ERROR. Zone controls use TOGGLE_ALL, TOGGLE_FRONT, TOGGLE_CENTER, and
// TOGGLE_REAR.
void lighting_init();
void lighting_update(const char* command = nullptr);
