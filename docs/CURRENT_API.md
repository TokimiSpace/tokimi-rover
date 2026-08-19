# Current HTTP API

> Audit date: 2026-08-19<br>
> Status: `CODE-CONFIRMED`<br>
> Security: HTTP only; no TLS, session, token, or application authentication

The rover and camera are separate servers on separate Wi-Fi access points. Replace the example host with the address printed by each device's serial log or configured in its local, ignored configuration file. Do not publish deployment credentials.

## Rover controller API

The rover uses Arduino `WebServer` on TCP port 80. In the normal AP configuration, its serial log prints the Web UI address.

### Route summary

| Method | Path | Query parameter | Success |
|---|---|---|---|
| `GET` | `/` | — | `200 text/html`; embedded control page |
| `POST` | `/api/command` | `value` | `200 text/plain`; movement result |
| `POST` | `/api/speed` | `value` | `200 text/plain`; requested speed and physical cap |
| `POST` | `/api/led` | `state` | `200 text/plain`; lighting command accepted |
| `POST` | `/api/expression` | `value` | `200 text/plain`; OLED expression accepted |

Any unhandled route or method reaches the not-found handler, invokes a full motor stop, and returns `404 text/plain` with `not found`.

### Movement command

```http
POST /api/command?value=<command>
```

Accepted values:

| Value | Motor state |
|---|---|
| `forward` | Both sides forward |
| `backward` | Both sides backward |
| `left` | Pivot left |
| `right` | Pivot right |
| `forward-left` | Forward arc; Motor A uses 40% inner duty |
| `forward-right` | Forward arc; Motor B uses 40% inner duty |
| `backward-left` | Reverse arc; Motor A uses 40% inner duty |
| `backward-right` | Reverse arc; Motor B uses 40% inner duty |
| `stop` | Both PWM duties zero, direction pins LOW, STBY LOW |

Missing `value` returns `400 missing command`; an unknown value returns `400 invalid command`. Both error paths stop the rover.

Example against an already joined rover AP:

```sh
curl -X POST 'http://192.168.4.1/api/command?value=stop'
```

Do not use a scripted movement example unless the rover is safely supported with its wheels clear and motor power can be disconnected immediately.

### Requested speed

```http
POST /api/speed?value=<0..100>
```

- Input is a base-10 integer from 0 through 100.
- The input is requested percentage, scaled inside the current **80% physical PWM cap**.
- `100` therefore means duty `204/255`, not unrestricted output.
- Value `0` stops the rover.
- Missing or invalid values return 400 and stop the rover.
- Due to the current `strtol` validation, an empty value is accepted as zero, returns 200, and stops the rover.
- A speed change while moving updates both PWM duties and refreshes the watchdog timestamp.

Example response:

```text
speed=30% (80% cap)
```

### Lighting

```http
POST /api/led?state=<state>
```

Accepted values are `toggle-all`, `toggle-front`, `toggle-center`, and `toggle-rear`.

This is a toggle API, not an idempotent `on`/`off` API, and there is no readback/status route. Missing or invalid lighting input returns 400 **without stopping the motors**. Internal `SEARCH`, `RECOVER`, and `ERROR` scenes are not exposed by this API.

### OLED expression

```http
POST /api/expression?value=<expression>
```

Accepted values:

- `happy`
- `angry`
- `sad`
- `joy`
- `rude`
- `tasa-tokimi`
- `tasa-astronaut`
- `sos`
- `dashboard`

Most expressions last six seconds; `sos` lasts ten seconds. `dashboard` only returns to the animated default face—the dormant text dashboard is not rendered. Missing or invalid expression input returns 400 **without stopping the motors**.

### Browser heartbeat behavior

The embedded page sends a movement request at pointer-down and every 250 ms while held. Pointer-up/cancel, page hide, or window blur sends STOP. Requests are not serialized or cancelled; an earlier movement request may complete after STOP and resume motion. The firmware watchdog threshold is 750 ms but is checked in the main loop and is not a hard deadline. See [Safety](SAFETY.md).

## Camera node API

The camera uses a custom `WiFiServer` on TCP port 80. Its local configuration defines AP name, channel, client limit, and IPv4 network. The safe example configuration uses `192.168.4.1/24`; deployments may differ.

Only `GET` is accepted. A parse failure returns `400 application/json`; any non-GET request returns `405 application/json`; an unknown GET path returns `404 application/json`.

### Route summary

| Method | Path | Success | Important errors/side effects |
|---|---|---|---|
| `GET` | `/` | `200 text/html`; camera UI | — |
| `GET` | `/capture` | `200 image/jpeg` | 503 if camera offline or acquisition fails |
| `GET` | `/stream` | `200 multipart/x-mixed-replace` | 503 if camera offline or another stream is active |
| `GET` | `/status` | `200 application/json` | Can contain stale health/stream state |
| `GET` | `/restart` | `200 application/json`, then reboot | Unauthenticated, state-changing GET |

The server allows up to six concurrent HTTP client tasks. A request beyond that limit returns `503` with `{"error":"HTTP connection limit reached"}`.

### JPEG snapshot

```http
GET /capture
```

The successful response is an inline JPEG named `tokimi-camera.jpg`, with cache disabled. The handler passes a nominal 250 ms timeout, but the current camera function ignores that value and attempts one immediate frame acquisition.

```sh
curl --fail --output tokimi-camera.jpg 'http://192.168.4.1/capture'
```

### MJPEG stream

```http
GET /stream
```

- Media type is `multipart/x-mixed-replace` with boundary `tokimi-boundary`.
- The target pacing rate is 10 FPS.
- Only one stream may be active.
- With PSRAM, capture uses two buffers; without PSRAM, it uses one DRAM buffer. Snapshot availability during the one-buffer stream is not guaranteed.
- The raw stream is not mirrored. Mirroring occurs only in the bundled browser page's CSS.

### Status JSON

```http
GET /status
```

Current fields:

| Field | Type | Meaning/limitation |
|---|---|---|
| `camera` | string | `online` after successful boot initialization; not cleared on later capture failures |
| `sensor` | string | Currently hardcoded `OV3660`, including offline state |
| `resolution` | string | Configured `480x320` |
| `fps` | number | Target FPS, currently 10 |
| `actual_fps` | number | Most recently calculated stream FPS; zeroed when stream ends |
| `avg_frame_ms` | number | Recent streamed-frame average |
| `avg_capture_ms` | number | Recent capture average |
| `avg_jpeg_bytes` | number | Recent streamed JPEG-size average |
| `heap` | number | Free heap bytes |
| `psram` | boolean | Whether PSRAM was detected |
| `psram_free` | number | Free PSRAM bytes |
| `uptime` | number | `millis()` value in milliseconds |
| `rssi` | number | Instantaneous RSSI of the first associated client, or −127 when unavailable |
| `channel` | number | Current AP channel |
| `phy` | string | First associated client's PHY label or fallback state |
| `protocol` | string | Enabled AP protocol set |
| `bandwidth_mhz` | number | AP bandwidth, configured as 20 |
| `tx_power_dbm` | number | Reported configured maximum TX power |
| `power_save` | boolean | Whether Wi-Fi power save is active |
| `ip` | string | Current camera AP address |
| `ap` | string | Configured camera AP name |

This endpoint reports firmware state, not a hardware health guarantee. In particular, `camera: online` can become stale after runtime capture failure.

### Restart

```http
GET /restart
```

Successful response:

```json
{"restarting":true}
```

The device flushes the response, waits approximately 150 ms, and calls `ESP.restart()`. There is no authentication or CSRF protection. Treat exposure of the camera AP as exposure of a remote reboot control.

## Compatibility policy

V0.1 route names and parameters are considered public prototype interfaces. Changes to methods, paths, accepted values, or response fields should be documented and deliberately versioned. Safety fixes may require changed request sequencing or authorization; do not preserve unsafe behavior merely for compatibility.
