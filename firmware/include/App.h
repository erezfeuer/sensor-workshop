#pragma once
#include "Sensors.h"
#include "Storage.h"
#include <Adafruit_ST7789.h>
#include <Arduino.h>
#include <ArduinoJson.h>
#include <DNSServer.h>
#include <Preferences.h>
#include <WebServer.h>
#include <esp_timer.h>
struct Retained {
  uint32_t magic = 0, session = 0, storeBytes = 0, storeSequence = 0;
  uint64_t baseMs = 0, sleepWallUs = 0, nextLogMs = 0, scdStartedMs = 0;
  bool railOn = false, scdRunning = false, clockTrusted = false;
  Reading reading;
};
extern Retained retained;
class App {
public:
  logger::Settings settings;
  Preferences prefs;
  Sensors sensors;
  Storage storage;
  WebServer server{80};
  DNSServer dns;
  Adafruit_ST7789 tft{TFT_CS, TFT_DC, TFT_RST};
  bool wifi = false, screen = false, clockTrusted = false, rtcValid = false, calibration = false,
       configured = false;
  uint64_t activeUntil = 0, wifiUntil = 0, calibrationUntil = 0, lastDraw = 0, bootAt = 0;
  uint32_t resetReason = 0;
  int page = 0;
  uint32_t calibrationSamples = 0, calibrationErrors = 0;
  uint64_t calibrationLastReading = 0, calibrationExpires = 0;
  String ssid, password, token, notice;
  uint64_t noticeUntil = 0;
  uint64_t now() const {
    return retained.baseMs + uint64_t(esp_timer_get_time()) / 1000;
  }
  uint32_t utc() const;
  bool fresh() const;
  bool warming() const;
  void begin();
  void loop();
  void sleep();
  bool save(const logger::Settings &value);
  bool changeSettings(logger::Settings value, String &error);
  void setLogging(bool enabled);
  bool setClock(uint32_t epoch, String &error);
  bool event(uint16_t kind, uint32_t auxiliary = 0);
  logger::Record makeRecord(uint16_t kind = logger::Sample);
  void toast(const String &text);
  void startWifi();
  void stopWifi();
  void setupRoutes();
  void serviceWeb();
  void draw(bool force = false);
  void startScreen();
  void statusJson(JsonDocument &doc);

private:
  void buttons();
  void logIfDue();
};
extern App app;
