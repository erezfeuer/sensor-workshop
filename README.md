# Sensor Workshop

A three-day, hands-on microcontroller workshop with Erez Feuer, Yair Mau, and Elad Levintal. Yair and Elad are from Ben-Gurion University.

Students assemble the same battery-powered environmental monitor without soldering, then develop their own software. The intended device measures CO₂, temperature, humidity, and ambient light, displays readings, creates a Wi-Fi hotspot, and offers a browser interface for controls, data logging, and CSV downloads.

## Hardware planning

- [Proposed bill of materials and compatibility notes](hardware/BOM.md)
- [BOM as CSV](hardware/bom.csv)

Current proposal: Adafruit's own ESP32-S3 Feather, SCD30 sensor breakout, VEML7700 light sensor, and an I²C OLED, connected through STEMMA QT / Qwiic cables. Batteries will be purchased locally in Israel. An RTC is optional.

The BOM is a researched proposal, not a hardware-tested design. The exact local battery and final component selection will determine the enclosure. Firmware, enclosure CAD, and teaching materials are still to be developed.
