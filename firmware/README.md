# Sensor Workshop firmware

A PlatformIO logger for the **Adafruit ESP32-S3 Reverse TFT Feather (5691)**, SCD30, TSL2591 and DS3231. It records to internal flash, sleeps between observations, and serves a complete phone dashboard over a temporary Wi-Fi hotspot. The original VEML7700 light-sensor option is also detected automatically.

**Status: v0.1.0, compiled and tested in software; not yet flashed or tested on the assembled prototype.** Hardware acceptance checks are [listed here](docs/HARDWARE-CHECKS.md). The battery capacity defaults to Erez's **3,500 mAh, 3.7 V cell**.

**[Open the interactive preview](preview.html)** by downloading/opening the HTML in a browser. Its measurements and device controls are simulated and clearly labelled; its calculator uses the production model. It runs without an internet connection. The actual firmware serves [web/index.html](web/index.html), with no simulator, CDN, external fonts or chart library.

## What the device does

- **D0 — View:** cycle readings, light/battery, and storage/runtime screens. Hold for 1.5 seconds to sleep.
- **D1 — Phone:** open the hotspot and show a Wi-Fi QR code, network name, password and `192.168.4.1`. Press again to close it. The default session lasts ten minutes.
- **D2 — Start/Pause:** toggle logging. On first boot, logging is paused. On waking, the initial D0/D2 press only wakes the screen; D1 also opens Wi-Fi.
- **Any button wakes it.** During logging the ESP32 also wakes on its recording timer; the screen remains off on those timer wakes. The default screen timeout is 45 seconds.

The phone page has live readings, selectable plots, CSV/raw downloads, recording settings, runtime/storage planning and guided CO₂ calibration. Opening it sets an unset/drifting clock from the phone; a separate button also sets time explicitly. No internet connection is required. If a captive-portal window does not open or cannot download a file, stay connected to the hotspot and use your regular browser at `http://192.168.4.1/`.

The dashboard uses responsive cards, system fonts, large touch controls and a small native canvas plot. Its complete HTML/CSS/JS is about **13 KB compressed**, with a **16 KiB build budget** to catch asset growth. There are no framework, font, image or chart-library downloads. Status polling is limited to one request at a time: every two seconds in Live/Calibration, every five seconds in Settings/Runtime, and suspended while the browser page is hidden. Failed requests back off to fifteen seconds; returning to the page refreshes immediately. Plots redraw on demand, with their bitmap capped at 2× display resolution. These choices keep the interface small and reduce work for the Feather; actual hotspot latency still needs hardware testing.

The **SCD30 stays powered while logging**, including between ESP32 wakeups. Recording cadence and sensor measurement cadence are separate settings. The default is one record per minute with the SCD30 measuring every two seconds. Pausing and allowing the device to sleep turns off the external sensor/display power rail; the RTC keeps time from its coin cell. First readings after sensor power-up are marked as warming up.

Automatic CO₂ self-calibration is off by default, appropriate for a greenhouse without guaranteed daily fresh-air exposure. Forced calibration requires a known reference, six minutes of continuous stabilisation, and a separate confirmation. A slower sensor cadence requires recalibration and review of the temperature offset. Temperature is the SCD30 reading inside this enclosure, not a validated ambient reference.

## Build

Open **this `firmware` folder** in VS Code with PlatformIO, or run from it:

```sh
pio run -e feather
pio run -e feather-debug
```

The normal environment sleeps. The bench environment uses the same sensors, logger and UI but stays awake, making native USB serial easier to inspect. **Its battery runtime will not match the production calculator.** Dependencies and platform versions are pinned in [platformio.ini](platformio.ini).

The dashboard is compressed and embedded during compilation. **No `uploadfs` step is needed.** The filesystem is reserved for observations. The app and log partitions are each 1,408 KiB; the partition map preserves the board's TinyUF2 factory region. There is no OTA firmware updater in this version.

After hardware is connected and flashing is authorised, build/upload the bench version first:

```sh
pio run -e feather-debug -t upload
pio device monitor -b 115200
```

Serial `?` prints diagnostics; `w` opens Wi-Fi. There is no wait for a serial connection at boot. After bench checks, upload `feather` for button wake and sleep-current tests. Native USB disconnecting during deep sleep is expected. The board's BOOT/RESET recovery procedure is in the [Adafruit guide](https://learn.adafruit.com/esp32-s3-reverse-tft-feather/factory-reset).

Do not use full-flash erase, filesystem upload, or change the partition layout without first exporting wanted data. Normal firmware uploads with this same layout leave the log partition in place; this preservation still needs the hardware upgrade test.

## Tests and preview generation

```sh
pio test -e native
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/make_preview.py
python3 tests/check_dashboard.py
python3 scripts/check_build.py
```

The browser check requires Python Playwright plus Chromium or local Google Chrome (`python3 -m pip install playwright`, then `python3 -m playwright install chromium` if needed). It exercises the production HTML against a simulated API, saves screenshots to ignored `tests/artifacts/`, and does not contact hardware. It does **not** validate the ESP32 HTTP implementation or sensor buses. Native tests cover the portable firmware logic; Python tests cover raw-log decoding and corruption handling. [Validation record](docs/validation.json).

## Source map

| File | Purpose |
| --- | --- |
| [src/main.cpp](src/main.cpp) | Boot, persisted settings, recording schedule, buttons, sleep and UTC |
| [src/Sensors.cpp](src/Sensors.cpp) | SCD30 protocol/CRC, nonblocking light conversion, RTC and fuel gauge |
| [src/Storage.cpp](src/Storage.cpp) | LittleFS journal, reserve, CRC scanning and tail recovery |
| [src/Web.cpp](src/Web.cpp) | Hotspot, API, calibration and streamed exports |
| [src/Display.cpp](src/Display.cpp) | TFT pages, button labels and Wi-Fi QR code |
| [lib/LoggerCore/src](lib/LoggerCore/src) | Portable record format, validation, scheduling and power model |
| [web/index.html](web/index.html) | Complete production dashboard |
| [scripts/decode_log.py](scripts/decode_log.py) | Recover valid raw-log records to CSV on a computer |

[Power estimates and sources](docs/POWER.md) · [Architecture, API and data format](docs/ARCHITECTURE.md) · [Hardware acceptance checks](docs/HARDWARE-CHECKS.md)
