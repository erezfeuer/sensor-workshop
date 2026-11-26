#include "App.h"
#include <algorithm>
#include <cstring>
#include <new>
#include <qrcode.h>
using namespace logger;
namespace {
constexpr uint16_t BG = 0x0843, FG = 0xef7d, MUTED = 0x8d34, ACCENT = 0x5df2, WARN = 0xfcc0;
constexpr uint16_t Width = 240, Height = 135;
constexpr size_t FrameBytes = Width * Height * sizeof(uint16_t);
// Allocate only when the screen is used; timer-only wakes need no frame buffers.
GFXcanvas16 *canvas = nullptr;
uint16_t *shown = nullptr;
bool panelValid = false;
uint32_t framesSent = 0, framesSkipped = 0, renderUs = 0, presentUs = 0;
uint32_t maxRenderUs = 0, maxPresentUs = 0, pixelsSent = 0;

void present(Adafruit_ST7789 &panel) {
  const uint32_t started = micros();
  uint16_t *pixels = canvas->getBuffer();
  pixelsSent = 0;
  bool writing = false;
  for (uint16_t y = 0; y < Height;) {
    auto changed = [&](uint16_t row) {
      return !panelValid || !shown ||
             memcmp(pixels + row * Width, shown + row * Width, Width * sizeof(uint16_t)) != 0;
    };
    if (!changed(y)) {
      ++y;
      continue;
    }
    const uint16_t first = y++;
    while (y < Height && changed(y))
      ++y;
    if (!writing) {
      panel.startWrite();
      writing = true;
    }
    const uint32_t count = uint32_t(y - first) * Width;
    panel.setAddrWindow(0, first, Width, y - first);
    // Write completed pixels, including their backgrounds, with no visible erase.
    panel.writePixels(pixels + first * Width, count);
    if (shown)
      memcpy(shown + first * Width, pixels + first * Width, count * sizeof(uint16_t));
    pixelsSent += count;
  }
  if (writing) {
    panel.endWrite();
    ++framesSent;
  } else {
    ++framesSkipped;
  }
  panelValid = true;
  presentUs = micros() - started;
  maxPresentUs = std::max(maxPresentUs, presentUs);
}
void text(Adafruit_GFX &t, int x, int y, const String &s, int size = 1, uint16_t color = FG) {
  t.setCursor(x, y);
  t.setTextSize(size);
  t.setTextColor(color, BG);
  t.print(s);
}
String val(float f, int decimals = 0) {
  return isfinite(f) ? String(f, decimals) : String("--");
}
String duration(double hours) {
  if (hours >= 48)
    return String(hours / 24, 1) + " d";
  return String(hours, 0) + " h";
}
} // namespace
void App::startScreen() {
  if (screen)
    return;
  if (!canvas) {
    canvas = new (std::nothrow) GFXcanvas16(Width, Height);
    if (!canvas || !canvas->getBuffer()) {
      delete canvas;
      canvas = nullptr;
      Serial.println("Screen buffer unavailable; logger remains active.");
      return;
    }
    canvas->setTextWrap(false);
    shown = static_cast<uint16_t *>(ps_malloc(FrameBytes));
    if (!shown)
      shown = static_cast<uint16_t *>(malloc(FrameBytes));
    // If history allocation fails, full buffered transfers still avoid blanking.
  }
  digitalWrite(TFT_BACKLITE, LOW);
  tft.init(135, 240);
  tft.setRotation(3);
  tft.setTextWrap(false);
  tft.enableSleep(false);
  tft.enableDisplay(true);
  panelValid = false;
  screen = true;
  draw(true);
  digitalWrite(TFT_BACKLITE, HIGH);
}
void App::draw(bool force) {
  if (!screen || (!force && now() - lastDraw < 1000))
    return;
  lastDraw = now();
  const uint32_t started = micros();
  auto &frame = *canvas;
  frame.fillScreen(BG);
  if (!wifi) {
    text(frame, 7, 5, String(settings.name).substring(0, 24), 1, ACCENT);
    String battery =
        sensors.reading.batteryValid ? String(sensors.reading.percent, 0) + "%" : "--%";
    text(frame, 205, 5, battery, 1, MUTED);
    frame.drawFastHLine(7, 18, 226, 0x22c7);
  }
  if (wifi) {
    static QRCode qr;
    static uint8_t buffer[(29 * 29 + 7) / 8]; // Version 3 QR, cached for this boot.
    static String encoded;
    static int8_t result = -1;
    String payload = "WIFI:T:WPA;S:" + ssid + ";P:" + password + ";;";
    if (payload != encoded) {
      result = qrcode_initText(&qr, buffer, 3, ECC_LOW, payload.c_str());
      encoded = payload;
    }
    if (result == 0) {
      frame.fillRect(5, 5, 111, 111, ST77XX_WHITE);
      for (uint8_t y = 0; y < qr.size; y++)
        for (uint8_t x = 0; x < qr.size; x++)
          if (qrcode_getModule(&qr, x, y))
            frame.fillRect(17 + x * 3, 17 + y * 3, 3, 3, ST77XX_BLACK);
    }
    text(frame, 124, 14, "SCAN TO JOIN", 1, ACCENT);
    text(frame, 124, 41, ssid, 1);
    text(frame, 124, 55, password, 1);
    text(frame, 124, 74, "Then open:", 1, MUTED);
    text(frame, 124, 86, "192.168.4.1", 1);
    String remaining =
        calibration
            ? "Cal: " +
                  String(calibrationUntil > now() ? (calibrationUntil - now() + 999) / 1000 : 0) +
                  "s"
            : "WiFi: " + String(wifiUntil > now() ? (wifiUntil - now()) / 60000 : 0) + " min";
    text(frame, 124, 103, remaining, 1, WARN);
  } else if (page == 0) {
    text(frame, 8, 25, "CO2", 1, MUTED);
    text(frame, 8, 40, fresh() ? val(sensors.reading.co2) : "--", 4);
    text(frame, 154, 60, "ppm", 1, MUTED);
    text(frame, 8, 80,
         (fresh() ? val(sensors.reading.temperature, 1) : "--") + " C   " +
             (fresh() ? val(sensors.reading.humidity, 0) : "--") + "% RH",
         1);
    String state = !storage.healthy          ? "Storage needs attention"
                   : storage.full            ? "Storage full"
                   : !utc()                  ? "Set clock: D1 phone"
                   : warming()               ? "CO2 warming up"
                   : settings.calibrationDue ? "Review CO2 calibration"
                   : settings.logging        ? "Logging every " + String(settings.intervalS) + "s"
                                             : "Paused - D2 to start";
    text(frame, 8, 99, state, 1, (!utc() || warming() || storage.full) ? WARN : ACCENT);
  } else if (page == 1) {
    text(frame, 8, 27, "LIGHT", 1, MUTED);
    text(frame, 8, 42, sensors.reading.lightValid ? val(sensors.reading.lux) : "--", 3);
    text(frame, 170, 57, "lux", 1, MUTED);
    text(frame, 8, 77, sensors.lightName(), 1, ACCENT);
    text(frame, 8, 94,
         sensors.reading.saturated ? "Light sensor saturated"
                                   : "Battery " + val(sensors.reading.volts, 2) + " V",
         1, MUTED);
  } else {
    PowerInputs p;
    p.capacityMah = settings.batteryMah;
    p.intervalS = settings.intervalS;
    p.sensorIntervalS = settings.sensorIntervalS;
    if (sensors.reading.batteryValid)
      p.chargePercent = sensors.reading.percent;
    auto e = estimate(p, storage.freeBytes());
    text(frame, 8, 27,
         String(storage.count) + " records  /  " + String(storage.freeBytes() / 1024) + " KiB free",
         1);
    text(frame, 8, 45, "Storage: ~" + duration(e.storageHours), 1, ACCENT);
    text(frame, 8, 61, "Battery: ~" + duration(e.hours) + " (estimate)", 1, WARN);
    if (utc()) {
      time_t epoch = utc();
      tm t;
      gmtime_r(&epoch, &t);
      char clock[28];
      strftime(clock, sizeof(clock), "%d %b  %H:%M:%S UTC", &t);
      text(frame, 8, 79, clock, 1);
    } else
      text(frame, 8, 79, "Set clock from phone", 1, WARN);
    text(frame, 8, 97, "Hold D0: sleep | D2: wake", 1, MUTED);
  }
  if (noticeUntil > now() && !wifi) {
    frame.fillRect(0, 94, 240, 17, BG);
    text(frame, 7, 98, notice.substring(0, 37), 1, WARN);
  }
  frame.fillRect(0, 121, 240, 14, 0x1246);
  text(frame, 6, 125, "D0 View", 1);
  text(frame, 84, 125, wifi ? "D1 Done" : "D1 Phone", 1);
  text(frame, 166, 125, settings.logging ? "D2 Pause" : "D2 Start", 1);
  renderUs = micros() - started;
  maxRenderUs = std::max(maxRenderUs, renderUs);
  present(tft);
}

void App::displayStatus(JsonObject d) const {
  d["on"] = screen;
  d["buffered"] = canvas && canvas->getBuffer();
  d["differential"] = shown != nullptr;
  d["buffer_bytes"] = (canvas ? FrameBytes : 0) + (shown ? FrameBytes : 0);
  d["frames_sent"] = framesSent;
  d["frames_skipped"] = framesSkipped;
  d["last_pixels_sent"] = pixelsSent;
  d["last_render_us"] = renderUs;
  d["last_present_us"] = presentUs;
  d["max_render_us"] = maxRenderUs;
  d["max_present_us"] = maxPresentUs;
  d["free_heap_bytes"] = ESP.getFreeHeap();
  d["free_psram_bytes"] = ESP.getFreePsram();
}
