# TFT refresh — v0.1.2

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

[Recorded diagnostics and build hashes](display-validation.json). The user has been asked to confirm the visible result; software timings alone cannot establish the absence of perceived flicker or tearing.

To inspect refresh behaviour over USB, send `j` and read the `display` object. `last_pixels_sent: 0` means the last composed image matched the displayed one. `frames_skipped` counts such updates; `max_present_us` includes the initial full image. These diagnostics do not change the logging configuration.
