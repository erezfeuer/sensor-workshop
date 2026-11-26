# Firmware architecture and data contract

## Hardware and power

Target: Adafruit 5691, ESP32-S3 Reverse TFT Feather, 4 MB flash / 2 MB PSRAM. See the [Adafruit pinout](https://learn.adafruit.com/esp32-s3-reverse-tft-feather/pinouts), [power guide](https://learn.adafruit.com/esp32-s3-reverse-tft-feather/power-management) and [PlatformIO board definition](https://docs.platformio.org/en/latest/boards/espressif32/adafruit_feather_esp32s3_reversetft.html).

| Function | Pins/address | Firmware behaviour |
| --- | --- | --- |
| I²C | SDA 3, SCL 4 | 50 kHz, 200 ms bus timeout for SCD30 clock stretching |
| External QT + TFT power | GPIO7 | Held high through logging deep sleep; low during paused/full/fault sleep |
| TFT ST7789 | CS42, DC40, RESET41; SPI MOSI35, SCK36 | 135×240 controller, rotation 3, 240×135 landscape |
| Backlight | GPIO45 | Off before sleep; display receives sleep command |
| NeoPixel power | GPIO21 | Off |
| D0 | GPIO0, active low | ext0 low wake; view/hold-to-sleep |
| D1 / D2 | GPIO1 / GPIO2, active high | ext1 any-high wake; hotspot / logging |
| SCD30 | `0x61` | Continuous measurement; retained-power wake does not reset the sensor |
| TSL2591 | `0x29` | First-choice light sensor; 100 ms integration, gain adaptation |
| VEML7700 | `0x10` | Fallback if TSL2591 absent; 100 ms, 1/8 gain, corrected lux |
| DS3231 | `0x68` | UTC calendar and coin-cell backup |
| MAX17048 | `0x36` | Battery voltage and estimated state of charge |

GPIO holds are released only after output levels are established on wake. RTC GPIO mode/holds are cleared before reading buttons. Pin 7 must remain powered for SCD30 continuity: it controls the external connector and TFT together. ESP32 wake behaviour follows the [Espressif sleep API](https://docs.espressif.com/projects/esp-idf/en/v4.4/esp32s3/api-reference/system/sleep_modes.html). Confirm pin levels physically during acceptance testing.

The custom SCD30 driver uses STOP-separated command/read operations, word CRC-8, response range checks, and readback of settings. It avoids resetting the module on every ESP32 timer wake. Cold power-up allows two seconds before probing. Settings are written only when changed, avoiding needless nonvolatile sensor writes. Protocol: [Sensirion interface description](https://sensirion.com/media/documents/D7CEEF4A/6165372F/Sensirion_CO2_Sensors_SCD30_Interface_Description.pdf).

Light conversions run as a small nonblocking state machine so a 100 ms integration does not swallow button presses. TSL2591 uses 1×, 25× or 428× gain, with up to two adjustments per reading; a saturated reading is invalid, not a clipped lux value. Conversion is completed before a due record is appended. Modules missing at boot remain unavailable until the next wake/reboot; there is no hot-plug discovery loop.

## Main loop and clock

`App` coordinates sensors, buttons, HTTP, recording and display. Normal awake polling is once per second for sensors and once per second for the TFT, with fast button/web servicing between polls. The processor runs at 80 MHz. The bench environment bypasses deep sleep only.

Logging deadlines use a 64-bit monotonic counter: ESP high-resolution uptime while awake, plus retained elapsed time across sleep. Sleep elapsed time is calculated before setting system UTC from the external RTC. A phone clock correction does not move recording deadlines. If work delays a deadline, the next actual observation is saved and missed slots are skipped, never backfilled with invented readings.

The DS3231 is accepted only when its oscillator-stop flag is clear and its date is in range. The pinned Arduino/ESP-IDF toolchain uses signed 32-bit `time_t`; accepted clock dates are **2020 through 2037**. Extending that range requires a framework/time API upgrade, not just loosening validation. A cold reset never sets the RTC to the compile date. A valid phone time is written to the RTC and read back before being accepted. Without an RTC, phone time lasts through retained deep sleep but not a cold power loss. CSV is UTC; the web page formats local time in the browser.

A cold boot creates a new random session identifier and a boot event with the ESP reset reason. Deep-sleep wake retains the session, schedule, last sensor reading and storage fast-check information. Watchdog/brownout resets restart the session, validate storage, restore NVS settings, and use the external RTC if valid. An interruption may lose the last observation; no software-only check establishes power-failure guarantees.

Settings are a version-tagged, CRC-protected NVS blob. Invalid settings fall back to paused defaults. Hardware setting changes are validated and read back before committing; failed saves attempt to restore old sensor settings. Settings revisions let browser forms reject stale edits. A settings event records the revision and channel mask; the log does **not** contain complete historical configuration snapshots. Save experiment settings separately when reproducibility needs every offset/cadence value.

## Flash and recovery

[partitions.csv](../partitions.csv) reserves:

| Region | Offset | Bytes |
| --- | ---: | ---: |
| NVS | `0x9000` | 20,480 |
| OTA selector data | `0xe000` | 8,192 |
| Single application | `0x10000` | 1,441,792 |
| LittleFS log partition, label `spiffs` | `0x170000` | 1,441,792 |
| Board TinyUF2 factory image | `0x2d0000` | 262,144 |
| Existing factory filesystem, unmounted | `0x310000` | 983,040 |

The historical partition subtype/name `spiffs` is used by the ESP32 LittleFS integration; the actual filesystem is LittleFS. The factory image location matches the board's additional upload image. Web assets live in the application and do not consume log space.

Each observation is a single append to `/records.bin`, followed by flush/close. At least 32 KiB of free space is reserved. On normal deep wake, expected file length and last-record CRC/sequence provide a fast check. On a cold reset or mismatch, the journal is scanned from the start. An incomplete trailing record or invalid final full record can be truncated; corruption in the interior stops writing and retains the file for raw recovery. CRC detects corruption but does not guarantee atomic flash writes. A mount failure only autoformats an entirely `0xff` partition; any nonblank contents are preserved until explicit erase.

CSV/history export validates records and stops at the first invalid record. Raw export preserves bytes without interpreting them. All three exports use bounded chunks and a fixed starting file length while servicing sensor polling/logging between chunks. Slow synchronous socket writes can still delay samples; the acceptance test explicitly checks this. Filesystem mount failure prevents file-level download: recover a complete flash image separately before erasing in that situation.

## Record format: SLW1

Fixed **64 bytes**, little endian, IEEE-754 binary32 floats. CRC-32 uses the standard reflected polynomial `0xedb88320`, initial/final XOR `0xffffffff`, over bytes 0–59.

| Byte offset | Field | Type |
| --- | --- | --- |
| 0 | magic `0x31574c53` / ASCII `SLW1` | uint32 |
| 4 | sequence, increasing within this journal | uint32 |
| 8 | session ID | uint32 |
| 12 | UTC epoch seconds; zero if unset | uint32 |
| 16 | monotonic session uptime seconds | uint32 |
| 20 | channel mask | uint16 |
| 22 | quality flags | uint16 |
| 24 / 28 / 32 | CO₂ ppm / temperature °C / RH % | float ×3 |
| 36 / 40 / 44 | lux / battery volts / battery % | float ×3 |
| 48 | conservative CO₂ sample age bound, seconds; `65535` unknown | uint16 |
| 50 | settings revision | uint16 |
| 52 | event type | uint16 |
| 54 | reserved | uint16 |
| 56 | auxiliary event value | uint32 |
| 60 | CRC-32 | uint32 |

Channel bits: CO₂ `1`, temperature `2`, humidity `4`, light `8`, battery `16` (both voltage and percent). Missing, invalid or unselected measurements are NaN in the binary file and blank in CSV. They are never converted to zero. The CO₂ age bound includes one configured sensor interval because the module does not timestamp its samples.

Quality bits can be combined:

| Bit | Meaning |
| --- | --- |
| 1 | Valid UTC |
| 2 | Within two minutes of sensor power-up / warming |
| 4 | CO₂ unavailable or no valid reading yet |
| 8 | Light unavailable |
| 16 | Battery reading unavailable |
| 32 | Light sensor saturated |
| 64 | Calibration review due after cadence change |
| 128 | CO₂ reading stale |
| 256 | Calibration stabilisation/application session active |

Event values: `0 sample`, `1 clock_set` (auxiliary = previous UTC), `2 settings`, `3 start`, `4 pause`, `5 calibration` (auxiliary = reference ppm), `6 boot` (auxiliary = ESP reset reason). Measurement columns are blank for non-sample CSV rows. Events consume the same 64 bytes as samples. If storage is full/unavailable, settings/time can still change but their audit event cannot be appended.

Raw recovery on a computer:

```sh
python3 scripts/decode_log.py sensor-workshop.bin recovered.csv
```

The decoder never modifies the input or overwrites an existing output. It stops at the first invalid/torn record and returns exit code 2 while preserving the valid CSV prefix. It does not guess past damaged bytes.

## HTTP contract

The AP runs at `192.168.4.1`, has a device-specific SSID/password and allows up to three clients. It is not connected to an upstream Wi-Fi network. DNS directs captive-portal discovery to the local page. No cloud, station credentials or firmware update route is present.

Every POST requires JSON and the per-boot `X-Workshop-Token` returned by `/api/status`. There are no cross-origin access headers. The Wi-Fi password is persisted in NVS and displayed on the device; the dashboard is HTTP on this local WPA2 network. Request bodies are limited to 2 KiB in the handler.

| Method/path | Contract |
| --- | --- |
| GET `/` | Embedded gzip HTML/CSS/JS |
| GET `/api/status` | Live values/nulls, settings, UTC/RTC state, diagnostics, storage, Wi-Fi timeout, calibration state, estimates, token |
| GET `/api/history` | At most approximately 240 downsampled sample points, with sequence/UTC/session/flags; complete observations remain in CSV |
| GET `/api/download` | Streamed CSV of valid records |
| GET `/api/download/raw` | Exact raw journal bytes, including any corrupt tail |
| POST `/api/clock` | `{utc: integer_epoch_seconds}` |
| POST `/api/logging` | `{enabled: boolean}`; blocked during calibration |
| POST `/api/settings` | All settings fields plus `expected_revision`, `asc_acknowledged`, `cadence_acknowledged`; strict ranges/readback |
| POST `/api/wifi/extend` | `{}`; renew configured session timeout |
| POST `/api/calibration/start` | `{}`; start six-minute stability window, never automatically apply |
| POST `/api/calibration/cancel` | `{}`; cancel without changing correction |
| POST `/api/calibration/apply` | `{reference_ppm: 400..2000, confirmed: true}` after stability/readiness checks |
| POST `/api/storage/erase` | `{confirmation: "ERASE"}` while paused and no active calibration |

Settings fields and defaults are defined in `LoggerCore.h` and exposed with explicit names/units in `statusJson()`. The web page submits a complete form. Calibration requires at least five fresh observations; missing/stale data or a sensor I/O error restarts stabilisation. The process ends ten minutes after readiness or after 20 minutes total, whichever comes first. Closing Wi-Fi cancels it. Calibration-related records are flagged; reference gas values should not be mistaken for normal experiment observations.
