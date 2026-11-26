# TFT views and refresh

## Four views — v0.1.3

Press **D0 Next** to cycle through these views. D1 opens/closes the phone hotspot, and D2 starts/pauses logging. While the hotspot is open, its QR screen takes precedence; press **D1 Done** to return to the readings.

| View | Contents |
| --- | --- |
| CO2 | Large ppm value, recording interval/state, and sensor/clock warnings |
| Environment | Temperature and humidity side by side, with light below; all three values use the larger 3× font |
| Logger | Logging state; interval and countdown in 2× text; selected channels, separate CO₂ measurement cadence |
| Battery / Storage | Record count, free flash, estimated storage/runtime, UTC clock, and battery voltage |

`Next in … s` counts down to the next **saved observation**, not every continuous SCD30 conversion. It reads `retained.nextLogMs`, the same monotonic deadline used by the logger. Remaining milliseconds round up to seconds; when due but still waiting for a light conversion, the view says `Reading now...`. Phone/RTC clock adjustments do not move this deadline. The next interval appears after the logger advances its schedule. Paused logging shows `D2: start logging`, and unhealthy/full storage suppresses the countdown. No scheduler, sensor cadence, sleep timeout or stored setting changes are needed for these views.

The screen continues to compose once per second while awake, with immediate redraws on button actions. Toasts temporarily replace only the bottom information line. View titles and `1/4`–`4/4` identify each page; the battery percentage remains in the header. USB `j` and `/api/status` now include `display.page` (zero based), `display.page_count` and `display.view` (`PHONE` while the QR screen is open).

Both PlatformIO environments built and passed binary/partition/dashboard checks. Normal `feather` was uploaded with flash hash verification. USB reported v0.1.3, four views, buffered partial updates, live SCD30/TSL2591 readings, a valid RTC, and healthy storage. Recording remained enabled at the existing 60-second interval, and the saved settings revision was unchanged. [Targeted update checks](views-validation.json). All live channels were present; the post-reset sensor-error counter stayed at 1 throughout observation. Confirmation of the new views and countdown on the physical display remains pending. The initial logger and v0.1.2 refresh results below remain historical checks, rather than repeated full acceptance tests.

## Buffered refresh — v0.1.2

The once-per-second blink came from `tft.fillScreen(BG)` followed by many individual text and shape writes. The panel displayed that intermediate blank image before the new content arrived.

The firmware now draws into a 240×135 RGB565 canvas. It compares each completed row with the previously displayed image, then sends contiguous groups of changed rows. Background pixels and foreground pixels arrive together; unchanged frames do not write to the TFT. The QR matrix is cached. At screen startup the backlight remains off until the first image is complete. Refresh cadence remains once per second, with immediate redraws on button actions and notices.

The two buffers total 129,600 bytes and are allocated only when a screen is opened, so timer-only logging wakes do not allocate them. The history allocation prefers PSRAM. If history allocation fails, the full canvas can still be sent without a visible erase; a canvas allocation failure leaves logging active and reports the display failure over USB.

## Observed on the assembled device, 26 November 2026

The normal `feather` firmware was uploaded with PlatformIO and its flash hash verified. USB `j` reported both buffering and changed-row updates active. The original settings, valid RTC and healthy journal were retained; 57 earlier records remained counted, with two additional boot events after upload/restart.

- Reading-screen changes sent 1,680–13,440 pixels in the sampled updates, versus 32,400 pixels for a complete screen. Their presentation times were approximately 7.8–18.3 ms, including row comparison and copying.
- The maximum presentation time observed since boot was 36.5 ms. This is a software timing, not a camera measurement of LCD scanout or a worst-case guarantee.
- Identical reading and QR screens sent zero pixels. Skipped-frame counters increased while the QR screen remained displayed.
- Composition happens off-screen: sampled reading composition took approximately 11–48 ms; QR composition peaked at 61 ms on first generation and settled around 17 ms.
- With the hotspot running, diagnostics reported about 275 KB free heap and 1.95 MB free PSRAM. Live sensor values, RTC and the journal remained healthy; the existing startup sensor-error count did not increase during this check.

[Recorded diagnostics and build hashes](display-validation.json). **Visual check passed:** on 26 November 2026, Erez confirmed, “Yes, it looks steady now.” This confirms the reported once-per-second blink is resolved on the assembled prototype; it is not an instrumented LCD scanout measurement.

To inspect refresh behaviour over USB, send `j` and read the `display` object. `last_pixels_sent: 0` means the last composed image matched the displayed one. `frames_skipped` counts such updates; `max_present_us` includes the initial full image. These diagnostics do not change the logging configuration.
