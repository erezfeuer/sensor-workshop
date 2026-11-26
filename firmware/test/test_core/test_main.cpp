#include <LoggerCore.h>
#include <cstring>
#include <limits>
#include <unity.h>
using namespace logger;
void setUp() {}
void tearDown() {}
void crc_vectors() {
  const uint8_t a[] = {0xbe, 0xef}, b[] = {0, 2}, c[] = {0, 0};
  TEST_ASSERT_EQUAL_HEX8(0x92, crc8(a, 2));
  TEST_ASSERT_EQUAL_HEX8(0xe3, crc8(b, 2));
  TEST_ASSERT_EQUAL_HEX8(0x81, crc8(c, 2));
  TEST_ASSERT_EQUAL_HEX32(0xcbf43926, crc32("123456789", 9));
}
void sensor_float() {
  TEST_ASSERT_FLOAT_WITHIN(.001, 400, decodeFloat(0x43c8, 0));
  TEST_ASSERT_FLOAT_WITHIN(.001, -10, decodeFloat(0xc120, 0));
  TEST_ASSERT_TRUE(std::isnan(decodeFloat(0x7fc0, 0)));
}
void record_integrity() {
  Record r;
  r.sequence = 123;
  r.utc = 1795680000;
  r.flags = TimeValid;
  r.co2 = 423.5;
  seal(r);
  TEST_ASSERT_EQUAL(64, sizeof(r));
  TEST_ASSERT_TRUE(valid(r));
  for (size_t i = 0; i < sizeof(r); i++) {
    Record corrupt = r;
    reinterpret_cast<uint8_t *>(&corrupt)[i] ^= 1;
    TEST_ASSERT_FALSE(valid(corrupt));
  }
  TEST_ASSERT_TRUE(std::isnan(r.lux));
}
void settings_reject_bad_values() {
  Settings s;
  TEST_ASSERT_NULL(validate(s));
  s.intervalS = 4;
  TEST_ASSERT_NOT_NULL(validate(s));
  s.intervalS = 86401;
  TEST_ASSERT_NOT_NULL(validate(s));
  s = Settings{};
  s.sensorIntervalS = 30;
  s.intervalS = 15;
  TEST_ASSERT_NOT_NULL(validate(s));
  s.intervalS = 60;
  TEST_ASSERT_NULL(validate(s));
  s.sensorIntervalS = 3;
  TEST_ASSERT_NOT_NULL(validate(s));
  s = Settings{};
  s.channels = 0;
  TEST_ASSERT_NOT_NULL(validate(s));
  s.channels = 32;
  TEST_ASSERT_NOT_NULL(validate(s));
  s = Settings{};
  s.batteryMah = 3500;
  TEST_ASSERT_NULL(validate(s));
  memset(s.name, 'x', sizeof(s.name));
  TEST_ASSERT_NOT_NULL(validate(s));
  s = Settings{};
  s.name[1] = '\n';
  TEST_ASSERT_NOT_NULL(validate(s));
  s = Settings{};
  s.asc = 2;
  TEST_ASSERT_NOT_NULL(validate(s));
}
void monotonic_scheduling() {
  TEST_ASSERT_EQUAL_UINT64(60000, advanceDeadline(0, 1, 60));
  TEST_ASSERT_EQUAL_UINT64(120000, advanceDeadline(60000, 60000, 60));
  TEST_ASSERT_EQUAL_UINT64(240000, advanceDeadline(60000, 185000, 60));
  TEST_ASSERT_EQUAL_UINT64(60000, advanceDeadline(60000, 5000, 60));
  const uint64_t late = uint64_t(1) << 34;
  TEST_ASSERT_TRUE(advanceDeadline(late, late + 100000, 60) > late + 100000);
}
void clock_bounds() {
  TEST_ASSERT_FALSE(validUtc(0));
  TEST_ASSERT_FALSE(validUtc(1577836799));
  TEST_ASSERT_TRUE(validUtc(1577836800));
  TEST_ASSERT_TRUE(validUtc(2145916799));
  TEST_ASSERT_FALSE(validUtc(2145916800));
}
void calibration_guard() {
  TEST_ASSERT_EQUAL(360000, calibrationWaitMs(2));
  TEST_ASSERT_EQUAL(360000, calibrationWaitMs(60));
  TEST_ASSERT_EQUAL(500000, calibrationWaitMs(100));
}
void runtime_model() {
  PowerInputs p;
  Estimate e = estimate(p, 1441792);
  TEST_ASSERT_DOUBLE_WITHIN(.00001, 19, e.sensorMa);
  TEST_ASSERT_DOUBLE_WITHIN(.001, 23.8053611111, e.averageMa);
  TEST_ASSERT_EQUAL_UINT32(22016, e.records);
  TEST_ASSERT_DOUBLE_WITHIN(.01, 366.9333, e.storageHours);
  TEST_ASSERT_TRUE(e.lowHours < e.hours && e.highHours > e.hours);
  p.sensorIntervalS = 30;
  auto slow = estimate(p, 1441792);
  TEST_ASSERT_DOUBLE_WITHIN(.00001, 5.6, slow.sensorMa);
  TEST_ASSERT_TRUE(slow.hours > e.hours);
  p.chargePercent = 50;
  auto half = estimate(p, 1441792);
  TEST_ASSERT_DOUBLE_WITHIN(.001, slow.hours / 2, half.hours);
  p.chargePercent = 0;
  TEST_ASSERT_DOUBLE_WITHIN(.001, 0, estimate(p, 0).hours);
  TEST_ASSERT_EQUAL(0, estimate(p, 32767).records);
  TEST_ASSERT_EQUAL(1, estimate(p, 32832).records);
}
void duty_clamping() {
  PowerInputs p;
  p.wifiMinutesPerDay = 1440;
  p.screenMinutesPerDay = 1440;
  p.wakeSeconds = 500;
  auto e = estimate(p, 0);
  TEST_ASSERT_DOUBLE_WITHIN(.001, 181.224, e.averageMa);
  TEST_ASSERT_TRUE(std::isfinite(e.hours));
  TEST_ASSERT_EQUAL(0, e.records);
}
void power_loss_recovery_policy() {
  Record good;
  good.sequence = 2;
  seal(good);
  TEST_ASSERT_TRUE(checkRecord(good, 1, 64, 128) == RecordCheck::Good);
  for (size_t i = 0; i < sizeof(Record); i++) {
    Record broken = good;
    reinterpret_cast<uint8_t *>(&broken)[i] ^= 0x80;
    TEST_ASSERT_TRUE(checkRecord(broken, 1, 64, 128) == RecordCheck::TornTail);
    TEST_ASSERT_TRUE(checkRecord(broken, 1, 64, 192) == RecordCheck::Corrupt);
    TEST_ASSERT_TRUE(checkRecord(broken, 1, 64, 129) == RecordCheck::Corrupt);
  }
  TEST_ASSERT_TRUE(checkRecord(good, 2, 64, 192) == RecordCheck::Corrupt);
}
int main() {
  UNITY_BEGIN();
  RUN_TEST(power_loss_recovery_policy);
  RUN_TEST(crc_vectors);
  RUN_TEST(sensor_float);
  RUN_TEST(record_integrity);
  RUN_TEST(settings_reject_bad_values);
  RUN_TEST(monotonic_scheduling);
  RUN_TEST(clock_bounds);
  RUN_TEST(calibration_guard);
  RUN_TEST(runtime_model);
  RUN_TEST(duty_clamping);
  return UNITY_END();
}
