#include "LoggerCore.h"
#include <algorithm>
#include <cstring>
namespace logger {
uint8_t crc8(const uint8_t *b, size_t n) {
  uint8_t c = 0xff;
  while (n--) {
    c ^= *b++;
    for (int i = 0; i < 8; i++)
      c = (c & 0x80) ? (c << 1) ^ 0x31 : c << 1;
  }
  return c;
}
uint32_t crc32(const void *data, size_t n) {
  const auto *b = static_cast<const uint8_t *>(data);
  uint32_t c = 0xffffffff;
  while (n--) {
    c ^= *b++;
    for (int i = 0; i < 8; i++)
      c = (c >> 1) ^ ((0 - (c & 1)) & 0xedb88320);
  }
  return ~c;
}
void seal(Record &r) {
  r.magic = RecordMagic;
  r.crc = crc32(&r, offsetof(Record, crc));
}
bool valid(const Record &r) {
  return r.magic == RecordMagic && r.crc == crc32(&r, offsetof(Record, crc));
}
RecordCheck checkRecord(const Record &r, uint32_t previous, uint32_t offset, uint32_t size) {
  if (valid(r) && r.sequence > previous)
    return RecordCheck::Good;
  return uint64_t(offset) + sizeof(r) == size ? RecordCheck::TornTail : RecordCheck::Corrupt;
}
float decodeFloat(uint16_t h, uint16_t l) {
  uint32_t raw = (uint32_t(h) << 16) | l;
  float f;
  std::memcpy(&f, &raw, 4);
  return f;
}
bool validUtc(uint32_t e) {
  return e >= 1577836800u && e < 2145916800u;
} // 2020..2037: pinned Arduino core uses signed 32-bit time_t
const char *validate(const Settings &s) {
  if (s.intervalS < 5 || s.intervalS > 86400)
    return "Log interval must be 5 seconds to 24 hours.";
  if (s.sensorIntervalS != 2 && s.sensorIntervalS != 5 && s.sensorIntervalS != 15 &&
      s.sensorIntervalS != 30 && s.sensorIntervalS != 60)
    return "Choose a supported sensor cadence.";
  if (s.intervalS < s.sensorIntervalS)
    return "Log interval must be at least the CO2 sensor cadence.";
  if (s.channels == 0 || (s.channels & ~All))
    return "Select at least one valid channel.";
  if (s.screenSeconds < 10 || s.screenSeconds > 300)
    return "Screen timeout must be 10 to 300 seconds.";
  if (s.wifiMinutes < 2 || s.wifiMinutes > 60)
    return "Wi-Fi session must be 2 to 60 minutes.";
  if (s.temperatureOffsetCenti > 2000 || s.altitudeM > 3000)
    return "Temperature offset must be 0–20 C; altitude 0–3000 m.";
  if (s.batteryMah < 100 || s.batteryMah > 20000)
    return "Battery capacity must be 100–20000 mAh.";
  if (s.logging > 1 || s.asc > 1 || s.calibrationDue > 1)
    return "Invalid switch value.";
  size_t len = 0;
  for (; len < sizeof(s.name) && s.name[len]; len++)
    if (uint8_t(s.name[len]) < 32 || uint8_t(s.name[len]) > 126)
      return "Use a short plain-text device name.";
  if (!len || len == sizeof(s.name))
    return "Device name must be 1–24 characters.";
  return nullptr;
}
uint64_t advanceDeadline(uint64_t due, uint64_t now, uint32_t sec) {
  const uint64_t step = uint64_t(sec) * 1000;
  if (!step)
    return now;
  if (due > now)
    return due;
  return due + ((now - due) / step + 1) * step;
}
uint32_t calibrationWaitMs(uint16_t s) {
  return std::max(360000u, uint32_t(s) * 5000u);
}
const char *eventName(uint16_t e) {
  switch (e) {
  case Sample:
    return "sample";
  case ClockSet:
    return "clock_set";
  case ConfigChanged:
    return "settings";
  case Started:
    return "start";
  case Paused:
    return "pause";
  case Calibrated:
    return "calibration";
  case Boot:
    return "boot";
  default:
    return "unknown";
  }
}
Estimate estimate(const PowerInputs &p, uint32_t free) {
  const double interval = std::max(5., p.intervalS),
               cadence = std::max(2., std::min(60., p.sensorIntervalS));
  // Interpolation through Sensirion's 19 mA @2s and 5.6 mA @30s. Not a measured curve.
  const double sensor = 4.642857142857 + 28.714285714286 / cadence;
  const double wifi = std::max(0., std::min(1., p.wifiMinutesPerDay / 1440.));
  const double screen = std::max(0., std::min(1. - wifi, p.screenMinutesPerDay / 1440.));
  const double wake = (1. - wifi - screen) * std::max(0., std::min(1., p.wakeSeconds / interval));
  const double idle = std::max(0., 1. - wifi - screen - wake);
  const double ma = sensor + p.breakoutMa + p.rtcMa + p.lightSleepMa + p.lcdSleepMa +
                    idle * p.boardSleepMa + wake * p.cpuMa + screen * (p.cpuMa + p.screenMa) +
                    wifi * p.wifiBoardMa;
  const double capacity = std::max(0., p.capacityMah) *
                          std::max(0., std::min(1., p.usableFraction)) *
                          std::max(0., std::min(100., p.chargePercent)) / 100.;
  const double hours = ma > 0 ? capacity / ma : 0;
  const uint32_t records = free > StorageReserve ? (free - StorageReserve) / sizeof(Record) : 0;
  return {sensor, ma, hours, hours / 1.5, hours / .7, records * interval / 3600., records};
}

} // namespace logger
