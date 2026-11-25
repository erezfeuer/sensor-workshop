# Personal prototype print sets

These are separate from the standard workshop [production-stls](../production-stls/).

**[bare-scd30/](bare-scd30/)** is Erez's personal set for the **bare Sensirion SCD30** and Adafruit **TSL2591 QT** light board. Print **one of each of its three separate STLs**, at 100% scale in millimetres, keeping their supplied orientations. The shell and reinforced Feather frame match workshop v0.7; the sensor carrier is different.

[Assembly and hardware](../enclosure/variants/bare-scd30/README.md) · [Personal interactive model](../enclosure/variants/bare-scd30/model.html) · [Mounting sections](../enclosure/variants/bare-scd30/mounting.pdf)

The carrier has **three strengthened integral latches that snap over clear edges of the bare PCB**. No separate sensor clips, header clamp, screws or washers are required. The detailed manufacturer model includes components on both PCB sides. You will still solder and insulate your QT lead; its routing is not prescribed by this holder. PETG is preferred for the flexible latches; physical fit remains to be tested.

**25 November update:** reprint `02-sensor-carrier-bare-scd30.stl` and `03-feather-frame.stl`. The shell is unchanged. The frame now has USB/SCREEN SIDE marks and clears both USB-end LEDs; the carrier clips are thicker, wider where space permits, and hold the PCB with less play.
