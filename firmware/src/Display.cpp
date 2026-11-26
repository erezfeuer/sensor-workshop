#include "App.h"
#include <algorithm>
#include <qrcode.h>
using namespace logger;
namespace {
constexpr uint16_t BG = 0x0843, FG = 0xef7d, MUTED = 0x8d34, ACCENT = 0x5df2, WARN = 0xfcc0;
void text(Adafruit_ST7789 &t, int x, int y, const String &s, int size = 1, uint16_t color = FG) {
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
  tft.init(135, 240);
  tft.setRotation(3);
  tft.setTextWrap(false);
  tft.enableSleep(false);
  tft.enableDisplay(true);
  digitalWrite(TFT_BACKLITE, HIGH);
  screen = true;
  draw(true);
}
void App::draw(bool force) {
  if (!screen || (!force && now() - lastDraw < 1000))
    return;
  lastDraw = now();
  tft.fillScreen(BG);
  if (!wifi) {
    text(tft, 7, 5, String(settings.name).substring(0, 24), 1, ACCENT);
    String battery =
        sensors.reading.batteryValid ? String(sensors.reading.percent, 0) + "%" : "--%";
    text(tft, 205, 5, battery, 1, MUTED);
    tft.drawFastHLine(7, 18, 226, 0x22c7);
  }
  if (wifi) {
    QRCode qr;
    uint8_t buffer[qrcode_getBufferSize(3)];
    String payload = "WIFI:T:WPA;S:" + ssid + ";P:" + password + ";;";
    int8_t result = qrcode_initText(&qr, buffer, 3, ECC_LOW, payload.c_str());
    if (result == 0) {
      tft.fillRect(5, 5, 111, 111, ST77XX_WHITE);
      for (uint8_t y = 0; y < qr.size; y++)
        for (uint8_t x = 0; x < qr.size; x++)
          if (qrcode_getModule(&qr, x, y))
            tft.fillRect(17 + x * 3, 17 + y * 3, 3, 3, ST77XX_BLACK);
    }
    text(tft, 124, 14, "SCAN TO JOIN", 1, ACCENT);
    text(tft, 124, 41, ssid, 1);
    text(tft, 124, 55, password, 1);
    text(tft, 124, 74, "Then open:", 1, MUTED);
    text(tft, 124, 86, "192.168.4.1", 1);
    String remaining =
        calibration
            ? "Cal: " +
                  String(calibrationUntil > now() ? (calibrationUntil - now() + 999) / 1000 : 0) +
                  "s"
            : "WiFi: " + String(wifiUntil > now() ? (wifiUntil - now()) / 60000 : 0) + " min";
    text(tft, 124, 103, remaining, 1, WARN);
  } else if (page == 0) {
    text(tft, 8, 25, "CO2", 1, MUTED);
    text(tft, 8, 40, fresh() ? val(sensors.reading.co2) : "--", 4);
    text(tft, 154, 60, "ppm", 1, MUTED);
    text(tft, 8, 80,
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
    text(tft, 8, 99, state, 1, (!utc() || warming() || storage.full) ? WARN : ACCENT);
  } else if (page == 1) {
    text(tft, 8, 27, "LIGHT", 1, MUTED);
    text(tft, 8, 42, sensors.reading.lightValid ? val(sensors.reading.lux) : "--", 3);
    text(tft, 170, 57, "lux", 1, MUTED);
    text(tft, 8, 77, sensors.lightName(), 1, ACCENT);
    text(tft, 8, 94,
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
    text(tft, 8, 27,
         String(storage.count) + " records  /  " + String(storage.freeBytes() / 1024) + " KiB free",
         1);
    text(tft, 8, 45, "Storage: ~" + duration(e.storageHours), 1, ACCENT);
    text(tft, 8, 61, "Battery: ~" + duration(e.hours) + " (estimate)", 1, WARN);
    if (utc()) {
      time_t epoch = utc();
      tm t;
      gmtime_r(&epoch, &t);
      char clock[28];
      strftime(clock, sizeof(clock), "%d %b  %H:%M:%S UTC", &t);
      text(tft, 8, 79, clock, 1);
    } else
      text(tft, 8, 79, "Set clock from phone", 1, WARN);
    text(tft, 8, 97, "Hold D0: sleep | D2: wake", 1, MUTED);
  }
  if (noticeUntil > now() && !wifi) {
    tft.fillRect(0, 94, 240, 17, BG);
    text(tft, 7, 98, notice.substring(0, 37), 1, WARN);
  }
  tft.fillRect(0, 121, 240, 14, 0x1246);
  text(tft, 6, 125, "D0 View", 1);
  text(tft, 84, 125, wifi ? "D1 Done" : "D1 Phone", 1);
  text(tft, 166, 125, settings.logging ? "D2 Pause" : "D2 Start", 1);
}
