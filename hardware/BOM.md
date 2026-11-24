# Proposed bill of materials

Supplier listings researched **12 November 2026**. These are retrieved product-page and search-index snapshots, some cached, rather than reserved inventory or live quotations. Prices are single-unit USD before shipping and taxes. Delivery eligibility and the final price for Israel must be checked in the distributor cart.

The selected controller is the **Adafruit ESP32-S3 Reverse TFT Feather, product 5691**. It combines the microcontroller, colour screen, and three buttons. The **DS3231 RTC is included in every device**. Adafruit and SparkFun are both acceptable manufacturers. Both batteries will be purchased locally in Israel. No purchases have been made.

## Supplied prototype — 24 November 2026

Elad supplied the prototype electronics, with **Adafruit TSL2591 STEMMA QT (1980)** replacing the planned VEML7700. Erez confirmed the two-socket/four-hole QT version. **Use one light sensor, not both.** The current v0.5 production shell fits TSL2591. [Comparison, mechanical changes and prototype checks](LIGHT-SENSOR.md).

| Prototype substitution | Qty | Reference USD | Adafruit | Digi-Key | Mouser |
| --- | ---: | ---: | --- | --- | --- |
| TSL2591 light sensor; assembled STEMMA QT board; replaces 4162 | 1 from supplied stock | 6.95 | [1980](https://www.adafruit.com/product/1980) | [1528-1037-ND](https://www.digikey.com/en/products/detail/adafruit-industries-llc/1980/4990786) | [485-1980](https://www.mouser.com/en/ProductDetail/Adafruit/1980?qs=GURawfaeGuBXNh1gLjQA3Q%3D%3D) |

The original comparison and distributor import files below retain VEML7700 pending a class-wide decision. With TSL2591, the four-board reference subtotal would be **$104.80** instead of $102.80. No new order is needed for the supplied prototype. The CSV has a separate `quantity_in_tsl2591_prototype` column to avoid counting both alternatives.

## Original class-order comparison and supplier links

Each distributor link identifies the same manufacturer part, not a bare sensor or a substitute. Quantities are for one device except the shared cable assortment. The price column is a reference unit price; distributor-specific observations are in [bom.csv](bom.csv).

| Component | Qty | Reference USD | Adafruit | Digi-Key | Mouser |
| --- | ---: | ---: | --- | --- | --- |
| ESP32-S3 Reverse TFT Feather; 1.14-inch 240 × 135 colour display; 4 MB flash / 2 MB PSRAM; PCB antenna | 1 | 24.95 | [5691](https://www.adafruit.com/product/5691) | [1528-5691-ND](https://www.digikey.com/en/products/detail/adafruit-industries-llc/5691/18627502) | [485-5691](https://www.mouser.com/en/ProductDetail/Adafruit/5691?qs=mELouGlnn3eeALy2e3r3sw%3D%3D) |
| SCD30 CO₂, temperature, and humidity breakout; assembled STEMMA QT board | 1 | 58.95 | [4867](https://www.adafruit.com/product/4867) | [1528-4867-ND](https://www.digikey.com/en/products/detail/adafruit-industries-llc/4867/13627674) | [485-4867](https://www.mouser.com/en/ProductDetail/Adafruit/4867?qs=pBJMDPsKWf0ru2aWSWVb%2FA%3D%3D) |
| VEML7700 ambient light sensor; STEMMA QT revision | 1 | 4.95 | [4162](https://www.adafruit.com/product/4162) | [1528-2891-ND](https://www.digikey.com/en/products/detail/adafruit-industries-llc/4162/9997696) | [485-4162](https://www.mouser.com/en/ProductDetail/Adafruit/4162?qs=unwgFEO1A6urZiNnCPSvkw%3D%3D) |
| DS3231 Precision RTC; STEMMA QT breakout | 1 | 13.95 | [5188](https://www.adafruit.com/product/5188) | [1528-5188-ND](https://www.digikey.com/en/products/detail/adafruit-industries-llc/5188/15189155) | [485-5188](https://www.mouser.com/en/ProductDetail/Adafruit/5188?qs=TCDPyi3sCW0TSTr1Xi7pUg%3D%3D) |
| [SparkFun Qwiic Cable Kit, KIT-15081](https://www.sparkfun.com/sparkfun-qwiic-cable-kit.html), 10 assorted cables for prototyping | 1 shared kit | 12.95 | Exact kit not found | [1568-15081-ND](https://www.digikey.com/en/products/detail/sparkfun-electronics/15081/9770723) | [474-KIT-15081](https://www.mouser.com/en/ProductDetail/SparkFun/KIT-15081?qs=0lSvoLzn4L8uNN%252B5TDrwLw%3D%3D) |
| Final QT-to-QT cables; trial lengths 100 + 50 + 100 mm | 3/device | TBD | See cable options below | Bulk order after pilot fit | Bulk order after pilot fit |
| Protected prewired 1S 18650 battery, approximately 2,200 mAh; Ø20 × 72 mm design envelope | 1 | TBD | Local purchase in Israel | Local purchase in Israel | Local purchase in Israel |
| CR1220, 3 V, non-rechargeable RTC backup coin cell | 1 | TBD | Local purchase in Israel | Local purchase in Israel | Local purchase in Israel |
| [Printed enclosure and mechanical hardware](../enclosure/MECHANICAL-BOM.md) | 1 set | TBD | Local fabrication / fastener supplier | Local fabrication / fastener supplier | Local fabrication / fastener supplier |

The four per-device priced items total **$102.80**, including the RTC, before QT cables, batteries, and enclosure. USB cables are excluded from procurement as requested; programming uses an existing USB data cable.

For the requested **one-device comparison**, each distributor list includes those four boards plus **one SparkFun cable assortment**, for a reference subtotal of **$115.75**. The assortment supplies the prototype's three QT connections, so the comparison does not also buy three individual cables. It is a shared prototyping expense, not a recommendation to buy an assortment for every student. See [ordering files and cart status](ordering/README.md).

All five comparison items were listed in stock at Digi-Key and Mouser in the retrieved listings. For the four boards, the observed Digi-Key / Mouser counts were: Feather **1,730 / 214**, SCD30 **139 / 16**, VEML7700 **536 / 324**, RTC **748 / 158**. These counts may be stale; Mouser's SCD30 listing in particular should be rechecked before a class order. Adafruit listed the Feather at **34** and SCD30 at **86**, with the light sensor and RTC also in stock. The battery switch was removed in enclosure revision v0.2 at the workshop organizer’s request.

## Cable procurement

SparkFun's **KIT-15081** is the remembered assortment: ten cables of mixed lengths, including jumper-ended styles. It is not ten identical QT-to-QT leads. Use only the QT-to-QT leads in the student device. Digi-Key currently identifies this kit as manufacturer part **15081**, with ordering code **1568-15081-ND**; Mouser retains **KIT-15081**.

Use one assortment to try the component arrangement. Then buy the selected lengths in bulk: **three cables per device plus approximately 10% spares**, rounded up. The [v0.5 enclosure](../enclosure/README.md) proposes **100 mm Feather→RTC, 50 mm RTC→light sensor, and 100 mm light sensor→SCD30**. Confirm plug clearance, bend radius and carrier-removal slack with the pilot hardware before freezing the lengths:

| Cable option | Manufacturer link | Reference USD | Observation |
| --- | --- | ---: | --- |
| Flexible Qwiic, 50 mm | [SparkFun PRT-17260](https://www.sparkfun.com/flexible-qwiic-cable-50mm.html) | 1.50 | Listed in stock |
| Flexible Qwiic, 100 mm | [SparkFun PRT-17259](https://www.sparkfun.com/flexible-qwiic-cable-100mm.html) | 1.95 | Listed in stock |
| Flexible Qwiic, 200 mm | [SparkFun PRT-17258](https://www.sparkfun.com/flexible-qwiic-cable-200mm.html) | 1.95 | Listed in stock |
| Standard STEMMA QT / Qwiic, 100 mm | [Adafruit 4210](https://www.adafruit.com/product/4210), [Digi-Key 1528-4210-ND](https://www.digikey.com/en/products/detail/adafruit-industries-llc/4210/10230021) | 0.95 | Digi-Key listed stock; Adafruit direct out of stock |

These are alternatives for the later bulk order, excluded from the comparison imports. Purchase preassembled **4-pin JST-SH, 1 mm-pitch, QT-to-QT cables**, not loose connectors requiring crimping or soldering.

## Controller and firmware implications

The chosen Feather provides native **USB-C**, Wi-Fi, a battery connector and charger, a MAX17048 battery monitor, STEMMA QT, and a factory-connected SPI colour display. It needs no soldered headers or display wiring. Board plus screen costs **$24.95**, saving **$12.50** against the previous $17.50 Feather plus $19.95 separate OLED. The reverse layout places the screen and three buttons opposite the connectors, which suits an enclosure front panel. [Product](https://www.adafruit.com/product/5691), [overview](https://learn.adafruit.com/esp32-s3-reverse-tft-feather/overview)

Native USB avoids a separate USB-to-UART bridge. Most modern Windows, macOS, and Linux systems support USB CDC without a separate driver, but the workshop setup still needs testing with representative laptops, cables, and hubs. Keep BOOT and RESET accessible. [Espressif USB documentation](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/usb-otg-console.html)

The board has **4 MB flash and 2 MB PSRAM** and supports Arduino and CircuitPython. The teaching environment remains to be chosen. Flash is shared by firmware, partitions, and the logging filesystem; it is not all available for CSV files. Define the record format, sampling interval, and partition layout before estimating log duration. No SD card is planned.

The DS3231 keeps calendar time when the main battery is disconnected. Its separate **CR1220** is not included with the board and will be sourced locally. The firmware must provide initial clock setting, for example from the phone browser; the hotspot alone does not supply internet time. [RTC product](https://www.adafruit.com/product/5188)

## Solderless connections

```mermaid
flowchart LR
    F[ESP32-S3 Reverse TFT Feather] ---|QT 100 mm trial| R[DS3231 RTC]
    R ---|QT 50 mm trial| L[TSL2591 prototype]
    L ---|QT 100 mm trial| C[SCD30]
    F ---|Factory SPI connection| D[Built-in colour display]
    B[Local protected 18650 pack] ---|Prewired JST-PH| F
    U[Laptop] ---|Existing USB data cable| F
    K[Local CR1220] ---|Onboard holder| R
```

Three QT cables connect the three external modules. A hub is unnecessary. QT cables carry 3.3 V power, ground, SDA, and SCL. The main battery uses a separate **2-pin JST-PH** connector; the display is already connected on the Feather.

| Device | I²C address | Source |
| --- | --- | --- |
| SCD30 | `0x61` | [Sensirion interface specification](https://sensirion.com/media/documents/D7CEEF4A/6165372F/Sensirion_CO2_Sensors_SCD30_Interface_Description.pdf) |
| VEML7700 alternative | `0x10` | [Adafruit driver](https://github.com/adafruit/Adafruit_CircuitPython_VEML7700/blob/main/adafruit_veml7700.py) |
| TSL2591 prototype | `0x29` primary; also `0x28` | [TSL2591 datasheet, p13](https://cdn-learn.adafruit.com/assets/assets/000/078/658/original/TSL2591_DS000338_6-00.pdf) |
| Feather MAX17048 | `0x36` | [Reverse TFT Feather pinouts](https://learn.adafruit.com/esp32-s3-reverse-tft-feather/pinouts) |
| DS3231 | `0x68` | [RTC guide](https://learn.adafruit.com/adafruit-ds3231-precision-rtc-breakout?view=all) |

These addresses do not conflict. Purchase the assembled QT breakouts, including the current QT revision of whichever light sensor is selected. TSL2591 requires its own library and gain/integration settings; it is not a software drop-in replacement. The TFT uses SPI and has no I²C address.

**SCD30 integration:** Sensirion recommends I²C at 50 kHz or less and specifies clock stretching up to 150 ms. Validate the selected ESP32 core and sensor library with the entire chain. TFT updates do not use this bus. This is a documentation-based compatibility assessment, not a hardware test. [SCD30 specification](https://sensirion.com/media/documents/D7CEEF4A/6165372F/Sensirion_CO2_Sensors_SCD30_Interface_Description.pdf)

Use the **Adafruit Feather ESP32-S3 Reverse TFT** board definition. The shared display/QT power control, `TFT_I2C_POWER`, must be high before using the external modules or screen; supported board startup normally enables it. [Pinouts and power control](https://learn.adafruit.com/esp32-s3-reverse-tft-feather/pinouts)

## Local batteries and enclosure inputs

- Main pack: protected, prewired **1S 18650 Li-ion**, approximately **2,200 mAh**, **3.7 V nominal / 4.2 V full charge**, with a pre-attached **JST-PH 2-pin, 2.0 mm-pitch** plug matching the Feather's polarity. Connector shape alone does not establish polarity. The enclosure reserves **Ø20 × 72 mm** for the wrapped pack, based on the [Adafruit 1781 reference pack](https://www.adafruit.com/product/1781); the actual battery is purchased locally in Israel.
- Request pack capabilities of at least **1 A continuous discharge** and **500 mA charging** for margin. These are procurement requirements, not measured consumption or a claim about the Feather's charging current.
- RTC cell: one **CR1220, 3 V, non-rechargeable** per device, bought locally in Israel.
- Measure the chosen pack's dimensions, lead length, protection-board projection and connector orientation against the CAD envelope before the final print. Use an assembled pack rather than a bare cell needing soldered tabs or a student-wired holder.

The battery connects directly to the Feather, which supplies USB charging. There is no inline power switch. Firmware can provide a sleep control; full battery disconnection requires opening the carrier and unplugging the pack. Use a locally prewired pack with a suitable lead (target roughly 70–100 mm, to be checked on the pilot). [Power connections](https://learn.adafruit.com/esp32-s3-reverse-tft-feather/pinouts)

The [downloaded reference set](reference/README.md) includes the four exact PCB files, schematics, guides, sensor datasheets and available official STEP/STL models. The SCD30 PCB is **50.8 × 25.4 mm**; its official model extends from **2.934 mm below** the PCB bottom to **8.57 mm above**, about **11.50 mm overall**. The enclosure accounts for the underside pins; the older 8.8 mm product height alone is insufficient for clearance design.

The [v0.5 enclosure](../enclosure/README.md) uses **two case parts and a removable Feather mounting frame**, an integrated top light aperture, direct access to the PCB buttons, USB-C and RESET access, a battery retained by zip ties, and a downward-facing SCD30 under a simple open-bottom skirt. The [mechanical shopping list](../enclosure/MECHANICAL-BOM.md) ([CSV](../enclosure/hardware.csv)) specifies eight M2×5 pan-head board screws, two M3×8 pan-head closure screws, two thin RTC washers and two battery ties, plus optional external mounting supplies. No nuts, separate feet, button plungers or switch are used. These mechanical items remain separate from distributor imports. The Feather screws onto its frame outside the housing and slides in through the bottom. [Thermal screening](../enclosure/thermal/README.md) flags possible warming despite the slotted carrier; physical fit and temperature performance require a pilot build.

Before ordering for the class, assemble pilot hardware and check upload/recovery on macOS including Apple Silicon, Windows, and Linux; the complete sensor chain; hotspot operation while logging and downloading CSV; battery/USB transitions; charging and current draw; and enclosure fit. Runtime and laptop compatibility remain unmeasured. Pin the software versions that pass these checks.
