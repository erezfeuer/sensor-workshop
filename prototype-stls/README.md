# Personal prototype print sets

These are separate from the standard workshop [production-stls](../production-stls/).

**[bare-scd30/](bare-scd30/)** is Erez's personal set for the **bare Sensirion SCD30** and Adafruit **TSL2591 QT** light board. Print **one of each of its three separate STLs**, at 100% scale in millimetres, keeping their supplied orientations. The shell and reinforced Feather frame match workshop v0.8.1; the sensor carrier is different.

[Assembly and hardware](../enclosure/variants/bare-scd30/README.md) · [Personal interactive model](../enclosure/variants/bare-scd30/model.html) · [Mounting sections](../enclosure/variants/bare-scd30/mounting.pdf)

The carrier has **three strengthened integral latches that snap over clear edges of the bare PCB**. No separate sensor clips, header clamp, screws or washers are required. The detailed manufacturer model includes components on both PCB sides. You will still solder and insulate your QT lead; its routing is not prescribed by this holder. PETG is preferred for the flexible latches; physical fit remains to be tested.

**Current revision, v0.8.1:** if you printed v0.8 or v0.7.1, **reprint only `03-feather-frame.stl`**. Both screw collars are widened up to the PCB, with local component reliefs and unchanged fitted hole centres, pins and seat plane. The raised brace retains its wide open battery-lead notch above the closing carrier. [Collar sections](../enclosure/feather-collars.pdf). The shell and strengthened bare-SCD30 carrier are byte-for-byte unchanged. [Lay the connected lead in the notch](../enclosure/BATTERY-LEAD.md); choose **Battery cable** in the HTML for a close-up. All three files remain available here for a complete new set.