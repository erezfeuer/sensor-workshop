#pragma once
#include <cmath>
#include <cstddef>
#include <cstdint>
namespace logger {
constexpr uint32_t RecordMagic = 0x31574c53; // SLW1, little endian
constexpr uint32_t StorageReserve = 32768;
enum Channel : uint16_t {
  CO2 = 1,
  Temperature = 2,
  Humidity = 4,
  Light = 8,
  Battery = 16,
  All = 31
};
enum Flag : uint16_t {
  TimeValid = 1,
  Warming = 2,
  ScdMissing = 4,
  LightMissing = 8,
  BatteryMissing = 16,
  LightSaturated = 32,
  CalibrationDue = 64,
  Stale = 128,
  Calibrating = 256
};
enum Event : uint16_t {
  Sample = 0,
  ClockSet = 1,
  ConfigChanged = 2,
  Started = 3,
  Paused = 4,
  Calibrated = 5,
  Boot = 6
};
struct Settings {
  uint32_t intervalS = 60;
  uint16_t sensorIntervalS = 2, screenSeconds = 45, wifiMinutes = 10, channels = All;
  uint16_t temperatureOffsetCenti = 0, altitudeM = 0, revision = 1;
  uint8_t logging = 0, asc = 0, calibrationDue = 0, reserved = 0;
  uint32_t batteryMah = 3500;
  char name[25] = "Workshop logger";
};
// Fixed, versioned 64-byte records; never log native C++ Settings structs.
#pragma pack(push, 1)
struct Record {
  uint32_t magic = RecordMagic, sequence = 0, session = 0, utc = 0, uptimeS = 0;
  uint16_t channels = All, flags = 0;
  float co2 = NAN, temperature = NAN, humidity = NAN, lux = NAN, volts = NAN, percent = NAN;
  uint16_t co2AgeBoundS = 65535, revision = 0, event = Sample, reserved = 0;
  uint32_t auxiliary = 0, crc = 0;
};
#pragma pack(pop)
static_assert(sizeof(Record) == 64, "Record format changed: migrate, do not reinterpret old logs");
uint8_t crc8(const uint8_t *bytes, size_t n);
uint32_t crc32(const void *bytes, size_t n);
void seal(Record &r);
bool valid(const Record &r);
enum class RecordCheck { Good, TornTail, Corrupt };
RecordCheck checkRecord(const Record &r, uint32_t previousSequence, uint32_t offset,
                        uint32_t fileSize);
float decodeFloat(uint16_t high, uint16_t low);
const char *validate(const Settings &s);
bool validUtc(uint32_t epoch);
uint64_t advanceDeadline(uint64_t due, uint64_t now, uint32_t intervalS);
uint32_t calibrationWaitMs(uint16_t cadenceS);
const char *eventName(uint16_t event);
struct PowerInputs {
  double capacityMah = 3500, usableFraction = .8, chargePercent = 100;
  double intervalS = 60, sensorIntervalS = 2, wakeSeconds = 1.2;
  double wifiMinutesPerDay = 10, screenMinutesPerDay = 10;
  double boardSleepMa = .1, cpuMa = 45, screenMa = 25, wifiBoardMa = 160;
  double breakoutMa = 2, rtcMa = .2, lightSleepMa = .004, lcdSleepMa = .02;
};
struct Estimate {
  double sensorMa, averageMa, hours, lowHours, highHours, storageHours;
  uint32_t records;
};
Estimate estimate(const PowerInputs &p, uint32_t freeBytes);
} // namespace logger
