# Enclosure v0.7.1 — mounting-hole audit / TSL2591 QT prototype

**v0.7.1 update:** the [full mounting-hole audit](generated/mounting-hole-checks.json) verifies all mounting centres, pilot depths, locating pins, closure passages and screw approaches. It also found a small RTC LED/post overlap. A local notch now clears that LED without moving the hole. **Use the updated `01-shell.stl`**, including in the personal print folder; the Feather frame also restores its complete working v0.5 front interface, with reinforcement behind it. Both carriers are retained. [Measured screw-depth table](MECHANICAL-BOM.md#mounting-hole-audit--25-november-2026).

The Feather frame keeps the old hole/pin centres and restores the original contact diameters, with clearance around both USB-end LED packages. These LEDs overlapped the enlarged v0.6 posts and were missing from the simplified model. Reinforced roots and Ø1.8 × 6 mm blind pilots remain. **USB ←** and **SCREEN SIDE** replace the UP mark. v0.7.1 restores the complete first 2 mm of the working v0.5 frame and its original locating pins; it also updates the shell as noted above. The personal bare-SCD30 variant also has a strengthened snap carrier. [Fit correction and orientation](FEATHER-MOUNT.md) · [Mounting drawing](feather-mounting.pdf).

The shell retains the **Adafruit TSL2591 STEMMA QT** fit introduced in v0.5: the roof opening and notched light well align with its optical centre. An older VEML7700 shell still needs replacing when changing to TSL2591. [Sensor comparison and prototype checks](../hardware/LIGHT-SENSOR.md) · [Light-sensor fit drawing](light-sensor-fit.pdf).

The four corner mounting grooves and curved battery-tie returns from v0.4 are retained.

The sensor carrier remains a single part, with perimeter slots and four bridges around its central mounting region. A [thermal screening model](thermal/README.md) finds that heat below the enclosure remains a risk: the nominal 0.8 W shaded example gives about **1.9°C additional module warming**, with uncertain assumptions. This is not temperature validation; a measurement procedure is included.

The main body remains **92 × 66 × 60.8 mm**; the corner shoulders extend the overall envelope to **95.2 × 69.2 × 60.8 mm**. Its body footprint remains **35.5% smaller** than v0.1. Erez reports that the previous shell printed well in PLA on an X1 Carbon. His unidentified screws fitted the Feather pilots, but a post broke during removal; the reinforced frame needs a repeat assembly/removal trial. The specified BOM screws, revised tie guides and TSL2591 optical response also need physical checks.

## Open and compare

- **[Bare SCD30 personal variant](variants/bare-scd30/README.md)** — Erez's soldered prototype only; includes a separate full print folder, snap-in carrier, assembly guide and interactive model.

- **[Interactive HTML model](model.html)** — one offline file with 30 component checkboxes (including three optional mounting-example items), an explosion slider, movable cutaways, an **Underside** camera, a **Remove / install Feather** movement mode, a **Tie access** view of the empty shell, a **Tie section** through the two-guide route, and a **Pole mount** example. “Look inside” hides the shell. Download the file and open it in a browser; GitHub's file page displays source.
- [Nine-page design review](design-review.pdf), [measured cross-sections](sections.pdf), [mounting drawings](mounting-drawings.pdf), and [battery-tie access sections](battery-tie-access.pdf), and [corner-guide details](mounting-guide-details.pdf).
- [TSL2591 board fit and roof cross-section](light-sensor-fit.pdf).
- [Reinforced Feather mount and orientation](FEATHER-MOUNT.md), with [CAD section and assembly drawing](feather-mounting.pdf).
- **[Mechanical shopping list — screw sizes, washers, zip ties and quantities](MECHANICAL-BOM.md)** ([CSV](hardware.csv)).
- [Three STL files to print](../production-stls/), [OpenSCAD source](sensor-workshop.scad), [editable dimensions](parameters.scad).
- [Previous v0.2 viewer](archive/v0.2/model.html), [v0.2 archive](archive/v0.2/README.md), and [thermal review PDF](thermal/thermal-review.pdf).
- [Previous v0.1 viewer](archive/v0.1/model.html) and [archived design](archive/v0.1/README.md) for comparison.
- [Pole/rail mounting option and tradeoffs](MOUNTING.md).
- [Manufacturer references](../hardware/reference/README.md) and [hole-coordinate CSV](generated/mounting-holes.csv).

![Accessible enclosure assembly](renders/assembled.png)

| Per device | v0.2 | v0.7.1 |
| --- | ---: | ---: |
| Printed pieces | 2 | **3: shell, carrier, Feather frame** |
| Screws | 10 | **10** |
| Nuts | 0 | **0** |
| Body footprint | 92 × 66 mm | **92 × 66 mm** |
| Printed height | 60.8 mm | **60.8 mm** |
| Feather screw access | Inside box, sideways | **Outside box, on the table** |
| Feet / button plungers / sensor box | Integral / none / none | **Same** |

## Construction and sensor placement

The main shell prints **roof down**. This avoids suspending a large floor over the feet. All four feet and the skirt grow from the side walls in the same print. The carrier prints **flat upper face down**, with its SCD30 bosses pointing upward on the build plate. It fits through the open skirt, seats against an internal shoulder, and is secured with two M3×8 screws from underneath.

The light board and RTC attach to the roof, with screwdriver access straight through the open bottom. The Feather attaches to its removable frame using two M2×5 screws from the display face; two rear locating pins support the other corners. **No Feather screw is installed inside the shell.** The frame's side tongues slide in two guides, and its rear uprights clear the USB socket and antenna envelope. A continuous internal front recess clears the screen, buttons and screw heads throughout insertion. The frame has 0.3 mm nominal tongue clearance and 0.2 mm nominal clearance at each end between its stops and the carrier; check sliding fit on the pilot.

All **eight board screws are M2×5**. The RTC also uses two thin washers. The Feather screws engage approximately 3.4 mm into the printed frame; pilot bores stop before its back face. All four-hole boards retain two screws and two locating pins. The two M3×8 carrier screws close the case and retain the Feather frame without additional locks or clips.

The TSL2591 remains upward-facing behind a flared roof opening and opaque light well. Its board has the same mounting and QT connector positions as the original VEML7700. The optical centre moves 4.456 mm toward the front. Clearance notches in the well allow 0.3 mm around conservative 2 mm-high ancillary-component envelopes extracted from the PCB layout. The SCD30 mounts upside down below the carrier with **1.065 mm clearance** above its underside pins. Its sensing body is **11.43 mm above the table**, and the surrounding skirt ends at **8 mm above the table**. Air reaches it through the open bottom; there is no lower tray floor, separate roof, or double-wall vent cage.

The central carrier region shades the sensor from above, and the perimeter skirt reduces direct light from the sides. This is a simple shade, not a validated outdoor radiation shield. Low-angle/reflected sunlight, table heating and heat conducted from the electronics still need measurement. The 2 mm slots reduce the local plastic conduction path, while air/radiation and screw/wire coupling remain. See the [thermal assumptions, results and pilot procedure](thermal/README.md). Sensirion's guidance supports keeping the sensor below and away from heat sources and avoiding direct sunlight. [SCD30 design-in guide](https://sensirion.com/media/documents/84D49268/616536CB/Sensirion_CO2_Sensors_SCD30_Design-In_Guidelines_D1.pdf)

The three real Feather buttons are behind one **7 × 22 mm slot**, about **2.4 mm recessed**. No little printed buttons are required. Finger/nail access and BOOT/RESET recovery must be checked on the pilot. The separate reset hole accepts a small blunt tool. A recessed internal pocket clears the display glass and reset switch body.

## Optional pole or rail mounting

A single external tie wraps around the whole body and its support. Four identical corner grooves position the 4.8 mm band below the controls. Their paired shoulders stand 1.6 mm proud of the original surface, follow each complete corner arc, and return 2.5 mm onto both adjoining faces. The band bears on the rounded corners; the 2.4 mm wall remains intact. The straight feet and three-piece print count stay the same. See the [mounting guide](MOUNTING.md) for the rear-anchor comparison, tie length, grip pad and wall-anchor limitations. The HTML **Pole mount** view shows a Ø32 mm example pole; the three example items are hidden by default.

## Battery and cables

Buy the protected, prewired **1S 18650 pack locally in Israel**, around 2,200 mAh, within the **Ø20 × 72 mm** design envelope. Its JST-PH polarity must match the Feather. The small printed end stops have been removed. A centred 72 mm pack has 7.6 mm nominal clearance to each side wall; the cradle ties provide retention. It is based on the [Adafruit reference pack](https://www.adafruit.com/product/1781); the wrapped local pack, protection board and lead exit still need measuring.

Two **2.5 mm nylon zip ties**, approximately 150 mm long, pass through **5 mm front eyelets**, then along an accessible middle channel into a **4 mm-radius curved return**. Each return turns the tail 90° toward the open underside and through a **second eyelet**. Both eyelets connect to the roof through the cradle. Tightening the loop presses the pack into its cradle—downward when the shell is held roof-down for assembly. The nominal passage is **3.6 × 2.4 mm**, with flared entry/exit mouths; the 8 mm cradle leaves 2.2 mm cheeks beside the passage.

Thread both ties in the empty shell before fitting boards or battery. Keep enough length at both ends to place the pack between them, then close each tie with its head below the pack. Tighten only enough to retain the pack; thin soft padding may improve grip. The physical trial showed that the previous open channel let the tail run into the roof/rear corner despite nominal clearance. The new return is intended to redirect it; actual tip feeding, friction and clamping still need a print trial. Check axial sliding and lead pull. Battery replacement requires cutting the ties.

There is **no inline switch or extension**. The battery lead goes directly to the Feather, removing the previous 508 mm coil. Target roughly 70–100 mm of prewired battery lead and check it in the pilot. Full power disconnection requires unplugging the battery through the opened carrier; software sleep remains a firmware option.

The RTC is rotated 90° so its QT sockets face front/rear, improving plug clearance and routing. The tentative chain remains:

**Feather — 100 mm — RTC — 50 mm — TSL2591 — 100 mm — SCD30**

Use the assortment for the pilot, then freeze bulk lengths after checking real plug bodies and a service loop for lowering the carrier. The three smooth cable illustrations have approximately **95, 35 and 56 mm** centreline paths; the extra purchased length/slack is not all drawn. The Feather–RTC route now passes behind the right slide guide; its 100 mm trial lead is close to the illustrated path length, so also try 150 mm from the assortment if the real lead lacks relaxed slack. The lead to the SCD30 passes through a **7.5 × 9 mm** rounded carrier opening.

The HTML and OpenSCAD show four individually coloured conductors and nominal white plug bodies, with curved routes. They are placement illustrations, not a pinout or guarantee of supplier bend radius. Each cable can be hidden independently. Cables disappear during explosion because a fixed routing model cannot stretch with displaced boards.

## Print set and assembly

Use **[production-stls/](../production-stls/)** for the three separate per-device files. Their print orientations are already set; import at **100% scale in millimetres**. The full CAD export refreshes this folder automatically.

| File | Quantity | Print orientation |
| --- | ---: | --- |
| [01-shell.stl](../production-stls/01-shell.stl) | **1** | Roof exterior flat on the bed; feet finish at the top of the print. |
| [02-sensor-carrier.stl](../production-stls/02-sensor-carrier.stl) | **1** | Upper face on the bed; SCD30 bosses and locating pins point up. |
| [03-feather-frame.stl](../production-stls/03-feather-frame.stl) | **1** | Flat rear face down; pads and locating pins grow upward. |
| [coupon.stl](stl/coupon.stl) | One shared setup print | Eight small gauges; kept outside the production folder. |

The [printability review](PRINTING.md) identifies the remaining bridge spans and support-removal access. The carrier ledge now has a 45° backing ramp, and the top light opening now widens from 12 × 6 mm inside to **17 × 16 mm outside** for a wider view of incoming light. Local support at this steeper flare is acceptable. The carrier and Feather frame print from flat faces; their crossbars/thermal bridges are supported by the bed. Use small local supports at the shell openings if the pilot needs them.

The STL orientations are already set. Use light-coloured opaque PETG for the working prototype, or PLA for indoor fit trials. Start with a 0.4 mm nozzle, 0.2 mm layers, four perimeters (**five for the reinforced Feather frame**), five top/bottom layers and 15–20% infill, then inspect the slicer. The shell has a **27 mm display-window bridge**, a 7 mm button-slot bridge, smaller vent/USB bridges and a flared optical aperture. Test bridging on the coupon; add local supports if the printer/material requires them. No large floor bridge is needed. [Prusa PETG](https://help.prusa3d.com/article/petg_2059), [PLA](https://help.prusa3d.com/article/pla_2062)

The coupon checks all four received board patterns (TSL2591 and VEML7700 QT share a mounting pattern), the locating pins, M2 pilot diameters 1.6–1.9 mm, M3 pilots 2.4–2.7 mm, the 27 mm bridge, and the battery diameter. The current pilots are 1.8 and 2.6 mm; pre-thread them with gentle hand torque before class. The locating pins are 1.9 mm diameter and 1.2 mm tall. No heat-set inserts are used.

1. Print/check the coupon and measure the local pack. Inspect all three parts in the slicer. Clean the slide rails, thermal slots, cable passage, tie eyelets and bridge edges. With the empty shell roof down, feed each tie tail through its front eyelet toward the rear. The curved return should turn the tip upward through the second eyelet. Leave enough length at both ends to reach around the battery, and move the ends aside while fitting the boards. Check that the carrier's four thermal bridges are sound; it is still one part, not a breakaway support.
2. **On the table**, hold the frame with its engraved crossbar at the bottom and **SCREEN SIDE facing you**. Point the USB socket along the **USB arrow**, with **screen/buttons facing you**; the components face the frame. Seat it flat on both original locating pins without force before fitting the two M2×5 screws from the display face. Keep the driver off the glass, support the frame near the screw and tighten only until seated. [Orientation drawing and removal trial](FEATHER-MOUNT.md).
3. With the shell roof down and bottom open, insert the CR1220 into the RTC. Install the RTC with two M2×5 screws and washers, then the light board with two M2×5 screws. Approach these four screws straight through the bottom. Fit the RTC–light lead.
4. Slide the complete Feather/frame into its guides from the open bottom until it reaches the upper stops. The button and display faces point toward the front openings. Check the buttons, RESET and USB opening. Connect the Feather–RTC lead with the bottom still open. The frame remains loose in its guides until the carrier is fitted; keep it seated while handling the open device.
5. With the ties already threaded, insert the battery from below with its lead toward the left. Bring the ends around the pack, close each tie with its head below the battery, secure gently, and route its lead to the Feather's downward-facing socket. Keep the lead above the small bottom frame crossbar and away from the closing edge. Confirm polarity before connecting.
6. **Outside the housing**, screw the SCD30 onto the carrier with its body away from the plate, using two M2×5 screws and the two locating pins. Plug in its QT lead and feed it through the carrier opening to the light board. Leave a service loop so the carrier can be lowered.
7. Move loose wires and tie heads clear of the rails and closing rim. Raise the carrier straight through the open skirt onto its shoulder and fit the two M3×8 screws from below. This captures the Feather frame. Check sensing, programming/recovery, charging and the hotspot.

To remove the Feather, lower the carrier with its SCD30, unplug the battery and Feather QT lead, then slide the board/frame straight down. Its two mounting screws are removed only after it is outside the housing. The HTML movement mode hides the carrier/SCD30 and unplugged leads, and moves the Feather, frame and two screws as one unit. The general exploded view is an inspection illustration rather than an assembly sequence.

## Pilot checks and validation

Check physical finger and screwdriver access, real connector envelopes, received board revisions, tie routing, lead slack, pilot engagement and local pack fit. Verify that the carrier can be lowered for service and that all four feet sit steadily. The light opening is uncovered and the skirt is open: this is not a rainproof housing.

Compare CO₂ response and temperature/RH with the housing fitted/removed, under Wi-Fi activity, charging and display on/off. Then compare controlled sunlight/shade transitions against a shaded reference thermometer. Check light readings with the shell fitted/removed and with display/LEDs on/off; the optical well changes angular response. Adjust the mechanical layout based on measurements rather than assuming the skirt eliminates thermal bias.

[Validation results](generated/validation.json) check all three print solids and the shared coupon, source hashes, nominal gaps, screw engagement and Boolean intersections of the simplified mechanical/electronic/plug/cable envelopes and optional mounting route. [Browser checks](generated/viewer-checks.json) exercise all 30 visibility controls, explosion, Feather withdrawal, the empty-shell tie-access, battery-tie section and pole-mount views, cutaways, views and mobile layout offline. [Assembly checks](generated/assembly-checks.json) sample the Feather/frame/screws at 161 poses along an 80 mm vertical path, the carrier and battery at 81 poses each, eight straight screwdriver shafts, and nominal curved feed paths and tail-access envelopes for both battery ties. These nominal-envelope checks do not establish manufacturing tolerances, physical fit or sensor accuracy. The [detailed Feather fit check](generated/feather-fit-checks.json) additionally tests 186 closed meshes generated from the official STEP, compares hole/pin centres against the old fitted STL, and verifies removal of the v0.6 LED interference. The original vendor STLs have open surfaces and are not used as collision solids.

## Rebuild

Use OpenSCAD 2021.01 or later and Python 3.12. The detailed Feather fit check also needs FreeCAD Python; set `FREECAD_PYTHON` if it is not installed at the default macOS path. The tracked `light_sensor = "tsl2591"` setting selects the current prototype. To regenerate the original light-sensor layout, change it to `"veml7700"` in `parameters.scad` and run the full sequence; this replaces the production shell and viewer with that variant. From the repository root:

```sh
python3 -m venv .venv-cad
.venv-cad/bin/pip install -r enclosure/requirements-cad.txt
.venv-cad/bin/python enclosure/scripts/fetch_sources.py
.venv-cad/bin/python enclosure/scripts/extract_boards.py
.venv-cad/bin/python enclosure/scripts/cable_routes.py
.venv-cad/bin/python enclosure/scripts/export_parts.py
.venv-cad/bin/python enclosure/scripts/render_review.py
.venv-cad/bin/python enclosure/scripts/build_viewer.py
.venv-cad/bin/python enclosure/scripts/validate.py
.venv-cad/bin/python enclosure/scripts/check_feather_fit.py
.venv-cad/bin/python enclosure/scripts/check_mounting_holes.py
.venv-cad/bin/python enclosure/scripts/check_assembly.py
.venv-cad/bin/python enclosure/thermal/model.py
.venv-cad/bin/pip install -r enclosure/requirements-viewer-check.txt
.venv-cad/bin/python enclosure/scripts/check_viewer.py
```

Open `sensor-workshop.scad` for interactive CAD views. `part="shell"`, `part="carrier"` and `part="feather_frame"` select the three print pieces; `view="underside"` exposes the downward-facing sensor. `parameters.scad` contains the core dimensions. Optional vendor models need the reference cache, but the default simplified model does not. Some cable and mount placements are layout-specific: after changing dimensions, update routing and run the clearance checks rather than assuming every parameter change is automatic.

The HTML needs no web server, external JavaScript library or internet connection. Rebuild it from the scene meshes using [build_viewer.py](scripts/build_viewer.py); its editable files remain in [viewer/](viewer/). Renders use software rasterization, so OpenSCAD's OpenGL preview is not required.
