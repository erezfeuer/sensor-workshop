// Sensor Workshop enclosure v0.1 — millimetres. Edit here, then rerender.
// Board XY coordinates come from generated/boards.scad, not these parameters.
case_width = 112;
case_depth = 84;
base_z = 34;
case_top = 76;
wall = 2.4;
floor_thickness = 2.4;
lid_thickness = 2.4;
corner_radius = 6;
fit_clearance = 0.3;
m2_pilot = 1.8;
m3_clearance = 3.4;
m3_nut_af = 5.7;
pcb_thickness = 1.6;

// Each origin is the Eagle XY origin on the PCB's bottom plane.
feather_origin = [8, 7, 70]; // rotated -90 degrees about X; display faces front
rtc_origin = [76, 30, 44];
light_origin = [73, 44, 70.9]; // top of PCB = 72.5; 3.5 mm below lid
scd30_origin = [35, 28.4, 16.4];

// Protected 18650 pack envelope, NOT a bare-cell holder.
// Reference Adafruit 1781 pack = 18 dia x 69 long; allow local pack variation.
battery_diameter = 20;
battery_length = 72;
battery_center = [56, 66, 50];
strap_width = 8;

pod_origin = [17, 18, 10];
pod_size = [78, 48];
pod_floor = 2.4;
pod_roof_z = 28;
pod_roof_thickness = 2.4;
pod_wall = 2;
pod_baffle_inset = 4;
pod_mounts = [[22,23], [90,23], [22,61], [90,61]];
leg_mounts = [[8,22], [104,22], [8,68], [104,68]];
foot_splay = 12;

// Pigtail switch body has no manufacturer mechanical drawing. Adjustable bay.
switch_envelope = [12, 30, 16];
switch_origin = [3.8, 27, 45];

// Cap dimensions include 0.2 mm nominal free gap to official model actuator.
button_hole = 4.8;
button_neck = 4.3;
button_flange = 5.8;
button_stem_end = 4.9;
button_protrusion = 0.6;
