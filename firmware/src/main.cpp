#include "App.h"
#include <WiFi.h>
#include <driver/gpio.h>
#include <driver/rtc_io.h>
#include <esp_sleep.h>
#include <esp_system.h>
#include <sys/time.h>
using namespace logger;
RTC_DATA_ATTR Retained retained;
App app;
static constexpr uint32_t RetentionMagic = 0x53573031;
static uint64_t wallUs() {
  timeval t;
  gettimeofday(&t, nullptr);
  return uint64_t(t.tv_sec) * 1000000 + t.tv_usec;
}
struct DiskSettings {
  uint32_t magic;
  Settings value;
  uint32_t crc;
};
uint32_t App::utc() const {
  time_t t = time(nullptr);
  return clockTrusted && t > 0 && validUtc(uint32_t(t)) ? uint32_t(t) : 0;
}
bool App::fresh() const {
  return sensors.scd && sensors.reading.co2Valid && now() >= sensors.reading.co2At &&
         now() - sensors.reading.co2At <= uint64_t(settings.sensorIntervalS) * 2000 + 3000;
}
bool App::warming() const {
  return !retained.scdRunning || now() - retained.scdStartedMs < 120000;
}
void App::toast(const String &text) {
  notice = text;
  noticeUntil = now() + 4000;
  Serial.println(text);
  draw(true);
}
bool App::save(const Settings &value) {
  DiskSettings d{};
  d.magic = 0x53434631;
  d.value = value;
  d.crc = crc32(&d, offsetof(DiskSettings, crc));
  return prefs.putBytes("settings", &d, sizeof(d)) == sizeof(d);
}
void App::begin() {
  const auto wake = esp_sleep_get_wakeup_cause();
  const bool resumed = esp_reset_reason() == ESP_RST_DEEPSLEEP && retained.magic == RetentionMagic;
  if (resumed) {
    uint64_t wall = wallUs(),
             elapsed = wall >= retained.sleepWallUs ? wall - retained.sleepWallUs : 0;
    retained.baseMs += elapsed / 1000;
    const uint64_t awakeMs = uint64_t(esp_timer_get_time()) / 1000;
    retained.baseMs = retained.baseMs > awakeMs ? retained.baseMs - awakeMs : 0;
  } else {
    retained = Retained{};
    retained.magic = RetentionMagic;
    retained.session = esp_random();
  }
  // Establish the desired levels BEFORE releasing holds, avoiding a rail dip.
  pinMode(TFT_I2C_POWER, OUTPUT);
  digitalWrite(TFT_I2C_POWER, HIGH);
  gpio_hold_dis(GPIO_NUM_7);
  pinMode(TFT_BACKLITE, OUTPUT);
  digitalWrite(TFT_BACKLITE, LOW);
  gpio_hold_dis(GPIO_NUM_45);
  pinMode(NEOPIXEL_POWER, OUTPUT);
  digitalWrite(NEOPIXEL_POWER, LOW);
  gpio_hold_dis(GPIO_NUM_21);
  gpio_deep_sleep_hold_dis();
  for (int pin = 0; pin <= 2; pin++) {
    rtc_gpio_hold_dis(static_cast<gpio_num_t>(pin));
    rtc_gpio_deinit(static_cast<gpio_num_t>(pin));
  }
  pinMode(0, INPUT_PULLUP);
  pinMode(1, INPUT_PULLDOWN);
  pinMode(2, INPUT_PULLDOWN);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.begin(115200);
  setCpuFrequencyMhz(80);
  resetReason = esp_reset_reason();
  bootAt = now();
  prefs.begin("sensor-workshop", false);
  DiskSettings disk{};
  if (prefs.getBytesLength("settings") == sizeof(disk) &&
      prefs.getBytes("settings", &disk, sizeof(disk)) == sizeof(disk) && disk.magic == 0x53434631 &&
      disk.crc == crc32(&disk, offsetof(DiskSettings, crc)) && !validate(disk.value)) {
    settings = disk.value;
    configured = true;
  }
  char suffix[7];
  // The low three bytes are the vendor prefix; use the device-specific bytes.
  snprintf(suffix, sizeof(suffix), "%06X", unsigned((ESP.getEfuseMac() >> 24) & 0xffffff));
  ssid = String("Sensor-") + suffix;
  password = prefs.getString("wifi-pass", "");
  if (password.length() != 10) {
    const char alphabet[] = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz";
    password = "";
    for (int i = 0; i < 10; i++)
      password += alphabet[esp_random() % (sizeof(alphabet) - 1)];
    prefs.putString("wifi-pass", password);
  }
  char nonce[25];
  snprintf(nonce, sizeof(nonce), "%08lx%08lx%08lx", (unsigned long)esp_random(),
           (unsigned long)esp_random(), (unsigned long)esp_random());
  token = nonce;
  bool running = resumed && retained.railOn && retained.scdRunning;
  delay(20);
  sensors.reading = resumed ? retained.reading : Reading{};
  sensors.begin(settings, running);
  if (sensors.scd && !running)
    retained.scdStartedMs = now();
  retained.scdRunning = sensors.scd;
  clockTrusted = resumed && retained.clockTrusted;
  rtcValid = sensors.rtcPresent && !sensors.rtc.lostPower();
  if (rtcValid) {
    uint32_t epoch = sensors.rtc.now().unixtime();
    rtcValid = validUtc(epoch);
    if (rtcValid) {
      timeval tv{static_cast<time_t>(epoch), 0};
      settimeofday(&tv, nullptr);
      clockTrusted = true;
    }
  }
  storage.begin(resumed, retained.storeBytes, retained.storeSequence);
  if (!resumed) {
    retained.nextLogMs = now();
    event(Boot, resetReason);
  }
  setupRoutes();
  const bool timer = resumed && wake == ESP_SLEEP_WAKEUP_TIMER;
  if (!timer) {
    startScreen();
    activeUntil = now() + uint64_t(settings.screenSeconds) * 1000;
  }
  if (resumed && wake == ESP_SLEEP_WAKEUP_EXT1 &&
      (esp_sleep_get_ext1_wakeup_status() & (1ULL << 1)))
    startWifi();
  Serial.printf(
      "Sensor Workshop %s | reset %u wake %u | log %s | RTC %s | SCD30 %s | %s | %lu records\n",
      FW_VERSION, unsigned(resetReason), unsigned(wake), settings.logging ? "on" : "paused",
      rtcValid ? "ok" : "unset/missing", sensors.scd ? "ok" : "missing", sensors.lightName(),
      (unsigned long)storage.count);
}
bool App::changeSettings(Settings value, String &error) {
  if (const char *why = validate(value)) {
    error = why;
    return false;
  }
  if (calibration) {
    error = "Finish or cancel calibration first.";
    return false;
  }
  bool sensorChanged = value.sensorIntervalS != settings.sensorIntervalS ||
                       value.asc != settings.asc ||
                       value.temperatureOffsetCenti != settings.temperatureOffsetCenti ||
                       value.altitudeM != settings.altitudeM;
  if (sensorChanged && !sensors.scd) {
    error = "CO2 sensor is unavailable; sensor settings were not saved.";
    return false;
  }
  if (value.sensorIntervalS != settings.sensorIntervalS)
    value.calibrationDue = 1;
  value.revision = settings.revision == 65535 ? 1 : settings.revision + 1;
  if (sensorChanged && !sensors.configure(value)) {
    sensors.configure(settings);
    error = "Sensor did not confirm settings. Previous settings retained.";
    return false;
  }
  if (!save(value)) {
    if (sensorChanged)
      sensors.configure(settings);
    error = "Settings could not be saved.";
    return false;
  }
  bool restarted = value.sensorIntervalS != settings.sensorIntervalS;
  settings = value;
  configured = true;
  if (restarted)
    retained.scdStartedMs = now();
  retained.nextLogMs = now() + uint64_t(settings.intervalS) * 1000;
  event(ConfigChanged);
  activeUntil = now() + uint64_t(settings.screenSeconds) * 1000;
  if (wifi)
    wifiUntil = now() + uint64_t(settings.wifiMinutes) * 60000;
  return true;
}
void App::setLogging(bool enabled) {
  if (calibration) {
    toast("Finish calibration first");
    return;
  }
  Settings value = settings;
  value.logging = enabled;
  String error;
  if (!changeSettings(value, error)) {
    toast(error);
    return;
  }
  retained.nextLogMs = now();
  event(enabled ? Started : Paused);
  toast(enabled ? "Logging started" : "Logging paused");
}
bool App::setClock(uint32_t epoch, String &error) {
  if (!validUtc(epoch)) {
    error = "Phone time must be between 2020 and 2037.";
    return false;
  }
  uint32_t old = utc();
  if (sensors.rtcPresent) {
    sensors.rtc.adjust(DateTime(epoch));
    uint32_t back = sensors.rtc.now().unixtime();
    if (sensors.rtc.lostPower() || back < epoch || back > epoch + 2) {
      error = "RTC did not confirm the new time.";
      return false;
    }
    rtcValid = true;
  }
  timeval tv{static_cast<time_t>(epoch), 0};
  settimeofday(&tv, nullptr);
  clockTrusted = true;
  event(ClockSet, old);
  return true;
}
Record App::makeRecord(uint16_t kind) {
  Record r;
  r.session = retained.session;
  r.utc = utc();
  r.uptimeS = uint32_t(now() / 1000);
  r.channels = settings.channels;
  r.revision = settings.revision;
  r.event = kind;
  if (r.utc)
    r.flags |= TimeValid;
  if (warming())
    r.flags |= Warming;
  if (settings.calibrationDue)
    r.flags |= CalibrationDue;
  if (calibration)
    r.flags |= Calibrating;
  auto &v = sensors.reading;
  if (fresh()) {
    if (r.channels & CO2)
      r.co2 = v.co2;
    if (r.channels & Temperature)
      r.temperature = v.temperature;
    if (r.channels & Humidity)
      r.humidity = v.humidity;
    r.co2AgeBoundS =
        uint16_t(std::min<uint64_t>(65535, (now() - v.co2At) / 1000 + settings.sensorIntervalS));
  } else
    r.flags |= (!sensors.scd || !v.co2Valid) ? ScdMissing : Stale;
  if (v.lightValid) {
    if (r.channels & Light)
      r.lux = v.lux;
  } else
    r.flags |= v.saturated ? LightSaturated : LightMissing;
  if (v.batteryValid) {
    if (r.channels & Battery) {
      r.volts = v.volts;
      r.percent = v.percent;
    }
  } else
    r.flags |= BatteryMissing;
  return r;
}
bool App::event(uint16_t kind, uint32_t aux) {
  if (!storage.healthy)
    return false;
  Record r = makeRecord(kind);
  r.auxiliary = aux;
  return storage.append(r);
}
void App::logIfDue() {
  if (!settings.logging || now() < retained.nextLogMs || sensors.lightBusy())
    return;
  Record r = makeRecord();
  if (storage.append(r))
    Serial.printf("sample %lu utc=%lu co2=%.1f lux=%.2f flags=%u\n", (unsigned long)r.sequence,
                  (unsigned long)r.utc, r.co2, r.lux, r.flags);
  retained.nextLogMs = advanceDeadline(retained.nextLogMs, now(), settings.intervalS);
}
void App::buttons() {
  struct Button {
    bool raw = false, stable = false, armed = false, held = false;
    uint32_t changed = 0, down = 0;
  };
  static Button b[3];
  for (int i = 0; i < 3; i++) {
    bool raw = digitalRead(i) == (i == 0 ? LOW : HIGH);
    auto &k = b[i];
    uint32_t ms = millis();
    if (!raw && !k.stable)
      k.armed = true;
    if (raw != k.raw) {
      k.raw = raw;
      k.changed = ms;
    }
    if (ms - k.changed >= 30 && k.stable != raw) {
      k.stable = raw;
      if (raw) {
        k.down = ms;
        k.held = false;
        activeUntil = now() + uint64_t(settings.screenSeconds) * 1000;
      } else if (k.armed && !k.held) {
        if (i == 0) {
          page = (page + 1) % ScreenPageCount;
          draw(true);
        }
        if (i == 1) {
          if (wifi)
            stopWifi();
          else
            startWifi();
        }
        if (i == 2)
          setLogging(!settings.logging);
      }
    }
    if (i == 0 && k.stable && k.armed && !k.held && ms - k.down >= 1500) {
      k.held = true;
      if (calibration)
        toast("Calibration is active");
      else {
        if (wifi)
          stopWifi();
        activeUntil = 0;
      }
    }
  }
}
void App::sleep() {
#ifdef FW_STAY_AWAKE
  return;
#endif
  if ((settings.logging && storage.healthy && !storage.full && now() >= retained.nextLogMs) ||
      wifi || calibration || digitalRead(0) == LOW || digitalRead(1) == HIGH ||
      digitalRead(2) == HIGH)
    return;
  bool keep = settings.logging && storage.healthy && !storage.full;
  if (screen) {
    tft.enableDisplay(false);
    tft.enableSleep(true);
  }
  digitalWrite(TFT_BACKLITE, LOW);
  sensors.sleepLight();
  if (!keep)
    sensors.stopScd();
  Wire.end();
  pinMode(SDA, INPUT);
  pinMode(SCL, INPUT); // avoid parasitic powering when parked
  digitalWrite(TFT_I2C_POWER, keep ? HIGH : LOW);
  digitalWrite(NEOPIXEL_POWER, LOW);
  gpio_hold_en(GPIO_NUM_7);
  gpio_hold_en(GPIO_NUM_21);
  gpio_hold_en(GPIO_NUM_45);
  gpio_deep_sleep_hold_en();
  retained.railOn = keep;
  retained.scdRunning = keep && sensors.scd;
  retained.clockTrusted = clockTrusted;
  retained.reading = sensors.reading;
  retained.storeBytes = storage.count * sizeof(Record);
  retained.storeSequence = storage.sequence;
  retained.baseMs = now();
  retained.sleepWallUs = wallUs();
  esp_sleep_enable_ext0_wakeup(GPIO_NUM_0, 0);
  esp_sleep_enable_ext1_wakeup((1ULL << 1) | (1ULL << 2), ESP_EXT1_WAKEUP_ANY_HIGH);
  rtc_gpio_pullup_en(GPIO_NUM_0);
  rtc_gpio_pulldown_dis(GPIO_NUM_0);
  for (auto pin : {GPIO_NUM_1, GPIO_NUM_2}) {
    rtc_gpio_pullup_dis(pin);
    rtc_gpio_pulldown_en(pin);
  }
  if (keep) {
    uint64_t wait =
        retained.nextLogMs > retained.baseMs ? retained.nextLogMs - retained.baseMs : 1000;
    esp_sleep_enable_timer_wakeup(std::max<uint64_t>(1000, wait) * 1000);
  }
  Serial.flush();
  esp_deep_sleep_start();
}
void App::loop() {
  sensors.poll(now(), settings);
  buttons();
  serviceWeb();
  logIfDue();
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'w') {
      startWifi();
      if (wifi)
        Serial.printf("Wi-Fi: %s | password: %s | http://192.168.4.1/\n", ssid.c_str(),
                      password.c_str());
    }
    if (c == 'j') {
      DynamicJsonDocument d(4096);
      statusJson(d);
      d.remove("token"); // Diagnostics do not need the HTTP write token.
      serializeJson(d, Serial);
      Serial.println();
    }
    if (c == '?')
      Serial.printf("RTC=%s SCD30=%s light=%s records=%lu free=%lu errors=%lu\n",
                    rtcValid ? "ok" : "unset", sensors.scd ? "ok" : "missing", sensors.lightName(),
                    (unsigned long)storage.count, (unsigned long)storage.freeBytes(),
                    (unsigned long)sensors.errors);
  }
  if (wifi && now() >= wifiUntil && !calibration)
    stopWifi();
  if (screen)
    draw();
  if (!wifi && !calibration && now() >= activeUntil && now() - bootAt > 1200)
    sleep();
  delay(5);
}
void setup() {
  app.begin();
}
void loop() {
  app.loop();
}
