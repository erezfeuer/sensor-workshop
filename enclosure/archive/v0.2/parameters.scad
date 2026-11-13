// Sensor Workshop v0.2 — millimetres. Two printed parts per device.
case_width = 92;
case_depth = 66;
case_top = 58.4;
roof_thickness = 2.4;
wall = 2.4;
corner_radius = 6;
carrier_z = 24;
carrier_thickness = 2.4;
fit_clearance = 0.3;
skirt_bottom = 8;
foot_span = 14;
pcb_thickness = 1.6;
m2_pilot = 1.8;
m3_pilot = 2.6;
locating_pin = 1.9;
locating_height = 1.2;
case_mounts = [[86,6],[6,60]];

// Eagle PCB bottom-plane origins. Rotations are defined in board_transform().
feather_origin = [6,4.3,57];
light_origin = [30,17,53.3];
rtc_origin = [79,10.5,52]; // +90 degrees around Z, QT faces front/rear
scd30_origin = [21,43,20]; // 180 degrees around X, sensor faces down

battery_diameter = 20;
battery_length = 72;
battery_center = [46,50,41];
battery_saddles = [23,79];
tie_width = 2.5;
tie_slot_width = 3.2;
tie_tunnel_z = 54.2;

// Select two diagonal screws; the other two holes use printed locating pins.
board_screw_indices = [0,3];
board_pin_indices = [1,2];
board_screw_length = 5;
