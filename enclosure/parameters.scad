// Sensor Workshop v0.8.1 — millimetres. Two case parts + one Feather frame.
enclosure_version = "0.8.1";
light_sensor = "tsl2591"; // Adafruit QT only: "tsl2591" or "veml7700"; rebuild all outputs after changing.
case_width = 92;
case_depth = 66;
case_top = 58.4;
roof_thickness = 2.4;
optic_flare = [2.5,5]; // Per side in X/Y; wider light acceptance, local supports allowed.
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

// Optional mounting: a single external tie wraps the case and its support.
mount_band_z = 31;
mount_band_width = 4.8;
mount_groove_width = 6;
mount_groove_depth = 1.6; // Raised corner shoulders; no wall material removed.
mount_groove_bevel = 1.6;
mount_guide_land = 0.6;
mount_corner_run = 2.5;
mount_example_pole_diameter = 32;
mount_example_pad_thickness = 2;

// Eagle PCB bottom-plane origins. Rotations are defined in board_transform().
feather_origin = [6,4.3,57];
light_origin = [30,17,53.3];
rtc_origin = [79,10.5,52]; // +90 degrees around Z, QT faces front/rear
scd30_origin = [21,43,20]; // 180 degrees around X, sensor faces down

battery_diameter = 20;
battery_length = 72;
battery_center = [46,50,41];
battery_saddles = [23,79];
battery_saddle_width = 8;
tie_width = 2.5;
tie_slot_width = 3.6;
tie_tunnel_z = 54.2;
tie_slot_height = 2.4;
tie_eyelet_length = 5;
tie_turn_radius = 4;
tie_turn_start_y = 57;
tie_exit_z = 48.5;
tie_rear_outer_y = 64.2;

// Select two diagonal screws; the other two holes use printed locating pins.
board_screw_indices = [0,3];
board_pin_indices = [1,2];
board_screw_length = 5;
// Preserve the fitted pins/seat plane; broaden screw collars separately below.
feather_contact_diameters = [4.3,3.2]; // Original cores remain inside the new collars.
feather_contact_length = 2.0;
feather_screw_collar_diameter = 5.2;
feather_component_clearance = 0.2;
feather_root_diameter = 6.4;
feather_root_y = 8.7;
feather_root_span = 9;
feather_pilot_depth = 6;

// Open-bottom battery-lead notch. The plugged-in lead lifts out freely.
feather_cable_notch_x = [11,24];
feather_cable_notch_top = 30.5;
feather_cable_notch_radius = 1;
feather_cable_bridge_height = 3;
feather_cable_bridge_y = [12.5,16.5];

// Central carrier region stays attached by four broad, short printed bridges.
// Thermal model reads the same dimensions; no separate sensor-box parts.
thermal_island = [20.5,16.5,73,44.5];
thermal_slot_width = 2;
thermal_bridge_count = 4;
thermal_bridge_width = 3;
thermal_bridge_x = [30,63];
