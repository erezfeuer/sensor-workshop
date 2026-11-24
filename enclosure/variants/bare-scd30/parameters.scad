// Personal prototype only. Dimensions in mm; standard workshop CAD is unchanged.
variant_version = "0.6-personal-scd30-2";
bare_origin = [29,42,17]; // PCB back plane; optical chamber faces down.
bare_size = [35,23];
bare_pcb_thickness = 1.6;
snap_width = 3.4;
snap_wall = 1.1;
snap_side_gap = 0.25;
snap_face_gap = 0.2;
snap_overlap = 0.4;
snap_tip_z = 2.9;
// Local PCB coordinates: Z=0 back, +Z optical side. Rotation points clips outwards.
snap_locations = [[33.6,0,180],[0,21,90],[20,23,0]];
guide_y = 18.5;
