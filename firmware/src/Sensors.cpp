#include "Sensors.h"
using namespace logger;
bool Sensors::ping(uint8_t a) {
  Wire.beginTransmission(a);
  return Wire.endTransmission() == 0;
}
bool Sensors::command(uint16_t c) {
  Wire.beginTransmission(0x61);
  Wire.write(c >> 8);
  Wire.write(c & 255);
  bool ok = Wire.endTransmission() == 0;
  if (!ok)
    errors++;
  return ok;
}
bool Sensors::words(uint16_t c, uint16_t *out, size_t n) {
  if (n > 6 || !command(c))
    return false;
  delay(3);
  if (Wire.requestFrom(uint8_t(0x61), uint8_t(n * 3)) != n * 3) {
    while (Wire.available())
      Wire.read();
    errors++;
    return false;
  }
  uint8_t data[18];
  for (size_t i = 0; i < n * 3; i++)
    data[i] = Wire.read();
  for (size_t i = 0; i < n; i++) {
    if (crc8(data + i * 3, 2) != data[i * 3 + 2]) {
      errors++;
      return false;
    }
    out[i] = (uint16_t(data[i * 3]) << 8) | data[i * 3 + 1];
  }
  return true;
}
bool Sensors::scdWord(uint16_t c, uint16_t &o) {
  return words(c, &o, 1);
}
bool Sensors::scdWrite(uint16_t c, uint16_t v) {
  uint8_t b[2] = {uint8_t(v >> 8), uint8_t(v)};
  Wire.beginTransmission(0x61);
  Wire.write(c >> 8);
  Wire.write(c & 255);
  Wire.write(b, 2);
  Wire.write(crc8(b, 2));
  bool ok = Wire.endTransmission() == 0;
  delay(5);
  if (!ok)
    errors++;
  return ok;
}
bool Sensors::configure(const Settings &s) {
  if (!scd)
    return false;
  const uint16_t commands[] = {0x4600, 0x5306, 0x5403, 0x5102};
  const uint16_t values[] = {s.sensorIntervalS, s.asc, s.temperatureOffsetCenti, s.altitudeM};
  for (int i = 0; i < 4; i++) {
    uint16_t value;
    if (!scdWord(commands[i], value))
      return false;
    if (value != values[i]) {
      if (!scdWrite(commands[i], values[i]))
        return false;
      delay(20);
      if (!scdWord(commands[i], value) || value != values[i])
        return false;
    }
  }
  return true;
}
bool Sensors::begin(const Settings &s, bool retained) {
  const uint32_t beginAt = millis();
  Wire.begin(SDA, SCL, 50000);
  Wire.setClock(50000);
  Wire.setTimeOut(200);
  rtcPresent = ping(0x68) && rtc.begin(&Wire);
  fuel = ping(0x36) && gauge.begin(&Wire);
  tslPresent = ping(0x29) && tsl.begin(&Wire, 0x29);
  if (tslPresent) {
    tsl.setTiming(TSL2591_INTEGRATIONTIME_100MS);
    tsl.setGain(TSL2591_GAIN_MED);
    tsl.disable();
  } else {
    vemlPresent = ping(0x10) && veml.begin(&Wire);
    if (vemlPresent) {
      veml.setGain(VEML7700_GAIN_1_8);
      veml.setIntegrationTime(VEML7700_IT_100MS);
      veml.powerSaveEnable(false);
      veml.enable(false);
    }
  }
  // Sensirion specifies up to 2 seconds boot time after power is applied.
  // A normal logging wake retains the rail and does not incur this delay.
  if (!retained && millis() - beginAt < 2000)
    delay(2000 - (millis() - beginAt));
  uint16_t version = 0;
  scd = ping(0x61) && scdWord(0xd100, version);
  if (scd && !configure(s))
    scd = false;
  if (scd && !retained && !scdWrite(0x0010, 0))
    scd = false;
  return scd;
}
void Sensors::poll(uint64_t now, const Settings &s) {
  finishLight(now);
  if (lastPoll && now - lastPoll < 1000)
    return;
  lastPoll = now;
  if (scd) {
    uint16_t ready = 0, w[6];
    if (scdWord(0x0202, ready) && ready && words(0x0300, w, 6)) {
      float c = decodeFloat(w[0], w[1]), t = decodeFloat(w[2], w[3]), h = decodeFloat(w[4], w[5]);
      if (isfinite(c) && c > 0 && c <= 40000 && isfinite(t) && t >= -40 && t <= 85 && isfinite(h) &&
          h >= 0 && h <= 100) {
        reading.co2 = c;
        reading.temperature = t;
        reading.humidity = h;
        reading.co2At = now;
        reading.co2Valid = true;
      } else
        errors++;
    }
  }
  if (!lightPending) {
    lightAttempts = 0;
    startLight(now);
  }
  reading.batteryValid = false;
  if (fuel && ping(0x36)) {
    float v = gauge.cellVoltage(), pct = gauge.cellPercent();
    if (isfinite(v) && v > 2 && v < 4.8 && isfinite(pct) && pct >= 0 && pct <= 105) {
      reading.volts = v;
      reading.percent = constrain(pct, 0.f, 100.f);
      reading.batteryValid = true;
    }
  }
  (void)s;
}
bool Sensors::lightWord(uint8_t reg, uint16_t &value) {
  Wire.beginTransmission(0x29);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(uint8_t(0x29), uint8_t(2)) != 2) {
    errors++;
    while (Wire.available())
      Wire.read();
    return false;
  }
  uint8_t low = Wire.read();
  value = low | (uint16_t(Wire.read()) << 8);
  return true;
}
void Sensors::startLight(uint64_t now) {
  reading.saturated = false;
  if (tslPresent && ping(0x29)) {
    const tsl2591Gain_t gains[] = {TSL2591_GAIN_LOW, TSL2591_GAIN_MED, TSL2591_GAIN_HIGH};
    tsl.setGain(gains[gain]);
    tsl.enable();
    lightPending = true;
    lightReadyAt = now + 120;
  } else if (vemlPresent && ping(0x10)) {
    veml.enable(true);
    lightPending = true;
    lightReadyAt = now + 120;
  } else
    reading.lightValid = false;
}
void Sensors::finishLight(uint64_t now) {
  if (!lightPending || now < lightReadyAt)
    return;
  lightPending = false;
  reading.lightValid = false;
  if (tslPresent) {
    uint16_t full = 0, ir = 0;
    bool ok = lightWord(0xb4, full) && lightWord(0xb6, ir);
    tsl.disable();
    if (!ok)
      return;
    if (lightAttempts < 2) {
      if ((full >= 35000 || ir >= 35000) && gain > 0) {
        gain--;
        lightAttempts++;
        startLight(now);
        return;
      }
      if (full < 100 && gain < 2) {
        gain++;
        lightAttempts++;
        startLight(now);
        return;
      }
    }
    reading.saturated = full >= 36863 || ir >= 36863;
    float lux = full == 0 ? 0 : tsl.calculateLux(full, ir);
    if (!reading.saturated && isfinite(lux) && lux >= 0) {
      reading.lux = lux;
      reading.lightValid = true;
    }
  } else if (vemlPresent) {
    float lux = veml.readLux(VEML_LUX_CORRECTED_NOWAIT);
    uint16_t raw = veml.readALS();
    veml.enable(false);
    reading.saturated = raw >= 65500;
    if (!reading.saturated && isfinite(lux) && lux >= 0) {
      reading.lux = lux;
      reading.lightValid = true;
    }
  }
}
bool Sensors::forceCalibration(uint16_t ppm) {
  if (ppm < 400 || ppm > 2000 || !scd)
    return false;
  if (!scdWrite(0x5204, ppm))
    return false;
  delay(100);
  uint16_t back = 0;
  return scdWord(0x5204, back) && back == ppm;
}
bool Sensors::stopScd() {
  return !scd || command(0x0104);
}
void Sensors::sleepLight() {
  if (tslPresent)
    tsl.disable();
  if (vemlPresent)
    veml.enable(false);
}
