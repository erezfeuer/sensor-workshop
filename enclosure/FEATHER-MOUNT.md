# Feather mount — reinforced screw collars v0.8.1

**Reprint only [03-feather-frame.stl](../production-stls/03-feather-frame.stl) from v0.8.** Both screw collars are reinforced at the PCB-facing end. The raised left brace leaves a wide, open notch above the closing cover. The connected battery lead lifts out without unplugging its PH connector. [Assembly and sections](BATTERY-LEAD.md). The shell and both carriers are unchanged; the personal set has the same updated frame in its [print folder](../prototype-stls/bare-scd30/). [Mounting drawing](feather-mounting.pdf) · [Interactive model](model.html).

## What was wrong, and what changed

Restoring the old board fit in v0.7.1 also restored its entire first 2 mm of plastic behind the PCB. That left the radio-end screw on a **Ø3.2 mm neck around a Ø1.8 mm pilot: just 0.7 mm nominal radial wall**. The wider root behind it did not fix that neck. The old validation checked reinforcement 3.5 mm behind the PCB and froze the complete front interface, so it missed this weakness. The v0.8 battery notch did not remove post material.

**v0.8.1 adds nominal Ø5.2 mm collars at both screw mouths**, tapering into the existing Ø6.4 mm roots. Local shallow reliefs clear the USB-end LED and radio-module PCB; the end header positions also retain room for future pins. The radio-side relief still needs a thin local edge at the board face, but the remaining collar is broad rather than a long, thin circular stem. The change adds about 43.89 mm³ and removes none of the v0.8 frame's material.

The fitted **hole centres, locating pins, PCB seat plane, Ø1.8 mm pilots and 6 mm blind depth are unchanged**. The new collars clear all **186 manufacturer solids**, and their added material clears conservative component bounding boxes by at least 0.15 mm. Checks at 19 depths between 0.1 and 1.9 mm behind each screw mouth now require a minimum plastic section; the old frame fails this regression check.

| Screw collar | Previous minimum section | New minimum section |
| --- | ---: | ---: |
| USB end | 11.94 mm² | 18.20 mm² |
| Radio end | 5.48 mm² | 15.64 mm² |

Sections are measured inside a 2.6 mm radius of each screw axis. These are geometric areas, **not a measured strength or torque rating**. [Before/after cross-sections](feather-collars.pdf).

The lower crossbar carries a **USB arrow** and **SCREEN SIDE**. Its clear right half provides space for the labels; the left half is raised above an open battery-lead notch. The original overall size and slide tongues are retained.

![Corrected frame and engraved orientation labels](renders/feather-frame.png)

## Correct orientation before tightening

1. Work with the frame **outside the shell**. Face the engraved crossbar towards you, with that crossbar at the bottom.
2. Point the Feather's **USB socket in the engraved arrow's direction**. The **screen and three buttons face you**, on the side marked SCREEN SIDE; the rear components face the mounting pads.
3. Seat both locating pins gently. Confirm that the PCB sits flat against the pads and both screw holes line up before inserting screws. Do not use the screws to pull the board into place.
4. Fit the two screws from the display face with a straight precision screwdriver. Support the nearby upright and tighten gently until seated, keeping the driver off the glass.
5. Slide the complete frame into the shell from its open bottom. For removal, lift the battery lead out of the open notch and disconnect the QT lead if needed. Support the connected battery while bringing the frame out for screw access; available lead slack limits movement. Unscrew on the table while supporting the posts.

The [detailed fit check](generated/feather-fit-checks.json) independently compares STL hole/pin centres to the fitted v0.5 frame and to the manufacturer's PCB holes. All **186 STEP solids** clear the corrected frame; the six component-solid overlaps belonging to the two LEDs in v0.6 are removed. The two LEDs are also included in the routine simplified model now. These are nominal geometric checks; the revised print still needs a seating and removal trial.

## What the measured screw tells us

The reported measurements are **approximately 1.8 mm over the thread and 5.5 mm of threaded portion**. That alone does not establish a standard size: metric size also requires pitch, and threaded length may differ from the length measured under the head. M2 has a nominal 2 mm diameter and 0.4 mm coarse pitch; M1.8 also exists, with 0.35 mm coarse pitch. [Bossard metric-thread table](https://media.bossard.com/global-en/-/media/bossard-group/website/documents/technical-resources/en/f-079-en.pdf)

Record the successful pilot fit without labelling these particular screws M2. The [mechanical BOM](MECHANICAL-BOM.md) retains **M2×5 pan-head screws** as the proposed purchase specification, pending a trial with identified screws. If a screw is actually 5.5 mm under the head, the 6 mm blind pilot would leave **2.1 mm nominal tip clearance** through this PCB; that is a conditional calculation, not confirmation of the user's screw length.

## Other screw mounts reviewed

| Mount | Boss / pilot diameter | Nominal radial wall | Support |
| --- | --- | --- | --- |
| TSL2591 / VEML7700 | 4.8 / 1.8 mm | 1.5 mm | 3.5 mm-tall boss directly rooted in the roof |
| DS3231 RTC | 5.2 / 1.8 mm | 1.7 mm nominal; ≥1.15 mm checked at LED relief | 4.8 mm-tall boss directly rooted in the roof |
| SCD30 | 4.8 / 1.8 mm | 1.5 mm | 4 mm-tall boss directly rooted in the carrier |
| Case closure | 7.6 / 2.6 mm | 2.5 mm | Integrated shell-corner support |

These mounts have more direct support than the old Feather projections. The RTC post now has a local LED relief, checked against the full manufacturer model; its hole centre and depth remain unchanged. The TSL2591 component relief affects a locating-pin boss rather than its screw bosses. Each mount still needs a real fastener trial; this audit is not a torque rating.

## Print and repeat the removal trial

Keep the STL's **flat rear face on the bed**. Start with a 0.4 mm nozzle, 0.2 mm layers, **five perimeters** and five top/bottom layers. The broad roots print first and narrow toward the PCB; USB/SCREEN SIDE lettering and component reliefs open upward. No new support is intended, and no slicing has been performed here. PLA remains suitable for the indoor fit trial.

After cooling, fit the board correctly, snug the screws by hand, then gently remove and refit them a few times while supporting the frame near each screw. Inspect for cracks, whitening, loose threads or separation between layers, and confirm that the frame still slides freely. Stop if a screw bottoms out before the board seats. Keep the two remaining locating pins intact.

The CAD checks cover watertight solids, blind bores, reinforced threaded sections, every detailed manufacturer component, old/new hole and pin centres, PCB seat plane, front-collar sections and the full frame insertion path. **Repeated-removal durability remains untested until this print trial.**
