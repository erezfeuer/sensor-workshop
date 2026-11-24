# Feather mount — reinforced v0.6

**Reprint only [03-feather-frame.stl](../production-stls/03-feather-frame.stl) when upgrading from v0.5.** The shell and sensor carrier are unchanged. The frame still slides into the existing rails and uses two screws plus two locating pins. [Mounting drawing and true CAD section](feather-mounting.pdf) · [Interactive model](model.html)

## What changed after the assembly trial

On 24 November 2026, Erez reported that the Feather screws fitted, but a printed post broke while unscrewing a board mounted the wrong way round. The previous antenna-end posts were only **3.2 mm across around a 1.8 mm pilot**: a nominal radial wall of **0.7 mm**. They also projected 5.4 mm ahead of the supporting upright. This was a weak geometry for repeated handling; the exact fracture location and removal torque were not measured.

The four posts now taper into **6.4 mm nominal roots**, joined to a **9 mm-tall region of each upright**. The contact faces are 5.2 mm across at the USB end and 4.4 mm at the antenna end before trimming. The original rail/stop envelope clips the roots, and local relief keeps plastic clear of the radio package and antenna face. The small contact lip beside the antenna remains locally thin; the reinforcement adds material behind it and around the threaded section. These reliefs are mechanical clearances, not a verified RF keep-out.

The screw pilots remain **Ø1.8 mm**, preserving the fit Erez tried. Their blind depth increases from **4.3 to 6 mm**, leaving **4.6 mm of solid material behind the hole**. A nominal M2×5 screw through the 1.6 mm PCB still has **3.4 mm engagement**. Extra hole depth reduces the chance of bottoming out; it is not a reason to force a longer screw into any of the other mounts.

At a section 2 mm behind the PCB, CAD measures about **25.4 mm²** of plastic around the USB-end screw and **24.0 mm²** around the antenna-end screw, versus approximately 12.0 and 5.5 mm² in the old straight posts. Those are geometry comparisons, **not measured strength multipliers**. The frame also has an engraved UP arrow, away from the screw roots.

![Reinforced frame with mounting faces visible](renders/feather-frame.png)

## Correct orientation before tightening

1. Work with the frame **outside the shell**. Hold its mounting faces toward you, with the engraved **UP arrow pointing up**. The connecting crossbar is at the bottom.
2. Hold the Feather with **USB on the left, screen and three buttons facing you**. The components and connectors on the back face the frame.
3. Lower it onto both locating pins without force. Confirm that all four mounting pads contact the PCB and that the board clears the frame. Do not use screws to pull a misaligned board onto its pins.
4. Fit the two screws from the display face using a straight precision screwdriver. Support the nearby upright and tighten gently until the PCB is seated. Avoid loading the glass.
5. Slide the complete frame up through the open bottom of the shell. The carrier retains it. For removal, unplug the battery and Feather lead, withdraw the complete frame, then remove the screws on the table while supporting the upright.

## What the measured screw tells us

The reported measurements are **approximately 1.8 mm over the thread and 5.5 mm of threaded portion**. That alone does not establish a standard size: metric size also requires pitch, and threaded length may differ from the length measured under the head. M2 has a nominal 2 mm diameter and 0.4 mm coarse pitch; M1.8 also exists, with 0.35 mm coarse pitch. [Bossard metric-thread table](https://media.bossard.com/global-en/-/media/bossard-group/website/documents/technical-resources/en/f-079-en.pdf)

Record the successful pilot fit without labelling these particular screws M2. The [mechanical BOM](MECHANICAL-BOM.md) retains **M2×5 pan-head screws** as the proposed purchase specification, pending a trial with identified screws. If a screw is actually 5.5 mm under the head, the 6 mm blind pilot would leave **2.1 mm nominal tip clearance** through this PCB; that is a conditional calculation, not confirmation of the user's screw length.

## Other screw mounts reviewed

| Mount | Boss / pilot diameter | Nominal radial wall | Support |
| --- | --- | --- | --- |
| TSL2591 / VEML7700 | 4.8 / 1.8 mm | 1.5 mm | 3.5 mm-tall boss directly rooted in the roof |
| DS3231 RTC | 5.2 / 1.8 mm | 1.7 mm | 4.8 mm-tall boss directly rooted in the roof |
| SCD30 | 4.8 / 1.8 mm | 1.5 mm | 4 mm-tall boss directly rooted in the carrier |
| Case closure | 7.6 / 2.6 mm | 2.5 mm | Integrated shell-corner support |

These mounts already have thicker walls and more direct support than the old Feather projections, so they are unchanged in this revision. The TSL2591 component relief affects a locating-pin boss rather than its screw bosses. Each mount still needs a real fastener trial; this audit is not a torque rating.

## Print and repeat the removal trial

Keep the STL's **flat rear face on the bed**. Start with a 0.4 mm nozzle, 0.2 mm layers, **five perimeters** and five top/bottom layers. The broad roots print first and narrow toward the PCB; the orientation mark and component reliefs open upward. No new support is intended, and no slicing has been performed here. PLA remains suitable for the indoor fit trial.

After cooling, fit the board correctly, snug the screws by hand, then gently remove and refit them a few times while supporting the frame near each screw. Inspect for cracks, whitening, loose threads or separation between layers, and confirm that the frame still slides freely. Stop if a screw bottoms out before the board seats. Keep the two remaining locating pins intact.

The CAD checks cover watertight solids, deeper blind bores, increased material in the threaded section, clearances and the full frame insertion path. **Repeated-removal durability remains untested until this print trial.**
