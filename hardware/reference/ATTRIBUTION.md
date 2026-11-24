# Source attribution

The board coordinates and simplified board geometry in this project derive from Adafruit's open hardware designs. The selected source commits and individual hashes are recorded in [manifest.json](manifest.json). Changes here comprise extraction of PCB extents, mounting-hole centres, selected component locations, simplified mechanical envelopes and their placement in the workshop enclosure. These are not unmodified Adafruit enclosure designs, and Adafruit has not endorsed this project.

The board-derived material retains the upstream **Creative Commons Attribution-ShareAlike 3.0 Unported** terms. Full upstream README text and license notices are preserved below, with line endings and trailing whitespace normalized. The notices apply to their respective upstream materials and derivatives; this file does not assign a blanket license to unrelated workshop code or documents.

| Board | Design attribution | Upstream | Preserved notices |
| --- | --- | --- | --- |
| ESP32-S3 Reverse TFT Feather, 5691 | Limor Fried / Ladyada for Adafruit Industries | [PCB repository](https://github.com/adafruit/Adafruit-ESP32-S3-Reverse-TFT-Feather-PCB) | [README](notices/feather-README.txt), [license](notices/feather-license.txt) |
| SCD30, 4867 | Limor Fried / Ladyada for Adafruit Industries | [PCB repository](https://github.com/adafruit/Adafruit-SCD-30-PCB) | [README](notices/scd30-README.txt), [license](notices/scd30-license.txt) |
| VEML7700, flat STEMMA QT 4162 | Kattni Rembor for Adafruit Industries | [PCB repository](https://github.com/adafruit/Adafruit-VEML7700-PCB) | [README](notices/veml7700-README.txt), [license](notices/veml7700-license.txt) |
| TSL2591 STEMMA QT, 1980 | Limor Fried / Ladyada for Adafruit Industries | [PCB repository](https://github.com/adafruit/Adafruit-TSL2591-Breakout-PCB) | [README](notices/tsl2591-README.txt), [license](notices/tsl2591-license.txt) |
| DS3231 STEMMA QT, 5188 | Limor Fried / Ladyada for Adafruit Industries | [PCB repository](https://github.com/adafruit/Adafruit-DS3231-Precision-RTC-Breakout-PCB) | [README](notices/rtc-README.txt), [license](notices/rtc-license.txt) |

Official component STEP/STL files were obtained from [Adafruit CAD Parts](https://github.com/adafruit/Adafruit_CAD_Parts) and are cached as reference material, not redistributed in the tracked enclosure assets. Manufacturer datasheets and guides remain the works of their respective publishers: Adafruit, Sensirion, Vishay, ams, Espressif and Analog Devices/Maxim. They are downloaded to a local, Git-ignored reference cache; original download links are in the [reference index](README.md).

The personal bare-SCD30 viewer and drawings use tessellated geometry from **Sensirion AG's [official SCD30 STEP model](https://sensirion.com/media/documents/E9438033/61653143/Sensirion_CO2_Sensors_SCD30_POD_STEP_File.zip)**. The model was rotated, translated, coloured and tessellated for assembly visualization and clearance checks. The original STEP is cached locally; its source and hash are recorded in the [personal variant references](../../enclosure/variants/bare-scd30/references.json). This manufacturer reference geometry is separate from the Adafruit-derived material described above.

Support the original open hardware designers by purchasing their products. Preserve these notices with redistributed board-derived files.
