// Personal bare-SCD30 carrier: three integral edge snaps, no separate hardware.
include <../../parameters.scad>
include <parameters.scad>
use <../../sensor-workshop.scad>
$fn=48; // Keep the workshop mating rim identical.
eps=0.02;
variant_part="carrier"; // carrier, sensor
assembly_coordinates=false;
root_z=bare_origin[2]-carrier_z;

module yz_prism(points,w) {
    // A polygon in the local Y/Z plane, extruded along X.
    multmatrix([[0,0,1,-w/2],[1,0,0,0],[0,1,0,0],[0,0,0,1]])
        linear_extrude(w) polygon(points);
}
module edge_snap(w) {
    g=snap_side_gap; t=snap_wall; o=snap_overlap;
    // Long spring leaf, with an outward root gusset and a sloped insertion nose.
    yz_prism([[g,root_z-eps],[g+t+snap_root_extra,root_z-eps],
        [g+t+snap_root_extra,root_z+.3],[g+t,root_z+1.3],
        [g+t,snap_tip_z],[g,snap_tip_z],[-o,bare_pcb_thickness+snap_face_gap+snap_nose_thickness],
        [-o,bare_pcb_thickness+snap_face_gap],[g,bare_pcb_thickness+snap_face_gap]],w);
    // Back stop: a short, gradually widening pad. The PCB sits loosely between
    // this stop and the nose, with 0.1 mm clearance at each face; no preload.
    yz_prism([[g,root_z-eps],[g+t,root_z-eps],[g+t,-snap_face_gap],
        [-.55,-snap_face_gap],[-.55,-.65],[g,-1.45]],w);
}
module sensor_frame() {
    translate(bare_origin) rotate([180,0,0]) children();
}
module snap_features() {
    sensor_frame() {
        for(i=[0:len(snap_locations)-1]) let(p=snap_locations[i])
            translate([p[0],p[1],0]) rotate([0,0,p[2]]) edge_snap(snap_widths[i]);
        // Fourth edge is only a lateral stop. It does not overlap either PCB face.
        translate([bare_size[0]+snap_side_gap,guide_y-1.5,root_z-eps])
            cube([2,3,bare_pcb_thickness+snap_face_gap-root_z+eps]);
    }
}
module personal_carrier() {
    difference() {
        union() {
            translate([wall+fit_clearance,wall+fit_clearance,carrier_z])
                rounded_box([case_width-2*(wall+fit_clearance),case_depth-2*(wall+fit_clearance),carrier_thickness],corner_radius-wall-fit_clearance);
            snap_features();
        }
        for(p=case_mounts) translate([p[0],p[1],carrier_z-eps]) cylinder(h=carrier_thickness+2*eps,d=3.4);
        translate([13.5,29,carrier_z-eps]) rounded_box([7.5,9,carrier_thickness+2*eps],1.2);
        thermal_slots();
        translate([49,54,carrier_z+.45]) rotate([180,0,0]) linear_extrude(.5)
            text("SNAP SCD30",size=3,font="Liberation Sans:style=Bold");
    }
}
module bare_sensor() {
    // Detailed manufacturer STEP, converted by prepare_sensor.py, not a box.
    sensor_frame() import("generated/scene/sensor-local.stl");
}
if(variant_part=="sensor") bare_sensor();
else if(assembly_coordinates) personal_carrier();
else translate([0,case_depth,carrier_z+carrier_thickness]) rotate([180,0,0]) personal_carrier();
