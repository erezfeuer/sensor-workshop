# Sensor Workshop

A three-day, hands-on microcontroller workshop with Erez Feuer, Yair Mau, and Elad Levintal. Yair and Elad are from Ben-Gurion University.

Students assemble the same battery-powered environmental monitor without soldering, then develop their own software. The intended device measures CO₂, temperature, humidity, and ambient light, displays readings, creates a Wi-Fi hotspot, and offers a browser interface for controls, data logging, and CSV downloads.

## Hardware planning

- [Proposed bill of materials and compatibility notes](hardware/BOM.md)
- [BOM as CSV](hardware/bom.csv)
- [One-device distributor comparison and cart imports](hardware/ordering/README.md)
- [Enclosure design, printing and assembly](enclosure/README.md)
- [Interactive 3D model — open the downloaded HTML in a browser](enclosure/model.html)
- [Enclosure design review and cross-sections (PDF)](enclosure/design-review.pdf)

Selected controller: Adafruit ESP32-S3 Reverse TFT Feather, with a built-in colour display, three buttons, 4 MB flash, and 2 MB PSRAM. An SCD30, VEML7700 light sensor, and required DS3231 RTC connect through three STEMMA QT / Qwiic cables. Adafruit and SparkFun parts are both acceptable; the prototype order includes SparkFun's assorted Qwiic cable kit. Both the rechargeable battery and RTC backup cell will be purchased locally in Israel.

The first OpenSCAD enclosure prototype has a top-mounted light sensor, a shaded lower SCD30 tray, a front display, four feet and a protected 18650 battery bay. It includes printable STLs, mounting drawings, assembly instructions and an offline HTML viewer with component visibility and an explosion slider. The battery design envelope is Ø20 × 72 mm; the actual local pack and inline switch need physical fit checks.

The BOM and CAD are source-based proposals, not hardware-tested designs. Start with the fit coupon and one pilot device before printing or ordering a classroom batch. Firmware and teaching materials are still to be developed.
