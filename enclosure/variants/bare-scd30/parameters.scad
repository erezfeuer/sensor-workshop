// Personal prototype only. Dimensions in mm; standard workshop CAD is unchanged.
variant_version = "0.8.1-personal-scd30-3";
bare_origin = [29,42,17]; // PCB back plane; optical chamber faces down.
bare_size = [35,23];
bare_pcb_thickness = 1.6;
snap_widths = [3.4,4.2,6.0]; // Corner is space-limited; widen the two clear edge latches.
snap_wall = 1.6;
snap_root_extra = 0.5;
snap_side_gap = 0.12;
snap_face_gap = 0.1;
snap_overlap = 0.65;
snap_tip_z = 3.2;
snap_nose_thickness = 0.5;
snap_opening = 0.85;
// Local PCB coordinates: Z=0 back, +Z optical side. Rotation points clips outwards.
snap_locations = [[33.6,0,180],[0,21,90],[20,23,0]];
guide_y = 18.5;
