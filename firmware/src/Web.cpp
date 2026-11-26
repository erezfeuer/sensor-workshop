#include "App.h"
#include "web_asset.h"
#include <WiFi.h>
#include <algorithm>
using namespace logger;
static void reply(int code, const String &message) {
  StaticJsonDocument<512> d;
  d["ok"] = code < 400;
  d["message"] = message;
  String out;
  serializeJson(d, out);
  app.server.send(code, "application/json", out);
}
static bool body(JsonDocument &doc) {
  if (!app.wifi || app.server.header("X-Workshop-Token") != app.token) {
    reply(403, "Reconnect to this device and reload the page.");
    return false;
  }
  if (!app.server.hasArg("plain") || app.server.arg("plain").length() > 2048 ||
      deserializeJson(doc, app.server.arg("plain")) || !doc.is<JsonObject>()) {
    reply(400, "Invalid request.");
    return false;
  }
  return true;
}
static void number(JsonObject o, const char *key, float value, bool good) {
  if (good && isfinite(value))
    o[key] = value;
  else
    o[key] = nullptr;
}
void App::statusJson(JsonDocument &d) {
  d["version"] = FW_VERSION;
  d["name"] = settings.name;
  d["token"] = token;
  d["utc"] = utc();
  d["uptime_s"] = now() / 1000;
  d["session"] = retained.session;
  d["logging"] = bool(settings.logging);
  d["warming"] = warming();
  d["calibration_due"] = bool(settings.calibrationDue);
  d["rtc"] = rtcValid ? "ready" : sensors.rtcPresent ? "needs_time" : "missing";
  d["clock_source"] = clockTrusted ? (rtcValid ? "RTC" : "phone, until power loss") : "unset";
  d["sensor"] = sensors.scd ? "SCD30" : "missing";
  d["light_sensor"] = sensors.lightName();
  d["sensor_errors"] = sensors.errors;
  d["reset_reason"] = resetReason;
  auto live = d.createNestedObject("live");
  auto &r = sensors.reading;
  number(live, "co2", r.co2, fresh());
  number(live, "temperature", r.temperature, fresh());
  number(live, "humidity", r.humidity, fresh());
  number(live, "lux", r.lux, r.lightValid);
  number(live, "volts", r.volts, r.batteryValid);
  number(live, "percent", r.percent, r.batteryValid);
  live["light_saturated"] = r.saturated;
  live["co2_age_bound_s"] = r.co2Valid ? (now() - r.co2At) / 1000 + settings.sensorIntervalS : 0;
  auto cfg = d.createNestedObject("settings");
  cfg["name"] = settings.name;
  cfg["interval_s"] = settings.intervalS;
  cfg["sensor_interval_s"] = settings.sensorIntervalS;
  cfg["screen_seconds"] = settings.screenSeconds;
  cfg["wifi_minutes"] = settings.wifiMinutes;
  cfg["channels"] = settings.channels;
  cfg["asc"] = bool(settings.asc);
  cfg["temperature_offset_centi"] = settings.temperatureOffsetCenti;
  cfg["altitude_m"] = settings.altitudeM;
  cfg["battery_mah"] = settings.batteryMah;
  cfg["revision"] = settings.revision;
  auto fs = d.createNestedObject("storage");
  fs["mounted"] = storage.mounted;
  fs["healthy"] = storage.healthy;
  fs["full"] = storage.full;
  fs["records"] = storage.count;
  fs["sequence"] = storage.sequence;
  fs["free_bytes"] = storage.freeBytes();
  fs["total_bytes"] = storage.totalBytes();
  fs["record_bytes"] = sizeof(Record);
  fs["reserve_bytes"] = StorageReserve;
  fs["recovered_bytes"] = storage.recoveredBytes;
  fs["error"] = storage.error;
  auto net = d.createNestedObject("wifi");
  net["ssid"] = ssid;
  net["seconds_left"] = wifiUntil > now() ? (wifiUntil - now()) / 1000 : 0;
  net["clients"] = WiFi.softAPgetStationNum();
  auto cal = d.createNestedObject("calibration");
  cal["active"] = calibration;
  cal["seconds_left"] =
      calibration && calibrationUntil > now() ? (calibrationUntil - now() + 999) / 1000 : 0;
  cal["ready"] = calibration && now() >= calibrationUntil && fresh() && calibrationSamples >= 5;
  PowerInputs p;
  p.capacityMah = settings.batteryMah;
  p.intervalS = settings.intervalS;
  p.sensorIntervalS = settings.sensorIntervalS;
  auto e = estimate(p, storage.freeBytes());
  auto power = d.createNestedObject("estimate");
  power["average_ma"] = e.averageMa;
  power["sensor_ma"] = e.sensorMa;
  power["full_hours"] = e.hours;
  power["low_hours"] = e.lowHours;
  power["high_hours"] = e.highHours;
  power["storage_hours"] = e.storageHours;
  power["remaining_records"] = e.records;
  power["measured"] = false;
}
void App::startWifi() {
  if (wifi) {
    wifiUntil = now() + uint64_t(settings.wifiMinutes) * 60000;
    return;
  }
  WiFi.persistent(false);
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(IPAddress(192, 168, 4, 1), IPAddress(192, 168, 4, 1),
                    IPAddress(255, 255, 255, 0));
  if (!WiFi.softAP(ssid.c_str(), password.c_str(), 1, false, 3)) {
    WiFi.mode(WIFI_OFF);
    toast("Wi-Fi could not start");
    return;
  }
  wifi = true;
  wifiUntil = now() + uint64_t(settings.wifiMinutes) * 60000;
  dns.start(53, "*", WiFi.softAPIP());
  server.begin();
  startScreen();
  draw(true);
}
void App::stopWifi() {
  if (!wifi)
    return;
  calibration = false;
  server.stop();
  dns.stop();
  WiFi.softAPdisconnect(true);
  WiFi.mode(WIFI_OFF);
  wifi = false;
  activeUntil = now() + uint64_t(settings.screenSeconds) * 1000;
  toast("Wi-Fi off");
}
void App::serviceWeb() {
  if (calibration) {
    if (!fresh() || sensors.errors != calibrationErrors) {
      calibrationUntil = now() + calibrationWaitMs(settings.sensorIntervalS);
      calibrationSamples = 0;
      calibrationErrors = sensors.errors;
      wifiUntil = std::min(calibrationUntil + 600000, calibrationExpires);
    }
    if (fresh() && sensors.reading.co2At != calibrationLastReading) {
      calibrationLastReading = sensors.reading.co2At;
      calibrationSamples++;
    }
    if (now() > calibrationUntil + 600000 || now() >= calibrationExpires) {
      calibration = false;
      wifiUntil = now() + 60000;
      toast("Calibration timed out");
    }
  }
  if (wifi) {
    dns.processNextRequest();
    server.handleClient();
  }
}
static void csvNumber(String &out, float f) {
  if (isfinite(f))
    out += String(f, 3);
}
static String csvRow(const Record &r) {
  String s;
  s.reserve(200);
  s += String(r.sequence) + "," + eventName(r.event) + "," + String(r.session) + ",";
  if (r.flags & TimeValid) {
    time_t t = r.utc;
    tm parts;
    gmtime_r(&t, &parts);
    char iso[25];
    strftime(iso, sizeof(iso), "%Y-%m-%dT%H:%M:%SZ", &parts);
    s += iso;
  }
  s += "," + String(r.uptimeS) + "," + String(r.revision) + "," + String(r.channels) + "," +
       String(r.flags) + ",";
  if (r.event == Sample) {
    csvNumber(s, r.co2);
    s += ",";
    csvNumber(s, r.temperature);
    s += ",";
    csvNumber(s, r.humidity);
    s += ",";
    csvNumber(s, r.lux);
    s += ",";
    csvNumber(s, r.volts);
    s += ",";
    csvNumber(s, r.percent);
  } else
    s += ",,,,,";
  s += ",";
  if (r.co2AgeBoundS != 65535)
    s += String(r.co2AgeBoundS);
  s += "," + String(r.auxiliary) + "\r\n";
  return s;
}
void App::setupRoutes() {
  const char *headers[] = {"X-Workshop-Token", "Origin"};
  server.collectHeaders(headers, 2);
  server.on("/", HTTP_GET, [this]() {
    server.sendHeader("Cache-Control", "no-store");
    server.sendHeader("Content-Encoding", "gzip");
    server.send_P(200, "text/html", reinterpret_cast<const char *>(WEB_GZ), sizeof(WEB_GZ));
  });
  server.on("/api/status", HTTP_GET, [this]() {
    DynamicJsonDocument d(4096);
    statusJson(d);
    String s;
    serializeJson(d, s);
    server.sendHeader("Cache-Control", "no-store");
    server.send(200, "application/json", s);
  });
  server.on("/api/clock", HTTP_POST, [this]() {
    StaticJsonDocument<256> d;
    if (!body(d))
      return;
    if (!d["utc"].is<uint32_t>()) {
      reply(400, "Missing phone time.");
      return;
    }
    String error;
    if (!setClock(d["utc"], error)) {
      reply(400, error);
      return;
    }
    reply(200, rtcValid ? "RTC set from this phone."
                        : "Clock set; RTC missing. Time will be lost if power is removed.");
  });
  server.on("/api/logging", HTTP_POST, [this]() {
    StaticJsonDocument<256> d;
    if (!body(d))
      return;
    if (!d["enabled"].is<bool>() || calibration) {
      reply(409, "Choose start/pause after calibration is finished.");
      return;
    }
    bool wanted = d["enabled"];
    setLogging(wanted);
    reply(settings.logging == wanted ? 200 : 500, notice);
  });
  server.on("/api/settings", HTTP_POST, [this]() {
    StaticJsonDocument<2048> d;
    if (!body(d))
      return;
    if (!d["expected_revision"].is<uint16_t>() ||
        d["expected_revision"].as<uint16_t>() != settings.revision) {
      reply(409, "Settings changed since this form was opened. Reload settings and try again.");
      return;
    }
    Settings next = settings;
    const char *uints[] = {"interval_s",   "sensor_interval_s", "screen_seconds",
                           "wifi_minutes", "channels",          "temperature_offset_centi",
                           "altitude_m",   "battery_mah"};
    for (const char *k : uints)
      if (!d[k].is<uint32_t>() || d[k].as<uint32_t>() > 100000) {
        reply(400, String("Invalid ") + k);
        return;
      }
    for (const char *k : {"sensor_interval_s", "screen_seconds", "wifi_minutes", "channels",
                          "temperature_offset_centi", "altitude_m"})
      if (d[k].as<uint32_t>() > 65535) {
        reply(400, String("Out of range: ") + k);
        return;
      }
    if (!d["name"].is<const char *>() || strlen(d["name"]) > 24 || !d["asc"].is<bool>()) {
      reply(400, "Invalid name or calibration switch.");
      return;
    }
    strlcpy(next.name, d["name"], sizeof(next.name));
    next.intervalS = d["interval_s"];
    next.sensorIntervalS = d["sensor_interval_s"];
    next.screenSeconds = d["screen_seconds"];
    next.wifiMinutes = d["wifi_minutes"];
    next.channels = d["channels"];
    next.temperatureOffsetCenti = d["temperature_offset_centi"];
    next.altitudeM = d["altitude_m"];
    next.batteryMah = d["battery_mah"];
    next.asc = d["asc"].as<bool>();
    if (next.asc && !settings.asc && d["asc_acknowledged"] != true) {
      reply(400, "Confirm that this sensor will see fresh air every day before enabling ASC.");
      return;
    }
    if (next.sensorIntervalS != settings.sensorIntervalS && d["cadence_acknowledged"] != true) {
      reply(400, "Changing sensor cadence requires recalibration and temperature-offset review.");
      return;
    }
    String error;
    if (!changeSettings(next, error)) {
      reply(400, error);
      return;
    }
    reply(200, "Settings saved.");
  });
  server.on("/api/wifi/extend", HTTP_POST, [this]() {
    StaticJsonDocument<128> d;
    if (!body(d))
      return;
    wifiUntil = now() + uint64_t(settings.wifiMinutes) * 60000;
    reply(200, "Wi-Fi session extended.");
  });
  server.on("/api/calibration/start", HTTP_POST, [this]() {
    StaticJsonDocument<256> d;
    if (!body(d))
      return;
    if (!sensors.scd) {
      reply(409, "Connect the CO2 sensor first.");
      return;
    }
    calibration = true;
    calibrationExpires = now() + 1200000;
    calibrationSamples = 0;
    calibrationLastReading = sensors.reading.co2At;
    calibrationErrors = sensors.errors;
    calibrationUntil = now() + calibrationWaitMs(settings.sensorIntervalS);
    wifiUntil = std::min(calibrationUntil + 600000, calibrationExpires);
    reply(200, "Stabilisation started. Calibration is not applied automatically.");
    draw(true);
  });
  server.on("/api/calibration/cancel", HTTP_POST, [this]() {
    StaticJsonDocument<128> d;
    if (!body(d))
      return;
    calibration = false;
    reply(200, "Calibration cancelled; no correction applied.");
  });
  server.on("/api/calibration/apply", HTTP_POST, [this]() {
    StaticJsonDocument<256> d;
    if (!body(d))
      return;
    if (!calibration || now() < calibrationUntil || !fresh() || calibrationSamples < 5) {
      reply(409, "Wait for stabilisation and a fresh CO2 reading.");
      return;
    }
    if (!d["reference_ppm"].is<uint16_t>() || d["reference_ppm"].as<uint16_t>() < 400 ||
        d["reference_ppm"].as<uint16_t>() > 2000 || d["confirmed"] != true) {
      reply(400, "Enter a known reference between 400 and 2000 ppm and confirm stable conditions.");
      return;
    }
    uint16_t ppm = d["reference_ppm"];
    if (!sensors.forceCalibration(ppm)) {
      reply(500, "Sensor did not confirm calibration. Check the sensor before retrying.");
      return;
    }
    settings.calibrationDue = 0;
    calibration = false;
    const bool recorded = event(Calibrated, ppm);
    if (!save(settings)) {
      reply(500, "Calibration was applied, but the settings save failed.");
      return;
    }
    reply(200, recorded ? "Calibration applied and recorded."
                        : "Calibration applied. Storage is unavailable; no event was recorded.");
  });
  server.on("/api/storage/erase", HTTP_POST, [this]() {
    StaticJsonDocument<256> d;
    if (!body(d))
      return;
    if (d["confirmation"] != "ERASE" || settings.logging || calibration) {
      reply(409, "Pause logging, cancel calibration and type ERASE first.");
      return;
    }
    if (!storage.erase()) {
      reply(500, storage.error);
      return;
    }
    retained.storeBytes = 0;
    retained.storeSequence = 0;
    reply(200, "Log erased. Settings and RTC are unchanged.");
  });
  server.on("/api/download", HTTP_GET, [this]() {
    if (!storage.mounted) {
      reply(503, storage.error);
      return;
    }
    File f = storage.open();
    if (!f) {
      reply(503, "Log is unavailable.");
      return;
    }
    server.sendHeader("Content-Disposition", "attachment; filename=\"sensor-workshop.csv\"");
    server.sendHeader("Cache-Control", "no-store");
    server.setContentLength(CONTENT_LENGTH_UNKNOWN);
    server.send(200, "text/csv", "");
    uint32_t remaining = f.size();
    String block = "sequence,event,session_id,timestamp_utc,uptime_s,settings_revision,channel_"
                   "mask,quality_flags,co2_ppm,temperature_c,humidity_pct,illuminance_lux,battery_"
                   "v,battery_pct,co2_age_bound_s,event_value\r\n";
    Record r;
    while (remaining >= sizeof(r) && server.client().connected()) {
      if (f.read(reinterpret_cast<uint8_t *>(&r), sizeof(r)) != sizeof(r) || !valid(r))
        break;
      remaining -= sizeof(r);
      block += csvRow(r);
      if (block.length() > 1200) {
        server.sendContent(block);
        block = "";
        sensors.poll(now(), settings);
        logIfDue();
        yield();
      }
    }
    f.close();
    if (block.length())
      server.sendContent(block);
    server.sendContent("");
  });
  server.on("/api/download/raw", HTTP_GET, [this]() {
    if (!storage.mounted) {
      reply(503, storage.error);
      return;
    }
    File f = storage.open();
    if (!f) {
      reply(503, "Log is unavailable.");
      return;
    }
    server.sendHeader("Content-Disposition", "attachment; filename=\"sensor-workshop.bin\"");
    server.sendHeader("Cache-Control", "no-store");
    server.setContentLength(CONTENT_LENGTH_UNKNOWN);
    server.send(200, "application/octet-stream", "");
    uint32_t remaining = f.size();
    char block[1024];
    while (remaining && server.client().connected()) {
      size_t size =
          f.read(reinterpret_cast<uint8_t *>(block), std::min(remaining, uint32_t(sizeof(block))));
      if (!size)
        break;
      remaining -= size;
      server.sendContent(block, size);
      sensors.poll(now(), settings);
      logIfDue();
      yield();
    }
    f.close();
    server.sendContent("");
  });
  server.on("/api/history", HTTP_GET, [this]() {
    if (!storage.mounted) {
      reply(503, storage.error);
      return;
    }
    File f = storage.open();
    uint32_t total = f.size() / sizeof(Record), stride = std::max(1u, (total + 239) / 240);
    Record r;
    server.sendHeader("Cache-Control", "no-store");
    server.setContentLength(CONTENT_LENGTH_UNKNOWN);
    server.send(200, "application/json", "");
    String block = "{\"points\":[";
    bool first = true;
    for (uint32_t i = 0; i < total; i++) {
      if (f.read(reinterpret_cast<uint8_t *>(&r), sizeof(r)) != sizeof(r) || !valid(r))
        break;
      if (r.event != Sample || ((i % stride) != 0 && i + 1 != total))
        continue;
      StaticJsonDocument<384> d;
      d["sequence"] = r.sequence;
      d["utc"] = r.utc;
      d["session"] = r.session;
      d["uptime_s"] = r.uptimeS;
      d["flags"] = r.flags;
      d["co2"] = r.co2;
      d["temperature"] = r.temperature;
      d["humidity"] = r.humidity;
      d["lux"] = r.lux;
      d["percent"] = r.percent;
      if (!first)
        block += ",";
      first = false;
      serializeJson(d, block);
      if (block.length() > 1200) {
        server.sendContent(block);
        block = "";
        sensors.poll(now(), settings);
        logIfDue();
        yield();
      }
    }
    f.close();
    block += String("],\"total_records\":") + total + ",\"stride\":" + stride + "}";
    server.sendContent(block);
    server.sendContent("");
  });
  server.onNotFound([this]() {
    if (server.uri().startsWith("/api/")) {
      reply(404, "Unknown endpoint.");
      return;
    }
    server.sendHeader("Location", "http://192.168.4.1/", true);
    server.send(302, "text/plain", "Open http://192.168.4.1/");
  });
}
