# Enclosure v0.1

The first prototype is a small desktop instrument with an upward-facing light sensor, a front display and three buttons, a protected cylindrical battery at the rear, and a separate shaded CO₂ sensing tray underneath. Four splayed feet raise the tray above the table. The body is **112 × 84 mm**; the printed assembly is **78.4 mm high** (approximately 81 mm including screw heads). The feet extend the total depth to 88 mm.

**This is a source-based CAD prototype. No physical fit, printing, electrical or thermal tests have been performed.** Print the coupon and assemble one pilot before making a classroom batch.

## Review the design

- **[Interactive 3D model](model.html)** — download/open in a browser. One self-contained HTML file, usable offline, with 53 component checkboxes, continuous explosion, orbit/pan/zoom, camera presets and movable cutaways. Expand “Fasteners” for individual screws and nuts. GitHub's file page displays HTML source; download the file to use it.
- [Seven-page design review](design-review.pdf): assembly, inside, exploded view, cutaways, measured sections and mounting drawings.
- [True cross-sections](sections.pdf) and [board mounting drawings](mounting-drawings.pdf).
- [OpenSCAD source](sensor-workshop.scad), [dimensions and fit parameters](parameters.scad), [printable STL files](stl/), [mechanical BOM](hardware.csv).
- [Downloaded references and source manifest](../hardware/reference/README.md).

![Enclosure prototype](renders/assembled.png)

The HTML uses the same exported OpenSCAD solids as the printable design. Electronics are simplified envelopes based on the PCB files, datasheets and vendor models. Fasteners, straps and cable paths are assembly illustrations, not manufacturing drawings. Cable guides disappear during explosion because the fixed routing illustration cannot stretch with the parts. Interactive cutaways are uncapped; the PDF includes filled, measured cross-sections.

## Placement and clearances

The top lid has a flared, uncovered opening above the VEML7700 and an internal opaque light well. The recess protects the PCB and reduces stray light from the display/LEDs, but also limits grazing-angle light. Check readings against the uncovered sensor; do not assume an unchanged angular response or absolute lux accuracy.

The SCD30 is below the electronics in a removable tray. Outer vents are low and inner vents are high, giving light an indirect path into the bay. A roof shades the sensor and is separated from the upper housing by a **3.6 mm air gap**. The cable openings in the two floors are offset. This arrangement follows Sensirion's guidance to separate the sensor from heat sources and direct sun; it is not a validated radiation shield. It needs diffusion/response and temperature-bias testing. [Sensirion design-in guide](https://sensirion.com/media/documents/84D49268/616536CB/Sensirion_CO2_Sensors_SCD30_Design-In_Guidelines_D1.pdf)

The Feather sits vertically behind the front wall. Its TFT, three user buttons, USB-C and recessed reset are accessible. The printed plungers have a nominal **0.2 mm free gap** to the switch actuators. Confirm they release completely, including the BOOT button, and that a tool can reach RESET. The PCB antenna faces the central empty region; route wires away from it and verify hotspot range in the completed enclosure.

| Interface | Nominal clearance |
| --- | ---: |
| SCD30 underside pins → tray floor | 1.065 mm |
| SCD30 top → shade roof | 3.03 mm |
| Shade roof → main floor | 3.6 mm |
| RTC holder → main floor | 4.4 mm |
| Light-board QT sockets → lid underside | 0.5 mm |
| Light sensor top → lid underside | 1.15 mm |
| Battery top → light PCB underside | 10.9 mm |

Coordinates use X left-to-right, Y front-to-rear and Z above the table. Board XY values are unmirrored Eagle top-view coordinates; the Feather is rotated −90° about X. See the [hole-coordinate CSV](generated/mounting-holes.csv). The Feather's two right-hand holes differ from a generic Feather template; the RTC has **two** mounting holes. Those details come directly from the selected PCB revisions.

## Battery and switch

Use a **protected, prewired 1S 18650 Li-ion pack**, approximately 2,200 mAh, with the correct-polarity JST-PH 2-pin plug. Purchase locally in Israel. The reference is [Adafruit 1781](https://www.adafruit.com/product/1781), whose product page lists Ø18 × 69 mm. Its linked cell-pack drawing and product dimensions differ, so this design reserves **Ø20 × 72 mm** and 4 mm total axial space between the end stops. This is an envelope, not a guarantee that every protected 18650 fits. Measure the actual wrapped pack, protection board and lead exit.

Two soft 8 mm straps retain the assembled pack in curved saddles. A smaller pack may need thin removable padding. No student soldering, bare-cell holder or hard pressure fit is required. The plug must match the Feather's polarity, not just its connector shape. Electrical procurement requirements remain in the [BOM](../hardware/BOM.md).

The [Adafruit 3064 switch cable](https://www.adafruit.com/product/3064) is about 508 mm long. Its body dimensions are not published. The CAD therefore uses an **unverified 12 × 30 × 16 mm envelope**, an adjustable tie mount and a generous side opening. Check the actual body, actuator travel, plug accessibility and coiled slack. Adjust `switch_envelope`, the plate and opening together if required. The long lead must be coiled gently in the front-centre bay and tied away from the antenna, battery straps and sensor vents. The HTML cable geometry is illustrative and does not model all 508 mm of slack.

## Print and hardware

Use light-coloured, opaque **PETG for the working prototype**. PLA is suitable for an indoor fit prototype. PETG offers better heat resistance than PLA, but neither material makes this open, ventilated enclosure weatherproof. The uncovered light aperture and vents exclude rain exposure. [Prusa PETG guide](https://help.prusa3d.com/article/petg_2059), [PLA guide](https://help.prusa3d.com/article/pla_2062)

Suggested starting profile: 0.4 mm nozzle, 0.2 mm layers, four perimeters, five top/bottom layers, 15–20% infill, using the filament manufacturer's temperature profile. Inspect the slicer's bridges, thin walls, screw bosses and nut pockets before printing. Exported STLs are already oriented for printing and use millimetres.

| File | Print count | Orientation / attention |
| --- | ---: | --- |
| `base.stl` | 1 | Floor down. The 30 mm display opening is a bridge; test it on the coupon. Use local build-plate supports there if needed. |
| `lid.stl` | 1 | Exterior face down; light-board bosses and well point up. |
| `pod.stl` | 1 | Floor down; inspect 10 mm ventilation-slot bridges. |
| `shade.stl` | 1 | Flat roof down; spacers point up. |
| `foot_front.stl` | 2 | Foot pad down; nut pocket up. |
| `foot_rear.stl` | 2 | Foot pad down; nut pocket up. |
| `button.stl` | 3 | Button face down; stem up. |
| `coupon.stl` | 1 shared | Eight separate pieces: four board templates, pilot gauge, nut gauge, bridge and battery diameter gauge. |

The [mechanical BOM](hardware.csv) calls for **14 M2×6 screws, two M2 washers, four M3×50 screws, four M3×25 screws and eight M3 nuts**, plus two battery straps and four small cable ties. These are proposed quantities for local procurement, not additions to the existing distributor cart imports. Screw lengths exclude heads. No heat-set inserts are used.

M2 screws engage printed pilots, nominally 1.8 mm. The coupon offers 1.6/1.7/1.8/1.9 mm pilots and 5.5/5.6/5.7/5.8 mm nut pockets. Select the fit on the actual printer and material; pre-thread the chosen pilots before the workshop. Use gentle hand torque. Repeated service may justify revising the design for inserts later.

## Assembly sequence

1. Print the coupon. Check all four real board patterns, the protected battery diameter, screw engagement, nut fit and bridge quality. Caliper-check the switch body and pack length. Update dimensions before the full print if needed.
2. Print and clean the parts. Pre-thread pilots; clear cable slots and vents. Put a CR1220 in the RTC holder before fastening the board. Prepare four nuts in the feet and four in the underside of the sensor tray.
3. Fit the three plungers from inside the front housing. Place the Feather with display/buttons facing forward and USB-C left; retain with four M2×6 screws. Check all buttons and USB/recovery access immediately.
4. Mount the RTC with two M2×6 screws and two thin washers. Mount the SCD30 on its four corner bosses with four M2×6 screws. Do not press or clamp its sensor body.
5. Connect the SCD30's QT lead and feed the other end through the shade opening. Feed it across the air gap into the upper-floor opening. Fit the shade and tray using four M3×25 screws from the upper floor into the tray nuts. Keep the cable out of the joint.
6. Mount the light board under the lid using four M2×6 screws, with its sensing package facing the opening. Verify that the optical well clears all received-board components.
7. Fit the prewired switch with two ties and secure the battery with two straps. Route and restrain excess battery lead with the other ties. Keep access to the battery plug and leave strain relief. Connect power only after polarity is checked.
8. Wire the tentative chain **Feather → RTC → VEML7700 → SCD30**. Start with **100 mm + 100 mm + 200 mm** QT-to-QT leads from the assortment. The longer last lead permits lid removal and reaches the lower bay; confirm lengths and loop placement with real connectors before buying class quantities.
9. Bring the lid into place without pinching cables. Hold each foot/nut under its locating hole and fit the four M3×50 screws through the lid and housing into the foot nuts. Tighten evenly by hand. Verify every control, charging, hotspot, logging and all sensor readings.

The geometry reserves full nut engagement for both M3 screw lengths: M3×50 tips reach Z28.4 below foot nuts at Z31.4–33.8; M3×25 tips reach Z11.4 below tray nuts at Z12–14.4. Neither tip should protrude below its printed part. Verify actual screw and nut dimensions during the pilot build.

## Acceptance checks for the pilot

Record the actual pack and switch dimensions, the selected screw/nut coupon sizes, and the received board revisions. Confirm electrical connector insertion, wire bend/slack, full button release, reset access, lid removal and stable feet. Check that the pack cannot slide into a wire or board and that no retaining feature compresses it.

Compare SCD30 temperature/RH and CO₂ response with and without the enclosure, including Wi-Fi activity, display on/off and battery charging. Then test controlled sunlight/shade transitions against a reference thermometer in shade. Evaluate the light sensor with the lid fitted/removed and the display/LEDs on/off. Revise ventilation or separation based on measurements; do not apply an arbitrary temperature offset to hide a variable charging/solar bias.

## Rebuild

Open `sensor-workshop.scad` in OpenSCAD 2021.01 or later. Select `view` for assembled, exploded, open, sections or print layout; select `part` for a single printable item. `parameters.scad` contains fit settings. Generated PCB coordinates should be regenerated from their sources rather than edited manually. The printable model works without downloaded vendor models; `use_vendor_models=true` optionally previews the official Feather/SCD30/RTC STL files after fetching references.

From the repository root, with OpenSCAD on PATH and Python 3.12 (the version used for these outputs):

```sh
python3 -m venv .venv-cad
.venv-cad/bin/pip install -r enclosure/requirements-cad.txt
.venv-cad/bin/python enclosure/scripts/fetch_sources.py
.venv-cad/bin/python enclosure/scripts/extract_boards.py
.venv-cad/bin/python enclosure/scripts/export_parts.py
.venv-cad/bin/python enclosure/scripts/render_review.py
.venv-cad/bin/python enclosure/scripts/build_viewer.py
.venv-cad/bin/python enclosure/scripts/validate.py
```

For offline browser checks with a locally installed Chrome:

```sh
.venv-cad/bin/pip install -r enclosure/requirements-viewer-check.txt
.venv-cad/bin/python enclosure/scripts/check_viewer.py
```

The HTML viewer requires no libraries, CDN or web server. Python generates it from the scene meshes and the editable [viewer template](viewer/template.html) / [viewer code](viewer/viewer.js). PDF/PNG generation uses software rendering, so it does not require OpenSCAD's OpenGL preview.

Validation records are in [validation.json](generated/validation.json) and [viewer-checks.json](generated/viewer-checks.json). All eight printable STL files are checked for watertightness, winding and expected separate-body count. Reference hashes, nominal clearances and screw stacks are checked. These checks establish model consistency; they do not establish real-world fit. The vendor component STLs contain open surfaces, so their Boolean intersections cannot be used as a watertight collision proof.
