# Sensor Workshop

A three-day, hands-on microcontroller workshop by Erez Feuer, with Yair Mau and Elad Levintal.

Students assemble the same battery-powered environmental monitor without soldering, then develop their own software. The intended device measures CO₂, temperature, humidity, and ambient light, displays readings, creates a Wi-Fi hotspot, and offers a browser interface for controls, data logging, and CSV downloads.

## Files to print

**[production-stls/](production-stls/)** contains exactly the three separate STL files for one device. Print **one of each**, at **100% scale in millimetres**, keeping the supplied orientations:

| File | Bed-facing surface |
| --- | --- |
| [01-shell.stl](production-stls/01-shell.stl) | Exterior roof |
| [02-sensor-carrier.stl](production-stls/02-sensor-carrier.stl) | Flat upper face; sensor bosses point up |
| [03-feather-frame.stl](production-stls/03-feather-frame.stl) | Flat rear face; mounting pads point up |

**Updating the first printed prototype to v0.4: reprint only `01-shell.stl`. The two smaller parts and all screw-hole sizes are unchanged.**

For the first test, print the shell separately and the two smaller parts together. Once fit and settings are confirmed, all three can share a plate. See [printing guidance](enclosure/PRINTING.md) for support placement. The optional shared [fit coupon](enclosure/stl/coupon.stl) is outside the production folder. The CAD export script refreshes the three production files on every full export.

## Hardware planning

- [Proposed bill of materials and compatibility notes](hardware/BOM.md)
- [BOM as CSV](hardware/bom.csv)
- **[Mechanical shopping list — screw sizes, washers, zip ties and quantities](enclosure/MECHANICAL-BOM.md)** ([CSV](enclosure/hardware.csv))
- [One-device distributor comparison and cart imports](hardware/ordering/README.md)
- [Enclosure design, printing and assembly](enclosure/README.md)
- [Interactive 3D model — open the downloaded HTML in a browser](enclosure/model.html)
- [Enclosure design review and cross-sections (PDF)](enclosure/design-review.pdf)

Selected controller: Adafruit ESP32-S3 Reverse TFT Feather, with a built-in colour display, three buttons, 4 MB flash, and 2 MB PSRAM. An SCD30, VEML7700 light sensor, and required DS3231 RTC connect through three STEMMA QT / Qwiic cables. Adafruit and SparkFun parts are both acceptable; the prototype order includes SparkFun's assorted Qwiic cable kit. Both the rechargeable battery and RTC backup cell will be purchased locally in Israel.

The **v0.4 OpenSCAD enclosure** retains the 92 × 66 × 60.8 mm main body, straight integral feet and downward-facing SCD30. A small **removable Feather frame** fixes the inaccessible side screws: attach the board on the table, then slide it in through the open bottom. There are **three printed pieces and ten screws**. The HTML includes **Remove / install Feather**, **Tie access**, **Tie section** and **Pole mount** views alongside individual visibility, explosion and cutaways. The optional [full-wrap mounting tie](enclosure/MOUNTING.md) follows raised guides at all four corners, bringing the overall envelope to 95.2 × 69.2 × 60.8 mm. Each battery tie now has a curved return and a second eyelet; the battery end stops remain removed. Only the shell needs reprinting after the first PLA trial; the carrier, Feather frame and screw-hole sizes are unchanged. [Compare v0.2](enclosure/archive/v0.2/model.html).

A [reproducible thermal screening model](enclosure/thermal/README.md) includes conduction, warm air, radiation and sensor self-heating. Slots around the sensor mounting region reduce one heat path, but the estimate still flags potentially significant warming. Physical measurements are needed before treating temperature readings as ambient. [Thermal review PDF](enclosure/thermal/thermal-review.pdf).

The BOM and CAD are source-based proposals, not hardware-tested designs. Start with the fit coupon and one pilot device before printing or ordering a classroom batch. Firmware and teaching materials are still to be developed.
