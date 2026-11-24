# Light sensor for the prototype

**Use the TSL2591 already supplied by Elad.** Erez confirmed that it is the **Adafruit STEMMA QT board, product 1980**, with two QT sockets and four mounting holes. Enclosure **v0.5** and the current production STLs are prepared for that board. The older header-only board and other manufacturers' layouts are not covered.

For the class, my recommendation is to keep using TSL2591 if the prototype behaves well in the intended lighting and enough identical boards are available. There is little reason to replace working stock for a basic workshop. If the priority becomes bright outdoor daylight measurement, compare it against VEML7700 before selecting the class hardware.

## Practical trade-offs

| Topic | TSL2591 — prototype | VEML7700 — original selection |
| --- | --- | --- |
| Light readings | Broadband and infrared channels; lux derived in software. Useful for demonstrating spectral differences. | Ambient-light and white channels; software converts readings to lux. |
| Range | Particularly sensitive in dim light; Adafruit advertises up to about **88,000 lux**. | Adafruit advertises up to about **120,000 lux**, with suitable settings/correction. More advertised headroom in bright light. |
| Software | Change to the TSL2591 library; configure gain/integration and handle saturation. | Also needs suitable gain/integration; high-light correction is relevant. |
| Wiring | Same three-lead QT chain; library uses **0x29** and the chip also responds at **0x28**. Neither conflicts with our other devices. | **0x10**; same QT cables. |
| Reference Adafruit price, checked 24 November 2026 | **$6.95**; supplied stock for this prototype | **$4.95** |

These ceilings describe the sensor's configurable range, not guaranteed accuracy in every light source or behind this enclosure. The wide TSL2591 dynamic range does not mean that one gain setting covers darkness through full sunlight. [Adafruit TSL2591 overview](https://learn.adafruit.com/adafruit-tsl2591), [TSL2591 product](https://www.adafruit.com/product/1980), [VEML7700 product](https://www.adafruit.com/product/4162), [VEML7700 gain and correction guidance](https://learn.adafruit.com/adafruit-veml7700?view=all#adjusting-for-different-light-levels).

For a greenhouse, both are useful for logging relative light changes and approximate illuminance. Neither is a calibrated PAR/PPFD instrument: lux follows human visual response, whereas a plant-light measurement counts photons over a specified band. Do not label lux or raw infrared counts as PPFD.

## Enclosure change

The pinned Adafruit PCB files give both QT boards a **25.4 × 17.78 mm** outline, the same four **Ø2.5 mm** holes on a **20.32 × 12.70 mm** pattern, and identical QT socket positions. The same two M2×5 screws, two locating pins, cables and board height are used.

The chip moves from PCB coordinates **(12.7, 13.716)** to **(12.7, 8.89) mm**. The TSL2591 photodiode array is slightly off-centre within its package; after the board's 180° chip rotation, its nominal optical centre is **(12.7, 9.26) mm**. The roof opening and well move **4.456 mm toward the front** to follow that centre. Package dimensions come from the TSL2591 datasheet's page 24 drawing: nominal **2.0 × 2.4 × 0.65 mm**. [Pinned PCB source](https://github.com/adafruit/Adafruit-TSL2591-Breakout-PCB/tree/22be4c7b8d53155dacedc18f3373ba8dbf95dc23), [manufacturer datasheet](https://cdn-learn.adafruit.com/assets/assets/000/078/658/original/TSL2591_DS000338_6-00.pdf).

The internal light well has lower-edge reliefs for nearby components, and the locating boss beside the power LED has a small edge relief. Hole centres and screw pilots stay unchanged. Their XY bounds come from the PCB pads/body outlines; their **2 mm height is a conservative modelling allowance**, with an extra **0.3 mm clearance** in the reliefs. These remain integral to the shell and are open-ended when printed roof-down. The roof opening retains its **12 × 6 mm throat / 17 × 16 mm outer flare**.

**Reprint only [01-shell.stl](../production-stls/01-shell.stl).** Reuse the carrier and Feather frame. The v0.4 opening is not over the TSL2591 array even though its screw holes fit. See the updated [interactive model](../enclosure/model.html) and [light-sensor fit drawing](../enclosure/light-sensor-fit.pdf).

The OpenSCAD source retains both choices through `light_sensor` in [parameters.scad](../enclosure/parameters.scad). Set it to `"veml7700"` and run the [full rebuild](../enclosure/README.md#rebuild) before exporting that alternative. The three-file production folder always contains the currently selected variant; do not mix shells between sensors.

## Prototype checks

1. Before closing the case, run Adafruit's [TSL2591 example](https://learn.adafruit.com/adafruit-tsl2591/wiring-and-test). Use its library, not VEML7700 code. Keep the complete I²C chain at the SCD30-compatible rate of **50 kHz or less**.
2. Start bright-light testing with **low gain and 100 ms integration**. Check raw channel counts/overflow and reduce sensitivity before treating a clipped reading as valid. Record an over-range flag rather than a false lux value; increase sensitivity for dim conditions.
3. Verify that the board seats freely, its components clear the notched well and both QT plugs fit. Tighten the existing screws gently.
4. Compare readings with the shell fitted/removed and with the display on/off, in darkness, room light, shade and the greenhouse's brightest expected light. Check for contamination from board LEDs and angular shading from the opening. The shorter TSL2591 package sits deeper below the roof than VEML7700, so matching mounting holes does not imply matching optical response.

The source dimensions and nominal collision checks support a fit trial. Physical fit, light response and firmware operation have not yet been tested on the supplied hardware.
