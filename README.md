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

**Current print set: v0.7, with corrected Feather component clearance and clear USB/SCREEN SIDE marks. For the standard workshop set, reprint only `03-feather-frame.stl`; the shell and carrier are unchanged. For the personal bare-SCD30 set, also reprint its strengthened snap carrier.** See [Feather reinforcement and orientation](enclosure/FEATHER-MOUNT.md). If upgrading from the older VEML7700 shell, also print `01-shell.stl` for the TSL2591; see [sensor fit details](hardware/LIGHT-SENSOR.md).

For the first test, print the shell separately and the two smaller parts together. Once fit and settings are confirmed, all three can share a plate. See [printing guidance](enclosure/PRINTING.md) for support placement. The optional shared [fit coupon](enclosure/stl/coupon.stl) is outside the production folder. The CAD export script refreshes the three production files on every full export.

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

The **v0.7 OpenSCAD enclosure** restores the Feather's old contact diameters, clears the USB-end LEDs and adds USB/SCREEN SIDE labels while retaining reinforced roots and deeper blind pilots. It retains the TSL2591 roof opening, 92 × 66 × 60.8 mm main body, straight integral feet and downward-facing SCD30. Attach the Feather to its **removable frame** on the table, then slide it in through the open bottom. There are **three printed pieces and ten screws**. The HTML includes **Remove / install Feather**, **Tie access**, **Tie section** and **Pole mount** views alongside individual visibility, explosion and cutaways. The optional [full-wrap mounting tie](enclosure/MOUNTING.md) follows raised guides at all four corners, bringing the overall envelope to 95.2 × 69.2 × 60.8 mm. Each battery tie has a curved return and a second eyelet; the battery end stops remain removed. [Feather mounting drawing](enclosure/feather-mounting.pdf) · [Light-sensor fit drawing](enclosure/light-sensor-fit.pdf) · [Compare v0.2](enclosure/archive/v0.2/model.html).

A [reproducible thermal screening model](enclosure/thermal/README.md) includes conduction, warm air, radiation and sensor self-heating. Slots around the sensor mounting region reduce one heat path, but the estimate still flags potentially significant warming. Physical measurements are needed before treating temperature readings as ambient. [Thermal review PDF](enclosure/thermal/thermal-review.pdf).

An earlier shell printed well in PLA, and Erez's unidentified screws fitted the old Feather pilots, but a post broke when unscrewed. The v0.6 frame interfered with two LED packages in the detailed model; v0.7 removes that interference. The revised frame, specified BOM fasteners and complete assembly still need a pilot trial before a classroom batch. Firmware and teaching materials are still to be developed.
