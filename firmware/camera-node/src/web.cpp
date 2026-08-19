// SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
// SPDX-License-Identifier: Apache-2.0

#include "web.h"

#include <Arduino.h>
#include <WiFi.h>
#include <cerrno>
#include <esp_heap_caps.h>
#include <esp_wifi.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <new>
#include <sys/socket.h>

#include "camera.h"

#if defined(__has_include)
#if __has_include("camera_config.h")
#include "camera_config.h"
#else
#error "Missing include/camera_config.h. Copy include/camera_config.h.example to include/camera_config.h and set unique AP credentials."
// Keep the remainder of this translation unit parseable so the explicit
// configuration error above is not buried under undefined-symbol diagnostics.
#include "camera_config.h.example"
#endif
#else
#include "camera_config.h"
#endif

namespace TokimiWeb {
namespace {

namespace Config = TokimiCameraConfig;

static_assert(sizeof(Config::kApSsid) > 1 && sizeof(Config::kApSsid) <= 33,
              "Camera AP SSID must contain 1-32 bytes");
static_assert(sizeof(Config::kApPassword) >= 9 &&
                  sizeof(Config::kApPassword) <= 64,
              "Camera AP password must contain 8-63 bytes");
static_assert(Config::kApChannel >= 1 && Config::kApChannel <= 13,
              "Camera AP channel must be between 1 and 13");
static_assert(Config::kMaxWifiClients >= 1 &&
                  Config::kMaxWifiClients <= 4,
              "Camera AP client limit must be between 1 and 4");
constexpr uint8_t kMaxHttpConnections = 6;
constexpr uint32_t kRecoveryIntervalMs = 5000;
constexpr uint32_t kWriteTimeoutMs = 300;
constexpr size_t kStreamWriteChunk = 4096;
constexpr uint32_t kDiagnosticsIntervalMs = 3000;
constexpr char kMjpegBoundary[] = "tokimi-boundary";

const char kIndexHtml[] PROGMEM = R"HTML(<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#03070d">
  <title>Tokimi Mission Camera</title>
  <style>
    :root{color-scheme:dark;--void:#03070d;--panel:#09121d;--line:#19364a;--cyan:#58e6ff;--amber:#ffbd5c;--text:#e8f6ff;--muted:#7892a3}
    *{box-sizing:border-box}html{min-height:100%}body{margin:0;min-height:100vh;color:var(--text);font:14px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--void);background-image:radial-gradient(#4fb2d533 1px,transparent 1px),radial-gradient(#fff2 1px,transparent 1px),linear-gradient(160deg,#06111d 0%,#02060b 68%);background-size:47px 47px,83px 83px,100% 100%;background-position:0 0,17px 29px,0 0}
    main{width:min(900px,100%);margin:auto;padding:22px}.top{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:14px}.brand{display:flex;align-items:center;gap:12px}.mark{width:38px;height:38px;border:1px solid var(--cyan);border-radius:50%;display:grid;place-items:center;box-shadow:0 0 18px #58e6ff33}.mark:after{content:'';width:13px;height:13px;border:1px solid var(--cyan);border-radius:50%;box-shadow:0 0 8px var(--cyan)}
    .eyebrow,.label{color:var(--muted);font-size:.68rem;letter-spacing:.17em;text-transform:uppercase}.brand h1{font:600 1.05rem system-ui,sans-serif;letter-spacing:.08em;margin:2px 0 0}.link{display:flex;align-items:center;gap:8px;color:var(--cyan);font-size:.72rem;letter-spacing:.12em}.dot{width:7px;height:7px;border-radius:50%;background:var(--cyan);box-shadow:0 0 9px var(--cyan);animation:pulse 2s infinite}.dot.off{background:#ff6b6b;box-shadow:0 0 9px #ff6b6b}@keyframes pulse{50%{opacity:.38}}
    .shell{position:relative;padding:7px;border:1px solid var(--line);background:#07101aaa;box-shadow:0 18px 55px #000a}.camera{position:relative;background:#000;overflow:hidden;aspect-ratio:3/2}.camera img{position:absolute;left:50%;top:50%;display:block;width:100%;height:100%;object-fit:fill;transform-origin:center;transform:translate(-50%,-50%) scaleX(-1)}.camera canvas{position:absolute;inset:0;width:100%;height:100%;z-index:2;pointer-events:none}.camera:before,.camera:after{content:'';position:absolute;inset:12px;z-index:1;pointer-events:none}.camera:before{border:1px solid #58e6ff55;clip-path:polygon(0 0,13% 0,13% 1px,1px 1px,1px 13%,0 13%,0 0,100% 0,100% 13%,calc(100% - 1px) 13%,calc(100% - 1px) 1px,87% 1px,87% 0,100% 0,100% 100%,87% 100%,87% calc(100% - 1px),calc(100% - 1px) calc(100% - 1px),calc(100% - 1px) 87%,100% 87%,100% 100%,0 100%,0 87%,1px 87%,1px calc(100% - 1px),13% calc(100% - 1px),13% 100%)}.camera:after{inset:50%;width:28px;height:28px;transform:translate(-50%,-50%);border:1px solid #58e6ff88;border-radius:50%;background:linear-gradient(#58e6ff88,#58e6ff88) center/1px 100% no-repeat,linear-gradient(90deg,#58e6ff88,#58e6ff88) center/100% 1px no-repeat}
    .feedtag{position:absolute;left:18px;top:18px;z-index:3;padding:5px 8px;color:var(--cyan);background:#02070bcc;border-left:2px solid var(--cyan);font-size:.65rem;letter-spacing:.14em}.coords{position:absolute;right:18px;bottom:17px;z-index:3;color:#b9d3df;font-size:.64rem;letter-spacing:.1em;text-shadow:0 1px 3px #000}
    .panel{display:grid;grid-template-columns:1fr auto;gap:14px;margin-top:14px}.status{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.metric{min-width:0;padding:12px 14px;background:linear-gradient(135deg,#0b1925dd,#07101add);border:1px solid var(--line);border-top-color:#28546d}.value{display:block;margin-top:7px;color:var(--cyan);font:600 1rem system-ui,sans-serif;white-space:nowrap}.actions{display:flex;gap:8px}
    button{min-width:128px;border:1px solid #297089;background:#0a2836;color:var(--cyan);padding:0 17px;font:700 .72rem ui-monospace,monospace;letter-spacing:.1em;text-transform:uppercase;cursor:pointer}button:hover{background:#0d3445}button:active{transform:translateY(1px)}button.danger{min-width:48px;background:#251817;border-color:#6b4037;color:var(--amber)}
    .footer{display:flex;justify-content:space-between;gap:15px;margin-top:13px;padding-top:11px;border-top:1px solid #142b3b;color:var(--muted);font-size:.68rem;letter-spacing:.06em}.footer span:last-child{color:#466779}
    @media(max-width:680px){main{padding:12px}.top{margin:2px 2px 12px}.brand h1{font-size:.9rem}.link{font-size:.63rem}.panel{grid-template-columns:1fr}.actions{height:44px}.actions button:first-child{flex:1}.status{grid-template-columns:repeat(2,1fr);gap:6px}.metric{padding:10px}.value{font-size:.84rem}.coords{display:none}.footer{display:block;line-height:1.7}.footer span:last-child{display:none}}
  </style>
</head>
<body><main>
  <header class="top">
    <div class="brand"><div class="mark"></div><div><div class="eyebrow">Ground Support Rover</div><h1>TOKIMI // OPTICAL UNIT</h1></div></div>
    <div class="link"><i id="dot" class="dot"></i><span id="link">LINK ACQUIRING</span></div>
  </header>
  <div class="shell"><div class="camera">
    <img id="live" src="/stream" alt="Live camera feed">
    <canvas id="contours" width="480" height="320"></canvas>
    <span class="feedtag">CAM-01 · LIVE</span><span id="coords" class="coords">AP CONFIGURING</span>
  </div>
  </div>
  <div class="panel">
    <section class="status">
      <div class="metric"><span class="label">System Heap</span><span id="heap" class="value">—</span></div>
      <div class="metric"><span class="label">PSRAM Array</span><span id="psram" class="value">—</span></div>
      <div class="metric"><span class="label">Optical Frame</span><span id="resolution" class="value">—</span></div>
      <div class="metric"><span class="label">Signal RSSI</span><span id="rssi" class="value">—</span></div>
      <div class="metric"><span class="label">Actual FPS</span><span id="actualfps" class="value">—</span></div>
      <div class="metric"><span class="label">Wi-Fi Link</span><span id="wifi" class="value">—</span></div>
      <div class="metric"><span class="label">AP Name</span><span id="apname" class="value">—</span></div>
      <div class="metric"><span class="label">Current IP</span><span id="ip" class="value">—</span></div>
      <div class="metric"><span class="label">JPEG Average</span><span id="jpeg" class="value">—</span></div>
      <div class="metric"><span class="label">Rocket Scan</span><span id="vision" class="value">STARTING</span></div>
    </section>
    <div class="actions"><button id="capture">Capture Frame</button><button id="restart" class="danger" title="Restart optical unit">RST</button></div>
  </div>
  <div class="footer"><span id="state">ESTABLISHING TELEMETRY LINK…</span><span>MISSION TIME <b id="uptime">00:00:00</b> · <b id="fps">—</b> FPS</span></div>
</main><script>
const $=id=>document.getElementById(id),state=$('state'),live=$('live');
let reconnectTimer=0,zeroFpsSince=0,recoveryAttempts=0,lastReloadAt=0;
try{lastReloadAt=Number(sessionStorage.getItem('tokimiReloadAt'))||0}catch(e){}
function clock(ms){let s=Math.floor(ms/1000),h=Math.floor(s/3600);s%=3600;let m=Math.floor(s/60);s%=60;return[h,m,s].map(n=>String(n).padStart(2,'0')).join(':')}
function reconnect(delay=0){clearTimeout(reconnectTimer);reconnectTimer=setTimeout(()=>{reconnectTimer=0;if(document.hidden)return;recoveryAttempts++;zeroFpsSince=Date.now();live.src='/stream?t='+Date.now()},delay)}
function reloadPage(){const now=Date.now();if(now-lastReloadAt<30000){reconnect(2000);return}lastReloadAt=now;try{sessionStorage.setItem('tokimiReloadAt',String(now))}catch(e){}location.reload()}
const contourCanvas=$('contours'),contourContext=contourCanvas.getContext('2d');
const workCanvas=document.createElement('canvas'),workContext=workCanvas.getContext('2d',{willReadFrequently:true});
const scanWidth=160,scanHeight=107,scanPixels=scanWidth*scanHeight;
workCanvas.width=scanWidth;workCanvas.height=scanHeight;
const gray=new Uint8Array(scanPixels),edgeMask=new Uint8Array(scanPixels),visited=new Uint8Array(scanPixels),queue=new Uint32Array(scanPixels);
function scanContours(){
  if(!document.hidden&&live.naturalWidth){
    try{
      workContext.drawImage(live,0,0,scanWidth,scanHeight);
      const rgba=workContext.getImageData(0,0,scanWidth,scanHeight).data;
      for(let i=0,p=0;i<scanPixels;i++,p+=4)gray[i]=(rgba[p]*77+rgba[p+1]*150+rgba[p+2]*29)>>8;
      edgeMask.fill(0);visited.fill(0);
      for(let y=1;y<scanHeight-1;y++)for(let x=1;x<scanWidth-1;x++){
        const i=y*scanWidth+x;
        const gx=-gray[i-scanWidth-1]+gray[i-scanWidth+1]-2*gray[i-1]+2*gray[i+1]-gray[i+scanWidth-1]+gray[i+scanWidth+1];
        const gy=-gray[i-scanWidth-1]-2*gray[i-scanWidth]-gray[i-scanWidth+1]+gray[i+scanWidth-1]+2*gray[i+scanWidth]+gray[i+scanWidth+1];
        if(Math.abs(gx)+Math.abs(gy)>280)for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++)edgeMask[i+dy*scanWidth+dx]=1;
      }
      const boxes=[];
      for(let start=0;start<scanPixels;start++){
        if(!edgeMask[start]||visited[start])continue;
        let head=0,tail=0,count=0,minX=scanWidth,minY=scanHeight,maxX=0,maxY=0;
        visited[start]=1;queue[tail++]=start;
        while(head<tail){
          const i=queue[head++],x=i%scanWidth,y=(i/scanWidth)|0;count++;
          if(x<minX)minX=x;if(x>maxX)maxX=x;if(y<minY)minY=y;if(y>maxY)maxY=y;
          for(let ny=Math.max(0,y-1);ny<=Math.min(scanHeight-1,y+1);ny++)for(let nx=Math.max(0,x-1);nx<=Math.min(scanWidth-1,x+1);nx++){
            const next=ny*scanWidth+nx;
            if(edgeMask[next]&&!visited[next]){visited[next]=1;queue[tail++]=next}
          }
        }
        const width=maxX-minX+1,height=maxY-minY+1,longSide=Math.max(width,height),shortSide=Math.min(width,height),area=width*height,aspect=longSide/Math.max(1,shortSide),density=count/area;
        if(shortSide>=5&&longSide>=18&&aspect>=2.2&&aspect<=12&&area>=180&&area<=scanPixels*.4&&density>=.08&&density<=.85)boxes.push({x:minX,y:minY,width,height,score:area*aspect*density});
      }
      boxes.sort((a,b)=>b.score-a.score);contourContext.clearRect(0,0,480,320);
      const visible=boxes.slice(0,1),scaleX=480/scanWidth,scaleY=320/scanHeight;
      contourContext.lineWidth=2;contourContext.font='bold 12px ui-monospace,monospace';
      visible.forEach(box=>{
        const x=(scanWidth-box.x-box.width)*scaleX,y=box.y*scaleY,width=box.width*scaleX,height=box.height*scaleY,label='ROCKET';
        contourContext.strokeStyle='#58e6ff';contourContext.strokeRect(x,y,width,height);
        contourContext.fillStyle='#02070bcc';contourContext.fillRect(x,Math.max(0,y-17),54,17);
        contourContext.fillStyle='#58e6ff';contourContext.fillText(label,x+4,Math.max(12,y-4));
      });
      $('vision').textContent=visible.length?'LOCKED':'SCANNING';
    }catch(e){contourContext.clearRect(0,0,480,320);$('vision').textContent='WAITING'}
  }
  setTimeout(scanContours,250);
}
async function status(){try{const r=await fetch('/status',{cache:'no-store'});if(!r.ok)throw Error(r.status);const s=await r.json();
$('heap').textContent=(s.heap/1024).toFixed(1)+' KiB';$('psram').textContent=s.psram?(s.psram_free/1024).toFixed(0)+' KiB':'NOT FOUND';$('resolution').textContent=s.resolution;
$('rssi').textContent=s.rssi<=-127?'N/A':s.rssi+' dBm';const measuredFps=Number(s.actual_fps);$('actualfps').textContent=measuredFps.toFixed(1);$('wifi').textContent='CH '+s.channel+' · '+s.phy;$('apname').textContent=s.ap;$('ip').textContent=s.ip;$('coords').textContent='AP '+s.ip+' // CH '+s.channel;$('jpeg').textContent=s.avg_jpeg_bytes?s.avg_jpeg_bytes+' B':'—';
$('uptime').textContent=clock(s.uptime);$('fps').textContent=measuredFps.toFixed(1);$('link').textContent=s.camera==='online'?'UPLINK NOMINAL':'CAMERA OFFLINE';$('dot').classList.toggle('off',s.camera!=='online');state.textContent='SENSOR '+s.sensor+' · OPTICAL TELEMETRY '+s.camera.toUpperCase();if(measuredFps>0){zeroFpsSince=0;recoveryAttempts=0}else if(s.camera==='online'){if(!zeroFpsSince)zeroFpsSince=Date.now();if(Date.now()-zeroFpsSince>=5000){if(recoveryAttempts>=3)reloadPage();else reconnect()}}}catch(e){$('link').textContent='LINK LOST';$('dot').classList.add('off');state.textContent='TELEMETRY UNAVAILABLE';reconnect(1000)}}
document.getElementById('capture').onclick=()=>window.open('/capture?t='+Date.now(),'_blank');
document.getElementById('restart').onclick=async()=>{if(!confirm('Restart optical unit?'))return;state.textContent='RESTART SEQUENCE INITIATED';try{await fetch('/restart',{cache:'no-store'})}catch(e){}reconnect(3500)};
live.onerror=()=>reconnect(1000);document.addEventListener('visibilitychange',()=>{if(!document.hidden){reconnect();status()}});window.addEventListener('online',()=>reconnect());
scanContours();status();setInterval(status,2000);
</script></body></html>)HTML";

WiFiServer httpServer(80);
volatile bool serverStarted = false;
volatile bool apOnline = false;
char errorMessage[128] = "web server has not been initialized";
uint32_t lastRecoveryCheckMs = 0;
uint32_t lastDiagnosticsLogMs = 0;
portMUX_TYPE stateMux = portMUX_INITIALIZER_UNLOCKED;
portMUX_TYPE diagnosticsMux = portMUX_INITIALIZER_UNLOCKED;
uint8_t activeConnections = 0;
bool streamActive = false;

struct StreamMetrics {
  float fps = 0.0F;
  float averageFrameMs = 0.0F;
  float averageCaptureMs = 0.0F;
  uint32_t averageJpegBytes = 0;
};

struct WiFiMetrics {
  int8_t rssi = -127;
  uint8_t channel = 0;
  uint8_t protocol = 0;
  wifi_bandwidth_t bandwidth = WIFI_BW_HT20;
  wifi_ps_type_t powerSave = WIFI_PS_NONE;
  int8_t txPowerQuarterDbm = 0;
  const char* phy = "none";
};

StreamMetrics latestStreamMetrics;

struct ClientContext {
  WiFiClient client;
};

void setError(const char* message) {
  strlcpy(errorMessage, message, sizeof(errorMessage));
}

const char* protocolName(uint8_t protocol) {
  const uint8_t standard =
      protocol & (WIFI_PROTOCOL_11B | WIFI_PROTOCOL_11G | WIFI_PROTOCOL_11N);
  if (standard ==
      (WIFI_PROTOCOL_11B | WIFI_PROTOCOL_11G | WIFI_PROTOCOL_11N)) {
    return "11b/g/n";
  }
  if (standard == (WIFI_PROTOCOL_11G | WIFI_PROTOCOL_11N)) {
    return "11g/n";
  }
  if (standard == WIFI_PROTOCOL_11N) {
    return "11n";
  }
  if (standard == WIFI_PROTOCOL_11G) {
    return "11g";
  }
  if (standard == WIFI_PROTOCOL_11B) {
    return "11b";
  }
  return "unknown";
}

const char* powerSaveName(wifi_ps_type_t powerSave) {
  switch (powerSave) {
    case WIFI_PS_NONE:
      return "OFF";
    case WIFI_PS_MIN_MODEM:
      return "MIN_MODEM";
    case WIFI_PS_MAX_MODEM:
      return "MAX_MODEM";
    default:
      return "UNKNOWN";
  }
}

WiFiMetrics readWiFiMetrics() {
  WiFiMetrics metrics;
  wifi_second_chan_t secondaryChannel = WIFI_SECOND_CHAN_NONE;
  esp_wifi_get_channel(&metrics.channel, &secondaryChannel);
  esp_wifi_get_protocol(WIFI_IF_AP, &metrics.protocol);
  esp_wifi_get_bandwidth(WIFI_IF_AP, &metrics.bandwidth);
  esp_wifi_get_ps(&metrics.powerSave);
  esp_wifi_get_max_tx_power(&metrics.txPowerQuarterDbm);

  wifi_sta_list_t stations = {};
  if (esp_wifi_ap_get_sta_list(&stations) == ESP_OK && stations.num > 0) {
    const wifi_sta_info_t& station = stations.sta[0];
    metrics.rssi = station.rssi;
    if (station.phy_11n) {
      metrics.phy = "11n";
    } else if (station.phy_11g) {
      metrics.phy = "11g";
    } else if (station.phy_11b) {
      metrics.phy = "11b";
    } else if (station.phy_lr) {
      metrics.phy = "LR";
    } else {
      metrics.phy = "unknown";
    }
  }
  return metrics;
}

void setStreamMetrics(float fps, float averageFrameMs,
                      float averageCaptureMs, uint32_t averageJpegBytes) {
  portENTER_CRITICAL(&diagnosticsMux);
  latestStreamMetrics.fps = fps;
  latestStreamMetrics.averageFrameMs = averageFrameMs;
  latestStreamMetrics.averageCaptureMs = averageCaptureMs;
  latestStreamMetrics.averageJpegBytes = averageJpegBytes;
  portEXIT_CRITICAL(&diagnosticsMux);
}

StreamMetrics getStreamMetrics() {
  portENTER_CRITICAL(&diagnosticsMux);
  const StreamMetrics metrics = latestStreamMetrics;
  portEXIT_CRITICAL(&diagnosticsMux);
  return metrics;
}

void logDiagnostics() {
  const WiFiMetrics wifi = readWiFiMetrics();
  const StreamMetrics stream = getStreamMetrics();
  const String ip = WiFi.softAPIP().toString();
  char rssiText[12];
  if (wifi.rssi <= -127) {
    strlcpy(rssiText, "n/a", sizeof(rssiText));
  } else {
    snprintf(rssiText, sizeof(rssiText), "%ddBm", wifi.rssi);
  }

  Serial.printf(
      "[diag] rssi=%s ch=%u phy=%s protocols=%s bw=%uMHz "
      "tx-max=%.1fdBm power-save=%s ip=%s ap=%s fps=%.1f "
      "avg-frame=%.1fms avg-jpeg=%uB heap=%u psram=%u\n",
      rssiText, wifi.channel, wifi.phy, protocolName(wifi.protocol),
      wifi.bandwidth == WIFI_BW_HT40 ? 40 : 20,
      wifi.txPowerQuarterDbm / 4.0F, powerSaveName(wifi.powerSave),
      ip.c_str(), Config::kApSsid, stream.fps, stream.averageFrameMs,
      stream.averageJpegBytes, ESP.getFreeHeap(), ESP.getFreePsram());
}

void handleWiFiEvent(WiFiEvent_t event) {
  switch (event) {
    case ARDUINO_EVENT_WIFI_AP_START:
      apOnline = true;
      Serial.println("[wifi] access point started");
      break;
    case ARDUINO_EVENT_WIFI_AP_STOP:
      apOnline = false;
      Serial.println("[wifi] WARNING: access point stopped");
      break;
    case ARDUINO_EVENT_WIFI_AP_STACONNECTED:
      Serial.printf("[wifi] client connected; clients=%u\n",
                    WiFi.softAPgetStationNum());
      break;
    case ARDUINO_EVENT_WIFI_AP_STADISCONNECTED:
      Serial.printf("[wifi] client disconnected; clients=%u\n",
                    WiFi.softAPgetStationNum());
      break;
    default:
      break;
  }
}

bool startAccessPoint() {
  const IPAddress localIp(Config::kApAddress[0], Config::kApAddress[1],
                          Config::kApAddress[2], Config::kApAddress[3]);
  const IPAddress gateway(Config::kApGateway[0], Config::kApGateway[1],
                          Config::kApGateway[2], Config::kApGateway[3]);
  const IPAddress subnet(Config::kApSubnet[0], Config::kApSubnet[1],
                         Config::kApSubnet[2], Config::kApSubnet[3]);

  Serial.printf("[wifi] starting AP SSID=%s channel=%u\n", Config::kApSsid,
                Config::kApChannel);
  WiFi.mode(WIFI_AP);
  WiFi.setSleep(false);

  if (!WiFi.softAPConfig(localIp, gateway, subnet)) {
    setError("Wi-Fi AP IP configuration failed");
    Serial.printf("[wifi] ERROR: %s\n", errorMessage);
    return false;
  }

  if (!WiFi.softAP(Config::kApSsid, Config::kApPassword, Config::kApChannel,
                   false, Config::kMaxWifiClients)) {
    setError("Wi-Fi AP start failed");
    Serial.printf("[wifi] ERROR: %s\n", errorMessage);
    return false;
  }

  const bool txPowerSet = WiFi.setTxPower(WIFI_POWER_19_5dBm);
  const esp_err_t bandwidthResult =
      esp_wifi_set_bandwidth(WIFI_IF_AP, WIFI_BW_HT20);
  const esp_err_t powerSaveResult = esp_wifi_set_ps(WIFI_PS_NONE);

  apOnline = true;
  setError("none");
  Serial.printf("[wifi] AP ready: http://%s/\n",
                WiFi.softAPIP().toString().c_str());
  Serial.printf(
      "[wifi] AP MAC=%s channel=%u bandwidth=20MHz TX=%.1f dBm "
      "sleep=disabled (%s/%s)\n",
      WiFi.softAPmacAddress().c_str(), Config::kApChannel,
      static_cast<int>(WiFi.getTxPower()) / 4.0F,
      txPowerSet ? "tx-ok" : "tx-error",
      bandwidthResult == ESP_OK ? "bw-ok" : "bw-error");
  Serial.printf("[wifi] power-save disable: %s\n",
                powerSaveResult == ESP_OK ? "ok" : "error");
  return true;
}

bool claimConnection() {
  bool claimed = false;
  portENTER_CRITICAL(&stateMux);
  if (activeConnections < kMaxHttpConnections) {
    ++activeConnections;
    claimed = true;
  }
  portEXIT_CRITICAL(&stateMux);
  return claimed;
}

void releaseConnection() {
  portENTER_CRITICAL(&stateMux);
  if (activeConnections > 0) {
    --activeConnections;
  }
  portEXIT_CRITICAL(&stateMux);
}

bool claimStream() {
  bool claimed = false;
  portENTER_CRITICAL(&stateMux);
  if (!streamActive) {
    streamActive = true;
    claimed = true;
  }
  portEXIT_CRITICAL(&stateMux);
  return claimed;
}

void releaseStream() {
  portENTER_CRITICAL(&stateMux);
  streamActive = false;
  portEXIT_CRITICAL(&stateMux);
}

bool writeAll(WiFiClient& client, const uint8_t* data, size_t length) {
  size_t offset = 0;
  uint32_t noProgressSince = millis();
  const int socketFd = client.fd();
  if (socketFd < 0) {
    return false;
  }

  while (offset < length && client.connected()) {
    const size_t remaining = length - offset;
    const size_t chunk =
        remaining < kStreamWriteChunk ? remaining : kStreamWriteChunk;
    const ssize_t written =
        send(socketFd, data + offset, chunk, MSG_DONTWAIT);
    if (written > 0) {
      offset += static_cast<size_t>(written);
      noProgressSince = millis();
    } else if (written == 0) {
      return false;
    } else if (errno == EAGAIN || errno == EWOULDBLOCK || errno == ENOMEM) {
      if (millis() - noProgressSince >= kWriteTimeoutMs) {
        return false;
      }
      delay(1);
    } else {
      return false;
    }
  }
  return offset == length;
}

bool writeAll(WiFiClient& client, const char* text) {
  return writeAll(client, reinterpret_cast<const uint8_t*>(text),
                  strlen(text));
}

void sendSimple(WiFiClient& client, int code, const char* reason,
                const char* contentType, const String& body) {
  client.printf("HTTP/1.1 %d %s\r\n", code, reason);
  client.printf("Content-Type: %s\r\n", contentType);
  client.printf("Content-Length: %u\r\n", body.length());
  writeAll(client, "Cache-Control: no-store\r\nConnection: close\r\n\r\n");
  writeAll(client, reinterpret_cast<const uint8_t*>(body.c_str()),
           body.length());
}

void handleRoot(WiFiClient& client) {
  client.print(
      "HTTP/1.1 200 OK\r\n"
      "Content-Type: text/html; charset=utf-8\r\n"
      "Cache-Control: no-store\r\n"
      "Connection: close\r\n");
  client.printf("Content-Length: %u\r\n\r\n", sizeof(kIndexHtml) - 1);
  writeAll(client, reinterpret_cast<const uint8_t*>(kIndexHtml),
           sizeof(kIndexHtml) - 1);
  Serial.println("[http] GET / -> 200");
}

void handleStatus(WiFiClient& client) {
  const WiFiMetrics wifi = readWiFiMetrics();
  const StreamMetrics stream = getStreamMetrics();
  const String ip = WiFi.softAPIP().toString();
  char json[768];
  snprintf(json, sizeof(json),
           "{\"camera\":\"%s\",\"sensor\":\"OV3660\","
           "\"resolution\":\"%ux%u\",\"fps\":%u,"
           "\"actual_fps\":%.1f,\"avg_frame_ms\":%.1f,"
           "\"avg_capture_ms\":%.1f,\"avg_jpeg_bytes\":%u,"
           "\"heap\":%u,\"psram\":%s,\"psram_free\":%u,"
           "\"uptime\":%lu,\"rssi\":%d,\"channel\":%u,"
           "\"phy\":\"%s\",\"protocol\":\"%s\","
           "\"bandwidth_mhz\":%u,\"tx_power_dbm\":%.1f,"
           "\"power_save\":%s,\"ip\":\"%s\",\"ap\":\"%s\"}",
           TokimiCamera::isOnline() ? "online" : "offline",
           TokimiCamera::kWidth, TokimiCamera::kHeight,
           TokimiCamera::kTargetFps, stream.fps, stream.averageFrameMs,
           stream.averageCaptureMs, stream.averageJpegBytes,
           ESP.getFreeHeap(), psramFound() ? "true" : "false",
           ESP.getFreePsram(), static_cast<unsigned long>(millis()),
           wifi.rssi, wifi.channel, wifi.phy, protocolName(wifi.protocol),
           wifi.bandwidth == WIFI_BW_HT40 ? 40 : 20,
           wifi.txPowerQuarterDbm / 4.0F,
           wifi.powerSave == WIFI_PS_NONE ? "false" : "true", ip.c_str(),
           Config::kApSsid);
  sendSimple(client, 200, "OK", "application/json", json);
}

void handleRestart(WiFiClient& client) {
  Serial.println("[system] manual restart requested from Web UI");
  sendSimple(client, 200, "OK", "application/json",
             "{\"restarting\":true}");
  client.flush();
  delay(150);
  ESP.restart();
}

bool readRequest(WiFiClient& client, String* method, String* path) {
  // This Arduino core's WiFiClient override accepts seconds, not milliseconds.
  client.setTimeout(2);
  String requestLine = client.readStringUntil('\n');
  requestLine.trim();
  if (requestLine.length() == 0 || requestLine.length() > 255) {
    return false;
  }

  const int firstSpace = requestLine.indexOf(' ');
  const int secondSpace = requestLine.indexOf(' ', firstSpace + 1);
  if (firstSpace <= 0 || secondSpace <= firstSpace + 1) {
    return false;
  }

  *method = requestLine.substring(0, firstSpace);
  *path = requestLine.substring(firstSpace + 1, secondSpace);
  const int query = path->indexOf('?');
  if (query >= 0) {
    path->remove(query);
  }

  size_t headerBytes = requestLine.length();
  while (client.connected() && headerBytes < 2048) {
    String header = client.readStringUntil('\n');
    headerBytes += header.length();
    header.trim();
    if (header.length() == 0) {
      return true;
    }
  }
  return false;
}

void handleCapture(WiFiClient& client) {
  if (!TokimiCamera::isOnline()) {
    Serial.printf("[http] GET /capture -> 503 (%s)\n",
                  TokimiCamera::lastError());
    sendSimple(client, 503, "Service Unavailable", "application/json",
               String("{\"error\":\"") + TokimiCamera::lastError() + "\"}");
    return;
  }

  TokimiCamera::JpegFrame frame;
  if (!TokimiCamera::copyLatestJpeg(&frame, 250)) {
    Serial.println("[http] GET /capture -> 503 (JPEG unavailable)");
    sendSimple(client, 503, "Service Unavailable", "application/json",
               "{\"error\":\"JPEG capture unavailable\"}");
    return;
  }

  client.print(
      "HTTP/1.1 200 OK\r\n"
      "Content-Type: image/jpeg\r\n"
      "Cache-Control: no-store, no-cache, must-revalidate\r\n"
      "Pragma: no-cache\r\n"
      "Content-Disposition: inline; filename=\"tokimi-camera.jpg\"\r\n"
      "Connection: close\r\n");
  client.printf("Content-Length: %u\r\n\r\n", frame.length);
  const bool sent = writeAll(client, frame.data, frame.length);
  Serial.printf("[http] GET /capture -> %s (%u bytes, sequence=%lu)\n",
                sent ? "200" : "client disconnected", frame.length,
                static_cast<unsigned long>(frame.sequence));
  TokimiCamera::releaseJpeg(&frame);
}

void handleStream(WiFiClient& client) {
  if (!TokimiCamera::isOnline()) {
    sendSimple(client, 503, "Service Unavailable", "application/json",
               String("{\"error\":\"") + TokimiCamera::lastError() + "\"}");
    return;
  }
  if (!claimStream()) {
    sendSimple(client, 503, "Service Unavailable", "application/json",
               "{\"error\":\"one MJPEG stream is already active\"}");
    return;
  }

  client.setNoDelay(true);
  client.setTimeout(2);
  client.print(
      "HTTP/1.1 200 OK\r\n"
      "Content-Type: multipart/x-mixed-replace; boundary=tokimi-boundary\r\n"
      "Cache-Control: no-store, no-cache, must-revalidate\r\n"
      "Pragma: no-cache\r\n"
      "Connection: close\r\n\r\n");
  Serial.println("[stream] MJPEG client connected");

  const uint32_t framePeriodMs = 1000 / TokimiCamera::kTargetFps;
  uint32_t framesSent = 0;
  uint32_t reportStartedMs = millis();
  uint64_t accumulatedFrameUs = 0;
  uint64_t accumulatedCaptureUs = 0;
  uint64_t accumulatedJpegBytes = 0;

  while (client.connected() && apOnline && TokimiCamera::isOnline()) {
    const uint32_t frameStartedMs = millis();
    const uint32_t frameStartedUs = micros();
    TokimiCamera::JpegFrame frame;
    const uint32_t captureStartedUs = micros();
    if (!TokimiCamera::acquireJpeg(&frame)) {
      delay(10);
      continue;
    }
    const uint32_t captureTimeUs = micros() - captureStartedUs;
    const size_t jpegLength = frame.length;

    char partHeader[128];
    const int headerLength = snprintf(
        partHeader, sizeof(partHeader),
        "--%s\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n",
        kMjpegBoundary, frame.length);
    const bool jpegSent =
        headerLength > 0 &&
        writeAll(client, reinterpret_cast<const uint8_t*>(partHeader),
                 static_cast<size_t>(headerLength)) &&
        writeAll(client, frame.data, frame.length);
    TokimiCamera::releaseJpeg(&frame);
    const bool sent = jpegSent && writeAll(client, "\r\n");
    if (!sent) {
      break;
    }

    ++framesSent;
    accumulatedCaptureUs += captureTimeUs;
    accumulatedFrameUs += micros() - frameStartedUs;
    accumulatedJpegBytes += jpegLength;
    const uint32_t now = millis();
    const uint32_t reportDurationMs = now - reportStartedMs;
    if (reportDurationMs >= kDiagnosticsIntervalMs) {
      const float actualFps =
          framesSent * 1000.0F / static_cast<float>(reportDurationMs);
      const float averageFrameMs =
          accumulatedFrameUs / (framesSent * 1000.0F);
      const float averageCaptureMs =
          accumulatedCaptureUs / (framesSent * 1000.0F);
      const uint32_t averageJpegBytes = accumulatedJpegBytes / framesSent;
      setStreamMetrics(actualFps, averageFrameMs, averageCaptureMs,
                       averageJpegBytes);
      framesSent = 0;
      reportStartedMs = now;
      accumulatedFrameUs = 0;
      accumulatedCaptureUs = 0;
      accumulatedJpegBytes = 0;
    }

    const uint32_t elapsed = millis() - frameStartedMs;
    if (elapsed < framePeriodMs) {
      delay(framePeriodMs - elapsed);
    }
  }

  releaseStream();
  setStreamMetrics(0.0F, 0.0F, 0.0F, 0);
  Serial.println("[stream] MJPEG client disconnected");
}

void handleClientTask(void* parameter) {
  ClientContext* context = static_cast<ClientContext*>(parameter);
  WiFiClient client = context->client;
  delete context;

  client.setNoDelay(true);
  String method;
  String path;
  if (!readRequest(client, &method, &path)) {
    sendSimple(client, 400, "Bad Request", "application/json",
               "{\"error\":\"bad HTTP request\"}");
  } else if (method != "GET") {
    sendSimple(client, 405, "Method Not Allowed", "application/json",
               "{\"error\":\"GET required\"}");
  } else if (path == "/") {
    handleRoot(client);
  } else if (path == "/capture") {
    handleCapture(client);
  } else if (path == "/stream") {
    handleStream(client);
  } else if (path == "/status") {
    handleStatus(client);
  } else if (path == "/restart") {
    handleRestart(client);
  } else {
    Serial.printf("[http] GET %s -> 404\n", path.c_str());
    sendSimple(client, 404, "Not Found", "application/json",
               "{\"error\":\"not found\"}");
  }

  client.stop();
  releaseConnection();
  vTaskDelete(nullptr);
}

void acceptClient() {
  WiFiClient client = httpServer.available();
  if (!client) {
    return;
  }

  if (!claimConnection()) {
    sendSimple(client, 503, "Service Unavailable", "application/json",
               "{\"error\":\"HTTP connection limit reached\"}");
    client.stop();
    return;
  }

  ClientContext* context = new (std::nothrow) ClientContext{client};
  if (context == nullptr) {
    releaseConnection();
    sendSimple(client, 503, "Service Unavailable", "application/json",
               "{\"error\":\"out of memory\"}");
    client.stop();
    return;
  }

  const BaseType_t taskResult =
      xTaskCreate(handleClientTask, "http-client", 8192, context, 1, nullptr);
  if (taskResult != pdPASS) {
    delete context;
    releaseConnection();
    sendSimple(client, 503, "Service Unavailable", "application/json",
               "{\"error\":\"could not start HTTP task\"}");
    client.stop();
  }
}

}  // namespace

bool begin() {
  if (serverStarted) {
    return true;
  }

  WiFi.onEvent(handleWiFiEvent);
  if (!startAccessPoint()) {
    Serial.println("[web] HTTP server not started because AP setup failed");
    return false;
  }

  httpServer.setNoDelay(true);
  httpServer.begin();
  serverStarted = true;
  const String baseUrl = String("http://") + WiFi.softAPIP().toString();
  Serial.println("[web] HTTP server listening on port 80");
  Serial.printf("[web] JPEG snapshot: %s/capture\n", baseUrl.c_str());
  Serial.printf("[web] MJPEG stream: %s/stream\n", baseUrl.c_str());
  Serial.printf("[web] JSON status: %s/status\n", baseUrl.c_str());
  return true;
}

void maintain() {
  if (serverStarted && apOnline) {
    acceptClient();
  }

  const uint32_t now = millis();
  if (now - lastDiagnosticsLogMs >= kDiagnosticsIntervalMs) {
    lastDiagnosticsLogMs = now;
    logDiagnostics();
  }

  if (now - lastRecoveryCheckMs < kRecoveryIntervalMs) {
    return;
  }
  lastRecoveryCheckMs = now;

  const bool apModeEnabled = (WiFi.getMode() & WIFI_AP) != 0;
  if (apOnline && apModeEnabled) {
    return;
  }

  Serial.println("[wifi] AP unavailable; attempting recovery without reboot");
  apOnline = false;
  if (startAccessPoint()) {
    httpServer.end();
    httpServer.begin();
    serverStarted = true;
    Serial.println("[wifi] AP and HTTP listener recovered");
  } else {
    Serial.println("[wifi] recovery failed; another attempt will occur in 5 s");
  }
}

bool isOnline() {
  return serverStarted && apOnline;
}

const char* lastError() {
  return errorMessage;
}

}  // namespace TokimiWeb
