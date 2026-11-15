# Printability review — v0.4

The design keeps **three printed pieces** and uses their assembly layout to give each a flat printing face. The previous shell printed well in Erez’s PLA/X1 Carbon trial. The revised tie guides have been reviewed geometrically but have not yet been printed or sliced here. The **[production-stls/](../production-stls/)** folder contains exactly the three separate files to print, one of each per device. Import at **100% scale in millimetres** and keep the supplied orientations.

For the first test, **print the shell separately**, then print the **carrier and Feather frame together**. The shell has the openings and flare that may need support tuning; the smaller parts have straightforward flat printing faces. After the fit and settings are confirmed, all three can share a plate using normal layer-by-layer printing, with local support settings applied to the shell as needed.

| Part | Face on the bed | Overhang/support assessment |
| --- | --- | --- |
| Shell | Exterior roof | Feet, slide guides, board bosses, light well and battery cradles grow from the roof/walls. The display window and wider light flare are local-support candidates. |
| Carrier | Flat upper face | Plate, central sensor region and all four thermal bridges start on the bed. Bosses and pins grow vertically; no deliberate support is needed for this orientation. |
| Feather frame | Flat rear face | Uprights, crossbar and tongues start on the bed. Mounting pads and locating pins grow vertically; the crossbar is not an elevated bridge. |

## Geometry refinements

- **Carrier seating ledge:** a 1.4 mm rise/run ramp backs the ledge. With the shell roof down, the ramp grows from the wall before reaching the seating ledge, replacing a sudden unsupported projection. The flat carrier contact face and insertion clearance remain unchanged.
- **Light opening:** the inner opening remains **12 × 6 mm**; the outer mouth is now **17 × 16 mm** through the 2.4 mm roof. The nominal flare faces are about **46° / 64° from vertical**. This deliberately opens the view beyond the earlier 45° flare; small removable supports are acceptable here. Actual sensor angular response still needs a pilot comparison.
- **Battery ties:** each 8 mm cradle has a **5 mm front eyelet**, a **14.5 mm accessible middle channel**, and a **4 mm-radius return into a second eyelet**. The turn redirects the tail toward the open underside. The nominal passage remains 3.6 × 2.4 mm, with flared mouths and 2.2 mm side cheeks. Small roofs across this passage bridge 3.6 mm; inspect for droop or roughness that could catch the tip.
- **Mounting guides:** paired shoulders wrap all four corner arcs and short tangent returns. They form **1.6 mm-deep grooves without thinning the 2.4 mm wall**. Both flanks have 1.6 mm rise/run chamfers, so the lower shoulder grows gradually in roof-down printing. There are no separate ears or extra printed pieces.
- **Battery end stops:** the two thin end flaps have been removed; the existing cradles and ties retain the pack.

The carrier ledge retains its 45° slope; the light flare prioritizes a wider opening. Neither geometry is a print-quality guarantee for every printer or filament. Orientation, cooling, layer height and extrusion width affect the result. Chamfers are preferable to rounding an underside into a steep overhang; supported surfaces can also need cleanup. [Prusa's design guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)

## Where to allow local supports

| Shell feature | Approximate span in print orientation | Treatment |
| --- | ---: | --- |
| Display window | 27 mm | Test the existing bridge coupon. If it sags, add a removable local support under the bridge. Keep the rectangular opening so no active display area is obscured. |
| USB opening | 10.8 mm | Inspect the first bridge in the pilot; local support is acceptable if needed. |
| Three-button slot | 7 mm | Short bridge; inspect for droop that could restrict button access. |
| Rear vents | 4 mm | Short bridges; keep the slots clear. |
| Battery-tie guides | 3.6 mm across X; 4.8 mm at the mouths | Inspect the front eyelet, curved return and rear exit. Clear roughness from the accessible middle/ends, then feed a real tie before fitting boards. |
| Light flare | 17 × 16 mm outer mouth, 12 × 6 mm throat | Allow local support under the steeper flare faces; remove it through the roof opening before fitting the light board. |
| RESET hole | 2 mm | Small horizontal hole; check that the blunt reset tool can pass after printing. |

For the roof-down shell, the display bridge is the **lower edge of the window when the device is standing upright**, at assembly Z = 37.7 mm. This becomes print Z = 23.1 mm. Support there must generally start on the earlier printed front wall inside the window: **build-plate-only supports may not reach it through the intervening wall**. Use local paint/enforcers that permit support on the model, inspect their removal path, and remove them through the window before assembly. A small central support can shorten the free bridge span without filling the whole opening. [Prusa support controls](https://help.prusa3d.com/article/support-material_1698)

Keep supports off the Feather's sliding faces, small locating pins, screw pilots and carrier mating edge wherever possible. Do not fill the case with broad automatic supports. If a small opening really requires support, choose a placement that can be reached with a tool afterward.

The rounded battery cradle is not an unsupported arch in this orientation: its solid back prints first, then the open saddle forms as the print grows away from the roof. The thermal carrier's four connecting strips are also **in the bed plane**, not unsupported extrusion bridges.

## First-print feedback — 15 November 2026

The user reports that the previous shell printed well in PLA on a Bambu Lab X1 Carbon. The observed problems were tie retention on the flat exterior faces and battery-tie tails running into the rear/roof corner. v0.4 addresses those two points. **Reprint only `01-shell.stl`**; the carrier and Feather frame STLs are byte-for-byte unchanged. M2 pilots remain **1.8 mm** and M3 pilots **2.6 mm**, pending the user’s screw-fit test.

For the revised shell, test the two curved feeds while empty, then the battery clamping action and the external tie’s seating at the corners. The existing geometric checks cannot prove how a real nylon tip bends or slides.

## Before printing many units

Use the existing starting profile in [the assembly guide](README.md#print-set-and-assembly), then print the shared coupon and one pilot. Check the display/USB bridges, sliding fit, small pins, intact thermal bridges and clean cable/tie passages. Allow enough cooling time for the small pads and pins using the material's profile. Remove first-layer spread or use the printer's established compensation if it obstructs the sliding fit; do not compensate by forcing the board/frame into the case.

Future revisions should keep these priorities: flat printing faces, gradual growth under ledges, short accessible bridges, removable local supports, and no added assembly pieces solely to avoid a small support.
