#pragma once
#include <Adafruit_MAX1704X.h>
#include <Adafruit_TSL2591.h>
#include <Adafruit_VEML7700.h>
#include <Arduino.h>
#include <LoggerCore.h>
#include <RTClib.h>
#include <Wire.h>
struct Reading {
  float co2 = NAN, temperature = NAN, humidity = NAN, lux = NAN, volts = NAN, percent = NAN;
  uint64_t co2At = 0;
  bool co2Valid = false, lightValid = false, batteryValid = false, saturated = false;
};
class Sensors {
public:
  RTC_DS3231 rtc;
  bool scd = false, rtcPresent = false, fuel = false, tslPresent = false, vemlPresent = false;
  uint32_t errors = 0;
  Reading reading;
  bool begin(const logger::Settings &settings, bool continuousRetained);
  void poll(uint64_t now, const logger::Settings &settings);
  bool configure(const logger::Settings &settings);
  bool forceCalibration(uint16_t ppm);
  bool scdWord(uint16_t command, uint16_t &out);
  bool scdWrite(uint16_t command, uint16_t value);
  bool stopScd();
  void sleepLight();
  bool lightBusy() const {
    return lightPending;
  }
  const char *lightName() const {
    return tslPresent ? "TSL2591" : vemlPresent ? "VEML7700" : "Missing";
  }

private:
  Adafruit_TSL2591 tsl{2591};
  Adafruit_VEML7700 veml;
  Adafruit_MAX17048 gauge;
  uint64_t lastPoll = 0, lightReadyAt = 0;
  uint8_t gain = 1, lightAttempts = 0;
  bool lightPending = false;
  void startLight(uint64_t now);
  void finishLight(uint64_t now);
  bool lightWord(uint8_t reg, uint16_t &value);
  bool words(uint16_t command, uint16_t *out, size_t n);
  bool command(uint16_t cmd);
  bool ping(uint8_t address);
};
