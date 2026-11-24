// Personal prototype only. Dimensions in mm; standard workshop CAD is unchanged.
variant_version = "0.6-personal-scd30-1";
bare_origin = [29,38,18]; // PCB back plane; cavity faces down, contacts toward rear.
bare_size = [35,23];
bare_pcb_thickness = 1.6;
bare_back_envelope = 1.55;
bare_front_envelope = 6.15; // Includes PCB; total conservative envelope = 7.7 mm.
header_first = [30.4,36.6]; // VDD; then GND, SCL, SDA, RDY, PWM, SEL along +X.
header_pitch = 2.54;
header_body = [17.78,2.54,2.54];
header_clearance = 0.2;
header_seat_z = 24.1; // Header ends sit in a 0.1 mm recess in the carrier underside.
header_long_leg = 6;
header_short_leg = 3;
header_pin_width = 0.64;
header_wall = 2.4;
retainer_z = 21.2; // Washer upper face; 0.36 mm below nominal header body.
retainer_centers = [[33,41.3],[43,41.3]]; // Washers overlap plastic only, clear all seven pins.
retainer_boss_d = 6.4;
retainer_pilot_depth = 4.8;
retainer_washer = [2.2,8,0.5]; // ID, OD, thickness; small RTC washers will not reach.
wire_window = [16.64,4.4]; // End seats retain header; clear pins throughout pocket side play.
wire_window_top = [19.2,5.2]; // Taper gives the insulated solder joints extra room above.
strain_slots = [[23.5,28],[23.5,34]];
