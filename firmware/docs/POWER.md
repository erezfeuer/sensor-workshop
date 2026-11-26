# Battery and storage estimates

These are planning calculations, **not measurements of the assembled device**. Erez has a power profiler; the dashboard allows the uncertain current allowances to be replaced after profiling. The default battery is the supplied **3,500 mAh, 3.7 V nominal 1S Li-ion cell**. Capacity does not imply a different enclosure envelope; check the actual wrapped cell against the existing battery pocket.

## Default result

With one record per minute, a two-second SCD30 cadence, ten minutes of Wi-Fi/display use and ten additional minutes of screen-only use per day:

| Quantity | Estimate |
| --- | ---: |
| Usable capacity allowance | 80% × 3,500 = 2,800 mAh |
| Continuously powered SCD30 | 19.00 mA |
| Board, wakeups, display and Wi-Fi, averaged | 2.58 mA |
| RTC, sleeping light/display and breakout allowances | 2.22 mA |
| Average battery current | 23.81 mA |
| Runtime from full | 117.6 hours / **4.9 days** |
| Sensitivity range, using 0.7–1.5× modelled current | **3.3–7.0 days** |

The range is not a confidence interval or a battery guarantee. It does not cover every possible error in the assumptions. USB charging invalidates a discharge-only estimate. Temperature, ageing, cell protection cutoff, regulator dropout, enclosure heating and module LEDs all matter. The fuel gauge supplies an estimated state of charge, not a measured load current or a learned remaining-runtime prediction.

Keeping the same recording interval and changing the SCD30 cadence to 30 seconds gives about **10.41 mA / 11.2 days** in this model. This is a scenario, not an automatic optimisation: Sensirion calls for recalibration when the measurement interval changes, and temperature self-heating also changes. The firmware therefore requires acknowledgement, marks calibration as due, and does not silently change the sensor cadence when Wi-Fi opens or the log interval changes.

## Published figures versus engineering allowances

| Item | Value used | Basis |
| --- | ---: | --- |
| SCD30 | 19 mA at 2 s; 5.6 mA at 30 s | [Sensirion datasheet](https://sensirion.com/media/documents/4EAF6AF8/61652C3C/Sensirion_CO2_Sensors_SCD30_Datasheet.pdf), [low-power application note](https://sensirion.com/media/documents/0FEA2450/61652EF9/Sensirion_CO2_Sensors_SCD30_Low_Power_Mode.pdf) |
| Sleeping Feather board | 0.1 mA | Allowance near the upper end of the board's published all-off 40–100 µA range; the external rail-on configuration must be measured. [Adafruit power guide](https://learn.adafruit.com/esp32-s3-reverse-tft-feather/power-management) |
| CPU awake, Wi-Fi off | 45 mA | Unmeasured board allowance at the firmware's 80 MHz setting |
| Display/backlight increment | 25 mA | Unmeasured allowance; applied only while the screen is on |
| Board with AP and display | 160 mA | Unmeasured allowance, including CPU/backlight, excluding external sensors |
| Wake time per record | 1.2 s | Firmware minimum awake budget for normal retained-power timer wakes; physical timing pending |
| DS3231, main power | 0.2 mA | Typical active supply figure; coin-cell backup does not remove this load when VCC is present. [Analog Devices datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/DS3231.pdf) |
| TSL2591 sleep | 0.004 mA | Published sleep figure; brief active conversions are covered by the breakout allowance. [ams OSRAM datasheet](https://look.ams-osram.com/m/c901de8e97608f8/original/TSL2591-DS000338.pdf) |
| LCD controller sleeping | 0.020 mA | Provisional allowance, not a measurement of the Feather display assembly |
| Breakout LEDs/regulators | 2 mA | Provisional aggregate allowance; bare SCD30 and Adafruit breakout differ |

The MAX17048 is already included in the sleeping/awake board allowances, not added twice. Its published active figure is 23 µA; see [Analog Devices MAX17048](https://www.analog.com/en/products/max17048.html). The VEML7700 fallback currently shares the small light/overhead allowance; it has not been separately profiled.

The regulator is linear, so this first model approximates rail current as battery current, with board/quiescent allowances and 80% usable capacity. It does not multiply the cell's mAh by its nominal voltage and treat that result as mAh at 3.3 V. Charging losses are not part of discharge runtime.

## Equations

For sensor cadence `c` between 2 and 60 seconds, a two-point approximation is:

```text
I_scd = 4.642857 + 28.714286 / c       [mA]
f_wifi = wifi_minutes_per_day / 1440
f_screen = screen_only_minutes_per_day / 1440
f_wake = (1 - f_wifi - f_screen) × min(1, wake_seconds / log_interval_seconds)
f_idle = 1 - f_wifi - f_screen - f_wake
I_board = f_idle × I_sleep + f_wake × I_cpu
          + f_screen × (I_cpu + I_display) + f_wifi × I_wifi_board
I_total = I_scd + I_board + I_breakouts + I_rtc + I_light_sleep + I_lcd_sleep
full_hours = capacity_mAh × usable_fraction / I_total
remaining_hours = full_hours × fuel_gauge_percent / 100
```

Duty fractions are clamped to avoid totals above 100%; Wi-Fi takes precedence over screen-only time. The SCD expression is a fitted approximation through two published figures, not a manufacturer curve. The JS calculator and ESP32 estimate use the same equations and defaults; tests compare their default result. Editing calculator inputs does not change device settings. Advanced scenario inputs are temporary and reset when the page is reloaded.

## Storage is a separate limit

The 4 MB flash holds firmware, boot/recovery information and filesystems. This layout allocates **1,408 KiB** to the log filesystem. Every sample or audit event uses **64 bytes**, including CRC. The dashboard uses current filesystem free bytes, subtracts a **32 KiB reserve**, then computes:

```text
additional_records = floor(max(0, free_bytes - 32768) / 64)
storage_hours = additional_records × log_interval_seconds / 3600
```

The raw partition ceiling is 22,016 records after the reserve: **15.29 days at one-minute intervals**. Actual filesystem metadata, existing observations and future clock/settings/calibration events reduce that budget; a newly formatted device should show roughly 15 days, to be checked on hardware. Fewer selected channels leave blank values but do not make smaller records. Filesystem allocations are block-based, so the byte estimate is a budget rather than an exact promise of the last writable record.

Storage stops accepting new records when full. It never automatically overwrites or deletes old observations. Pausing, exporting, and explicitly erasing makes space again. Power runtime and storage horizon are displayed separately; the calculator identifies which modelled limit arrives first. The on-device TFT uses the fixed default usage assumptions plus current settings and fuel gauge; the browser permits what-if scenarios.

## Why not switch every peripheral off between records?

The Feather can cut the shared **STEMMA QT / TFT rail** with `TFT_I2C_POWER` (GPIO7). With the current wiring this switches the entire external chain together, not the SCD30 independently. The MAX17048 fuel gauge remains supplied separately. [Adafruit power management](https://learn.adafruit.com/esp32-s3-reverse-tft-feather/power-management)

The firmware already stops the SCD30 and cuts that rail when entering sleep with logging paused (also when storage is full or unhealthy). It releases SDA/SCL to inputs before shutdown and holds the power GPIO low during deep sleep. The RTC keeps time from its coin cell; its main-power removal is an intended use of the backup supply. [DS3231 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/DS3231.pdf)

During logging, the ESP32 sleeps but keeps the rail on. The light sensor is disabled between conversions and the display/backlight sleep. Repeatedly powering the light sensor off would require reinitialisation and a fresh integration on waking; it is already a small load. Cutting the SCD30 also removes temperature/humidity measurements: the public interface does not provide a separate temperature/humidity-only measurement command. [SCD30 interface, sections 1.4.1–1.4.5](https://sensirion.com/media/documents/D7CEEF4A/6165372F/Sensirion_CO2_Sensors_SCD30_Interface_Description.pdf)

For economical SCD30 logging, Sensirion recommends changing the internal measurement interval rather than cycling power. Restarting also changes self-heating, affecting temperature/humidity compensation. The note's approximately ten-minute thermal settling procedure is for determining temperature offset, not a mandatory wait before every record. [SCD30 low-power note](https://sensirion.com/media/documents/0FEA2450/61652EF9/Sensirion_CO2_Sensors_SCD30_Low_Power_Mode.pdf)

The specified boot time of less than two seconds establishes communication readiness, not settled measurement accuracy. Power loss **does not erase the FRC calibration correction**; its reference-value readback is volatile. It does interrupt initial ASC learning, which needs at least seven continuous days and daily fresh-air exposure. ASC is off by default in this firmware, so ASC is not the main obstacle here. [SCD30 interface, pages 2 and 13–14](https://sensirion.com/media/documents/D7CEEF4A/6165372F/Sensirion_CO2_Sensors_SCD30_Interface_Description.pdf)

A future **experimental burst mode** could power up, settle, record and turn everything off for a long interval. Before treating those records as reliable, compare repeated starts with a continuously powered reference in the same environment, including temperature/humidity and changing CO₂ conditions. Measure the required settling window and integrate battery-side energy over whole cycles. The current two-minute firmware warming flag is an engineering marker, not a validated startup specification. The calculator therefore continues to model retained sensor power while logging; simply setting its SCD30 current to zero would overstate runtime. No burst mode or new shutdown behaviour was added in this mechanical revision.

## Profiling later

Measure battery-side current with USB disconnected: paused sleep, logging sleep with the sensor rail held on, timer wake, screen-only use, and AP plus download. Integrate several full SCD30 cycles at each cadence. Record average wake duration and compare both bare-SCD30 prototype and intended class breakout. Update the advanced dashboard allowances, then replace the corresponding `PowerInputs` and HTML defaults together. Check the prediction against a complete discharge trial before reporting workshop runtime as measured.
