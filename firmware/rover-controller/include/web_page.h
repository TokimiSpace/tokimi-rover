// SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
// SPDX-License-Identifier: Apache-2.0

#pragma once

namespace web {

constexpr char controlPage[] = R"HTML(
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>4WD Robot Control</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    html,
    body {
      width: 100%;
      height: 100%;
      overflow: hidden;
    }

    body {
      display: grid;
      height: 100dvh;
      margin: 0;
      place-items: center;
      background: #111827;
      color: #f9fafb;
      overscroll-behavior: none;
      user-select: none;
      -webkit-user-select: none;
      -webkit-touch-callout: none;
    }

    main {
      box-sizing: border-box;
      width: min(94vw, 430px);
      max-height: 100dvh;
      overflow-y: auto;
      padding: 22px;
      border: 1px solid #ffffff12;
      border-radius: 24px;
      background: linear-gradient(160deg, #1f2937, #111827);
      box-shadow: 0 18px 45px #0008;
      text-align: center;
    }

    .controls {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin: 20px 0;
    }

    button {
      min-height: 68px;
      border: 0;
      border-radius: 14px;
      background: #2563eb;
      color: white;
      font-size: 1.75rem;
      font-weight: 700;
      touch-action: none;
      user-select: none;
      -webkit-user-select: none;
      -webkit-touch-callout: none;
      -webkit-tap-highlight-color: transparent;
      cursor: pointer;
    }

    button:active {
      transform: scale(0.96);
      background: #1d4ed8;
    }

    .stop {
      grid-column: 2;
      grid-row: 2;
      background: #dc2626;
      font-size: 0.95rem;
      letter-spacing: 0.08em;
    }

    h1 { margin: 0; font-size: 1.35rem; }
    .subtitle { margin: 6px 0 0; color: #94a3b8; font-size: .85rem; }

    label {
      display: block;
      margin-top: 16px;
      font-size: 1.05rem;
      font-weight: 700;
    }

    .led-controls {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin-top: 24px;
    }

    .led-controls button {
      --light-color: #38bdf8;
      min-height: 48px;
      padding: 8px 4px;
      border: 1px solid #334155;
      background: #0f172a;
      box-shadow: inset 0 0 12px #0008;
      color: #64748b;
      font-size: .72rem;
      letter-spacing: .04em;
      opacity: .65;
      transition: background .18s, box-shadow .18s, color .18s, opacity .18s;
    }

    .led-controls button[aria-pressed="true"] {
      background: var(--light-color);
      box-shadow: 0 0 14px var(--light-color);
      color: #fff;
      opacity: 1;
    }

    .led-controls [data-led-state="toggle-all"] {
      --light-color: #16a34a;
    }

    .led-controls [data-led-state="toggle-front"] {
      --light-color: #e2e8f0;
    }

    .led-controls [data-led-state="toggle-front"][aria-pressed="true"] {
      color: #0f172a;
    }

    .led-controls [data-led-state="toggle-center"] {
      --light-color: #2563eb;
    }

    .led-controls [data-led-state="toggle-rear"] {
      --light-color: #dc2626;
    }

    .expression-controls {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      margin-top: 8px;
    }

    .expression-controls button {
      min-height: 48px;
      background: #7c3aed;
      font-size: 1.15rem;
    }

    .expression-controls .sos {
      background: #dc2626;
      font-size: 1rem;
    }

    .expression-controls .rude {
      background: #be123c;
    }

    .collab-controls {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 8px;
    }

    .collab-controls button {
      min-height: 48px;
      padding: 6px;
      background: #0f766e;
      font-size: .78rem;
      line-height: 1.15;
    }

    .section-title {
      margin: 18px 0 0;
      color: #c4b5fd;
      font-size: .85rem;
      font-weight: 700;
      letter-spacing: .08em;
    }

    .led-off {
      background: #4b5563;
    }

    input[type="range"] {
      display: block;
      box-sizing: border-box;
      width: 100%;
      height: 48px;
      margin: 4px 0 0;
      appearance: none;
      -webkit-appearance: none;
      background: transparent;
      touch-action: pan-x;
      user-select: auto;
      -webkit-user-select: auto;
    }

    input[type="range"]::-webkit-slider-runnable-track {
      height: 14px;
      border-radius: 999px;
      background: #334155;
    }

    input[type="range"]::-webkit-slider-thumb {
      width: 34px;
      height: 34px;
      margin-top: -10px;
      border: 3px solid #dbeafe;
      border-radius: 50%;
      appearance: none;
      -webkit-appearance: none;
      background: #2563eb;
      box-shadow: 0 2px 8px #0008;
    }

    input[type="range"]::-moz-range-track {
      height: 14px;
      border-radius: 999px;
      background: #334155;
    }

    input[type="range"]::-moz-range-thumb {
      width: 28px;
      height: 28px;
      border: 3px solid #dbeafe;
      border-radius: 50%;
      background: #2563eb;
      box-shadow: 0 2px 8px #0008;
    }

    #status {
      min-height: 20px;
      margin: 12px 0 0;
      font-size: .9rem;
      color: #fbbf24;
    }
  </style>
</head>
<body>
  <main>
    <h1>Tokimi Rover</h1>
    <p class="subtitle">4WD CONTROL</p>

    <section class="controls" aria-label="Drive controls">
      <button data-command="forward-left" aria-label="Forward left">↖</button>
      <button data-command="forward" aria-label="Forward">↑</button>
      <button data-command="forward-right" aria-label="Forward right">↗</button>
      <button data-command="left" aria-label="Turn left">↺</button>
      <button class="stop" id="stop">STOP</button>
      <button data-command="right" aria-label="Turn right">↻</button>
      <button data-command="backward-left" aria-label="Backward left">↙</button>
      <button data-command="backward" aria-label="Backward">↓</button>
      <button data-command="backward-right" aria-label="Backward right">↘</button>
    </section>

    <label for="speed">Speed: <output id="speedValue">30</output>%</label>
    <input id="speed" type="range" min="0" max="100" value="30">

    <p class="section-title">OLED EXPRESSIONS</p>
    <section class="expression-controls" aria-label="OLED expressions">
      <button class="sos" data-expression="sos" aria-label="SOS">SOS</button>
      <button data-expression="happy" aria-label="Happy">喜</button>
      <button data-expression="angry" aria-label="Angry">怒</button>
      <button data-expression="sad" aria-label="Sad">哀</button>
      <button data-expression="joy" aria-label="Joy">樂</button>
      <button class="rude" data-expression="rude"
              aria-label="Middle finger">🖕</button>
    </section>

    <section class="collab-controls" aria-label="TASA collaborations">
      <button data-expression="tasa-tokimi">TASA feat TOKIMI</button>
      <button data-expression="tasa-astronaut">TASA feat ASTRONAUT</button>
    </section>

    <section class="led-controls" aria-label="WS2812B zone controls">
      <button data-led-state="toggle-all" aria-label="Toggle all lights"
              aria-pressed="true">ALL</button>
      <button data-led-state="toggle-front" aria-label="Toggle front lights"
              aria-pressed="true">FRONT</button>
      <button data-led-state="toggle-center" aria-label="Toggle center lights"
              aria-pressed="true">CENTER</button>
      <button data-led-state="toggle-rear" aria-label="Toggle rear lights"
              aria-pressed="true">REAR</button>
    </section>

    <p id="status">Robot stopped</p>
  </main>

  <script>
    const status = document.querySelector('#status');
    const speed = document.querySelector('#speed');
    const speedValue = document.querySelector('#speedValue');
    let commandTimer = null;
    let activeCommand = null;

    document.addEventListener('selectstart', (event) => event.preventDefault());

    async function sendCommand(command) {
      try {
        const response = await fetch(`/api/command?value=${command}`, {
          method: 'POST'
        });
        status.textContent = await response.text();
      } catch {
        status.textContent = 'Connection error';
        if (command !== 'stop') {
          stopDriving(true);
        }
      }
    }

    function stopDriving(force = false) {
      const wasDriving = activeCommand !== null;
      clearInterval(commandTimer);
      commandTimer = null;
      activeCommand = null;
      if (wasDriving || force) {
        sendCommand('stop');
      }
    }

    document.querySelectorAll('[data-command]').forEach((button) => {
      button.addEventListener('pointerdown', (event) => {
        event.preventDefault();
        clearInterval(commandTimer);
        activeCommand = button.dataset.command;
        sendCommand(activeCommand);
        commandTimer = setInterval(() => {
          if (activeCommand !== null) {
            sendCommand(activeCommand);
          }
        }, 250);
      });
      button.addEventListener('contextmenu', (event) => event.preventDefault());
      button.addEventListener('dragstart', (event) => event.preventDefault());
    });

    const stopButton = document.querySelector('#stop');
    stopButton.addEventListener('pointerdown', (event) => {
      event.preventDefault();
      stopDriving(true);
    });
    stopButton.addEventListener('contextmenu', (event) => event.preventDefault());

    document.addEventListener('pointerup', () => stopDriving());
    document.addEventListener('pointercancel', () => stopDriving());
    document.addEventListener('touchend', () => stopDriving(), { passive: true });
    document.addEventListener('touchcancel', () => stopDriving(), { passive: true });

    window.addEventListener('blur', () => {
      stopDriving();
    });

    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        stopDriving();
      }
    });

    document.querySelectorAll('[data-led-state]').forEach((button) => {
      button.addEventListener('click', async () => {
        try {
          const response = await fetch(
            `/api/led?state=${button.dataset.ledState}`,
            { method: 'POST' }
          );
          const message = await response.text();
          if (!response.ok) {
            throw new Error(message);
          }

          const isOn = button.getAttribute('aria-pressed') !== 'true';
          if (button.dataset.ledState === 'toggle-all') {
            document.querySelectorAll('[data-led-state]').forEach((item) => {
              item.setAttribute('aria-pressed', isOn ? 'true' : 'false');
            });
          } else {
            button.setAttribute('aria-pressed', isOn ? 'true' : 'false');
            const anyZoneOn = Array.from(document.querySelectorAll(
              '[data-led-state]:not([data-led-state="toggle-all"])'
            )).some((item) => item.getAttribute('aria-pressed') === 'true');
            document.querySelector('[data-led-state="toggle-all"]')
              .setAttribute('aria-pressed', anyZoneOn ? 'true' : 'false');
          }
          status.textContent = `${message} ${isOn ? 'ON' : 'OFF'}`;
        } catch {
          status.textContent = 'Connection error';
        }
      });
    });

    document.querySelectorAll('[data-expression]').forEach((button) => {
      button.addEventListener('click', async () => {
        try {
          const response = await fetch(
            `/api/expression?value=${button.dataset.expression}`,
            { method: 'POST' }
          );
          status.textContent = await response.text();
        } catch {
          status.textContent = 'Connection error';
        }
      });
    });

    speed.addEventListener('input', () => {
      speedValue.value = speed.value;
    });

    speed.addEventListener('change', async () => {
      try {
        const response = await fetch(`/api/speed?value=${speed.value}`, {
          method: 'POST'
        });
        status.textContent = await response.text();
      } catch {
        status.textContent = 'Connection error';
      }
    });
  </script>
</body>
</html>
)HTML";

}  // namespace web
