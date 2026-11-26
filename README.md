# Sensor Workshop

A three-day, hands-on microcontroller workshop by Erez Feuer, with Yair Mau and Elad Levintal.

Students assemble the same battery-powered environmental monitor without soldering, then develop their own software. The intended device measures CO₂, temperature, humidity, and ambient light, displays readings, creates a Wi-Fi hotspot, and offers a browser interface for controls, data logging, and CSV downloads.

## Files to print

**Erez's bare-SCD30 prototype:** use **[prototype-stls/bare-scd30/](prototype-stls/bare-scd30/)** for your complete three-file set. It includes the TSL2591 shell, reinforced Feather frame and a snap-in carrier for the bare Sensirion module. [Personal snap-holder guide](enclosure/variants/bare-scd30/README.md) · [Personal interactive model](enclosure/variants/bare-scd30/model.html). The standard workshop files below still use the Adafruit QT SCD30 breakout.

**[production-stls/](production-stls/)** contains exactly the three separate STL files for one device. Print **one of each**, at **100% scale in millimetres**, keeping the supplied orientations:

| File | Bed-facing surface |
| --- | --- |
| [01-shell.stl](production-stls/01-shell.stl) | Exterior roof |
| [02-sensor-carrier.stl](production-stls/02-sensor-carrier.stl) | Flat upper face; sensor bosses point up |
| [03-feather-frame.stl](production-stls/03-feather-frame.stl) | Flat rear face; mounting pads point up |

**Current print set: v0.8.1. Reprint only `03-feather-frame.stl` from v0.8.** Both screw collars are now reinforced right up to the PCB, with local clearance for nearby components. Hole centres, locating pins, PCB seat plane and the open battery-lead notch are retained. Both print folders contain the same frame; the shell and both carriers are unchanged. [Before/after collar sections](enclosure/feather-collars.pdf) · [Mount details](enclosure/FEATHER-MOUNT.md).

For the first test, print the shell separately and the two smaller parts together. Once fit and settings are confirmed, all three can share a plate. See [printing guidance](enclosure/PRINTING.md) for support placement. The optional shared [fit coupon](enclosure/stl/coupon.stl) is outside the production folder. The CAD export script refreshes the three production files on every full export.

## Firmware

**[PlatformIO project](firmware/README.md)** · **[Interactive dashboard preview](firmware/preview.html)** (download/open the HTML; simulated readings)

The first firmware provides internal-flash logging, a temporary Wi-Fi hotspot with a QR code, phone-to-RTC clock setting, plots and CSV downloads, guided CO₂ calibration, and button-controlled TFT/deep sleep. The prototype's 3,500 mAh cell is the default in its editable battery/storage calculator. The initial estimate is about **4.9 days** at one-minute logging with the SCD30 at a two-second cadence; power and storage assumptions are [documented here](firmware/docs/POWER.md). This is an unmeasured estimate. **Firmware v0.1.3 is installed, with larger temperature/humidity/light values and a logger-settings view with a live countdown to the next record.** Buffered TFT updates keep the refresh steady. [Display views](firmware/docs/DISPLAY.md). The initial v0.1.1 bench checks passed: live sensors, clock setting, logging and dashboard/CSV downloads worked. [Hardware results](firmware/docs/hardware-validation.json). Battery runtime, measurement accuracy and long-term reliability remain unqualified.

## Hardware planning

- [Proposed bill of materials and compatibility notes](hardware/BOM.md)
- [BOM as CSV](hardware/bom.csv)
- **[TSL2591 prototype: sensor comparison, enclosure changes and first checks](hardware/LIGHT-SENSOR.md)**
- **[Mechanical shopping list — screw sizes, washers, zip ties and quantities](enclosure/MECHANICAL-BOM.md)** ([CSV](enclosure/hardware.csv))
- [One-device distributor comparison and cart imports](hardware/ordering/README.md)
- [Enclosure design, printing and assembly](enclosure/README.md)
- [Interactive 3D model — open the downloaded HTML in a browser](enclosure/model.html)
- [Enclosure design review and cross-sections (PDF)](enclosure/design-review.pdf)

Selected controller: Adafruit ESP32-S3 Reverse TFT Feather, with a built-in colour display, three buttons, 4 MB flash, and 2 MB PSRAM. The supplied prototype uses an SCD30, Adafruit TSL2591 QT light sensor, and required DS3231 RTC connected through three STEMMA QT / Qwiic cables. VEML7700 remains the original class-order comparison option; the final class selection follows the prototype trial. Adafruit and SparkFun parts are both acceptable; the original ordering comparison includes SparkFun's assorted Qwiic cable kit, while this prototype uses the supplied stock. Both the rechargeable battery and RTC backup cell will be purchased locally in Israel.

The **v0.8.1 OpenSCAD enclosure** reinforces both Feather screw collars, with local relief around the LED and radio module. It retains the fitted hole/pin centres, seat plane, open battery-lead notch, RTC LED clearance, USB/SCREEN SIDE labels, reinforced roots and deeper blind pilots. It retains the TSL2591 roof opening, 92 × 66 × 60.8 mm main body, straight integral feet and downward-facing SCD30. Attach the Feather to its **removable frame** on the table, then slide it in through the open bottom. There are **three printed pieces and ten screws**. The HTML includes **Remove / install Feather**, **Tie access**, **Tie section**, **Pole mount** and **Battery cable** views alongside individual visibility, explosion and cutaways. The optional [full-wrap mounting tie](enclosure/MOUNTING.md) follows raised guides at all four corners, bringing the overall envelope to 95.2 × 69.2 × 60.8 mm. Each battery tie has a curved return and a second eyelet; the battery end stops remain removed. [Feather mounting drawing](enclosure/feather-mounting.pdf) · [Light-sensor fit drawing](enclosure/light-sensor-fit.pdf) · [Compare v0.2](enclosure/archive/v0.2/model.html).

A [reproducible thermal screening model](enclosure/thermal/README.md) includes conduction, warm air, radiation and sensor self-heating. Slots around the sensor mounting region reduce one heat path, but the estimate still flags potentially significant warming. Physical measurements are needed before treating temperature readings as ambient. [Thermal review PDF](enclosure/thermal/thermal-review.pdf).

Erez has printed and assembled the v0.7.1 set, reporting that almost everything fitted. The battery lead could be trapped at the frame/cover seam; v0.8 addresses that crossing. The v0.8 print revealed that one screw collar was still thin. v0.8.1 widens both collars and adds regression checks through their first 2 mm, alongside the existing hole and component checks. Seating and repeated-removal strength still need a physical trial. Firmware v0.1.3 is running on the assembled prototype, with four readable TFT views and a logging countdown following the initial sensor, logging and browser checks; remaining hardware acceptance work is documented. Teaching materials remain to be developed.
