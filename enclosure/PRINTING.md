# Printability review — v0.3

The design keeps **three printed pieces** and uses their assembly layout to give each a flat printing face. This is a geometry review; no slicing or physical printing has been performed. Use the orientations already exported in [stl/](stl/).

| Part | Face on the bed | Overhang/support assessment |
| --- | --- | --- |
| Shell | Exterior roof | Feet, slide guides, board bosses, light well and battery cradles grow from the roof/walls. The display window is the main local-support candidate. |
| Carrier | Flat upper face | Plate, central sensor region and all four thermal bridges start on the bed. Bosses and pins grow vertically; no deliberate support is needed for this orientation. |
| Feather frame | Flat rear face | Uprights, crossbar and tongues start on the bed. Mounting pads and locating pins grow vertically; the crossbar is not an elevated bridge. |

## Geometry refinements

- **Carrier seating ledge:** a 1.4 mm rise/run ramp backs the ledge. With the shell roof down, the ramp grows from the wall before reaching the seating ledge, replacing a sudden unsupported projection. The flat carrier contact face and insertion clearance remain unchanged.
- **Light opening:** the inner opening remains **12 × 6 mm**, with a nominal **45° flare** through the 2.4 mm roof to an outer opening of **16.8 × 10.8 mm**. Previously the 17 × 12 mm mouth made the steeper pair of faces about 51° from vertical in print orientation. `optic_flare` is limited to `roof_thickness` in the CAD.

The 45° slopes are a design target, not a promise for every printer or filament. Orientation, cooling, layer height and extrusion width affect the result. Chamfers are preferable to rounding an underside into a steep overhang; supported surfaces can also need cleanup. [Prusa's design guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)

## Where to allow local supports

| Shell feature | Approximate span in print orientation | Treatment |
| --- | ---: | --- |
| Display window | 27 mm | Test the existing bridge coupon. If it sags, add a removable local support under the bridge. Keep the rectangular opening so no active display area is obscured. |
| USB opening | 10.8 mm | Inspect the first bridge in the pilot; local support is acceptable if needed. |
| Three-button slot | 7 mm | Short bridge; inspect for droop that could restrict button access. |
| Rear vents | 4 mm | Short bridges; keep the slots clear. |
| Battery-tie tunnels | 3.2 mm across X | Short bridges in the roof-mounted saddles. Avoid filling the tunnels with support that is difficult to remove. |
| RESET hole | 2 mm | Small horizontal hole; check that the blunt reset tool can pass after printing. |

For the roof-down shell, the display bridge is the **lower edge of the window when the device is standing upright**, at assembly Z = 37.7 mm. This becomes print Z = 23.1 mm. Support there must generally start on the earlier printed front wall inside the window: **build-plate-only supports may not reach it through the intervening wall**. Use local paint/enforcers that permit support on the model, inspect their removal path, and remove them through the window before assembly. A small central support can shorten the free bridge span without filling the whole opening. [Prusa support controls](https://help.prusa3d.com/article/support-material_1698)

Keep supports off the Feather's sliding faces, small locating pins, screw pilots and carrier mating edge wherever possible. Do not fill the case with broad automatic supports. If a small opening really requires support, choose a placement that can be reached with a tool afterward.

The rounded battery cradle is not an unsupported arch in this orientation: its solid back prints first, then the open saddle forms as the print grows away from the roof. The thermal carrier's four connecting strips are also **in the bed plane**, not unsupported extrusion bridges.

## Before printing many units

Use the existing starting profile in [the assembly guide](README.md#print-set-and-assembly), then print the shared coupon and one pilot. Check the display/USB bridges, sliding fit, small pins, intact thermal bridges and clean cable/tie passages. Allow enough cooling time for the small pads and pins using the material's profile. Remove first-layer spread or use the printer's established compensation if it obstructs the sliding fit; do not compensate by forcing the board/frame into the case.

Future revisions should keep these priorities: flat printing faces, gradual growth under ledges, short accessible bridges, removable local supports, and no added assembly pieces solely to avoid a small support.
