# Personal prototype print sets

These are separate from the standard workshop [production-stls](../production-stls/).

**[bare-scd30/](bare-scd30/)** is Erez's personal set for the **bare Sensirion SCD30** and Adafruit **TSL2591 QT** light board. Print **one of each of its three separate STLs**, at 100% scale in millimetres, keeping their supplied orientations. The shell and reinforced Feather frame match workshop v0.7.1; the sensor carrier is different.

[Assembly and hardware](../enclosure/variants/bare-scd30/README.md) · [Personal interactive model](../enclosure/variants/bare-scd30/model.html) · [Mounting sections](../enclosure/variants/bare-scd30/mounting.pdf)

The carrier has **three strengthened integral latches that snap over clear edges of the bare PCB**. No separate sensor clips, header clamp, screws or washers are required. The detailed manufacturer model includes components on both PCB sides. You will still solder and insulate your QT lead; its routing is not prescribed by this holder. PETG is preferred for the flexible latches; physical fit remains to be tested.

**Current revision, v0.7.1:** use all three current files in this folder. The shell has a local RTC-post notch to clear its LED. The Feather frame exactly restores the working v0.5 board-facing interface, with reinforcement behind the first 2 mm. The strengthened, closer-fitting bare-SCD30 carrier from v0.7 is retained. [Hole and screw-depth checks](../enclosure/MECHANICAL-BOM.md#mounting-hole-audit--25-november-2026).
