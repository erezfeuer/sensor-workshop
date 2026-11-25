# Mechanical bill of materials — one device

For enclosure **v0.7.1, reinforced Feather frame / Adafruit TSL2591 QT prototype**; fastener quantities also apply to the VEML7700 alternative. Buy these generic items locally or from a fastener supplier; they are separate from the Digi-Key/Mouser electronics orders. Quantities below are the installed quantities, before spares. [CSV shopping list](hardware.csv) · [Electronics and batteries](../hardware/BOM.md) · [Assembly instructions](README.md#print-set-and-assembly)

## Required purchased hardware

| Item | Quantity per device | Specification to buy | Where it goes |
| --- | ---: | --- | --- |
| Board mounting screws | **8** | **M2 × 5 mm metric machine screws, pan head**: 2 mm nominal thread diameter, 5 mm length under the head | Two each for the Feather, SCD30, TSL2591 (or VEML7700) and DS3231 RTC |
| RTC washers | **2** | **Flat M2 washers**, approximately **2.2 mm inside diameter × 5 mm outside diameter × 0.5 mm thick** | One under each RTC screw head, above the PCB; spans the board's 3 mm mounting hole |
| Case closure screws | **2** | **M3 × 8 mm metric machine screws, pan head**: 3 mm nominal thread diameter, 8 mm length under the head | Bottom carrier into the main shell |
| Battery zip ties | **2** | **2.5 mm wide × approximately 150 mm long**, flexible nylon, standard locking head | One through each battery cradle's front and rear guides |

**Per-device hardware bag: 10 screws, 2 washers and 2 battery ties.** No nuts, heat-set inserts, separate spacers or additional frame fasteners are needed. The other board screws and the M3 closure screws do not use washers in this design.

### Screw and washer selection

Use pan heads with a flat bearing surface. Phillips recesses are convenient for workshop precision screwdrivers; match the driver to the actual screws supplied. Countersunk heads are unsuitable for the flat seats. Taller socket-cap heads need a separate clearance check.

The stated screw lengths exclude the heads. Use ordinary metric machine threads; the screws engage the printed pilot bores directly. The current **1.8 mm M2 pilots and 2.6 mm M3 pilots are hole sizes in the plastic**, not the screw diameters to purchase. Pre-thread gently by hand before class.

The CAD uses **0.5 mm-thick RTC washers** when calculating screw engagement. Check washer dimensions rather than relying on an “M2 washer” label alone. Do not omit them or substitute longer screws without checking the available depth.

**Physical feedback, 24 November 2026:** Erez's unidentified screws, measured at approximately **1.8 mm across the thread and 5.5 mm of threaded length**, fitted the Feather pilots. A printed post broke when unscrewed. This does not identify the screws as M2 or qualify the specified BOM fasteners. Keep the nominal shopping specification above until the thread/pitch and under-head length are confirmed. v0.7 keeps the reinforced frame and **6 mm** blind holes, and corrects clearance around the USB-end LEDs; other mounts keep their original depths. Repeat assembly/removal on the new frame and trial the specified fasteners on the other mounts before a classroom order. [Details and orientation](FEATHER-MOUNT.md).

| Assembly | Screws | Washers |
| --- | --- | --- |
| Feather → removable frame, assembled outside the case | 2 × M2 × 5 mm | None |
| TSL2591 / VEML7700 → shell roof | 2 × M2 × 5 mm | None |
| DS3231 RTC → shell roof | 2 × M2 × 5 mm | 2 × thin M2 flat washers |
| SCD30 → bottom carrier, assembled outside the case | 2 × M2 × 5 mm | None |
| Bottom carrier → shell | 2 × M3 × 8 mm | None |

## Mounting-hole audit — 25 November 2026

The [STL audit](generated/mounting-hole-checks.json) ([measurement table](generated/mounting-hole-checks.csv)) checks the released print files against the pinned manufacturer PCB files. It covers all **14 board mounting centres, 10 screw pilots, 6 locating pins, and the two closure passages in each carrier variant**. These are model dimensions, not measurements of a printed part.

| Mount | Screw | Pilot diameter | Measured blind depth | Spare depth beyond screw tip |
| --- | --- | ---: | ---: | ---: |
| Feather | M2×5 | 1.8 mm | 6.00 mm | 2.60 mm |
| TSL2591 / VEML7700 pattern | M2×5 | 1.8 mm | 4.40 mm | 1.00 mm |
| RTC, with 0.5 mm washer | M2×5 | 1.8 mm | 5.70 mm | 2.80 mm |
| Standard Adafruit SCD30 | M2×5 | 1.8 mm | 4.78 mm | 1.38 mm |
| Case closure | M3×8 | 2.6 mm | 8.98 mm | 3.38 mm |

Both carriers have **Ø3.4 mm through-holes** aligned with the shell pilots. The **Ø1.9 × 1.2 mm locating pins** fit their specified PCB holes, including the Feather's smaller Ø2.2 mm holes. All ten standard screw-head and straight-driver approaches are checked at their assembly stages. The personal bare SCD30 has no sensor mounting screws; its eight remaining screws use the same checked interfaces.

The detailed board check found one more interference in v0.7: the RTC D1 LED touched one post edge. **v0.7.1 adds a local clearance notch to the shell**, leaving the hole centre and bore unchanged. The notch clears the manufacturer model and retains at least a 1.15 mm continuous wall around the pilot mouth in the checked section. The fuller root remains behind it. Use the updated `01-shell.stl` in either print folder. The Feather frame also restores its complete working v0.5 front interface, with reinforcement behind it. Both carriers retain their v0.7 geometry.

The detailed Feather, RTC and standard SCD30 models are checked for mounting interference. TSL2591 uses PCB-derived component envelopes with conservative heights. Printed bore size, actual screw/thread dimensions and tightening force still need a physical fit check.

## Optional supplies

| Item | Quantity per device | Specification / use |
| --- | --- | --- |
| External mounting zip tie | **1 only when mounting to a pole/rail** | **4.8 mm wide × 400–450 mm long** for the illustrated Ø32 mm pole. Wraps the entire case and support through the four corner grooves. Choose length for the actual support, leaving a usable threading tail. |
| Mounting grip pad | **1 small piece if needed** | Non-slip rubber; the model uses **18 × 16 × 2 mm**. Place behind the mounting band, below the rear vents. |
| Battery padding | **1 small piece if needed** | Thin, soft, nonconductive removable foam to take up clearance around the actual battery. Keep connectors and vents clear. |

See the [mounting guide](MOUNTING.md) for routing and grip checks. A bare wall needs a site-specific eye or bracket; wall anchors and their screws are not part of this per-device kit.

## Printed parts

Print **one of each** from [production-stls/](../production-stls/):

| Part | Quantity | Production file |
| --- | ---: | --- |
| Main shell, including feet, skirt, battery cradles and tie guides | 1 | [01-shell.stl](../production-stls/01-shell.stl) |
| Bottom sensor carrier | 1 | [02-sensor-carrier.stl](../production-stls/02-sensor-carrier.stl) |
| Removable Feather frame | 1 | [03-feather-frame.stl](../production-stls/03-feather-frame.stl) |

The optional [fit coupon](stl/coupon.stl) is a shared printer setup aid, not a fourth assembly part. See [printing guidance](PRINTING.md) for material and orientation.

For a class, multiply the installed quantities by the number of devices and allow roughly **10% spare screws, washers and ties**, rounded up. Battery replacement consumes two new ties. Shared assembly tools are matching precision screwdrivers and small flush cutters for the ties.
