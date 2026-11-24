// One-off carrier for a bare Sensirion SCD30, supported ONLY by its contact pins.
// The header plastic is captured by two wide washers; no screw touches the sensor.
include <../../parameters.scad>
include <parameters.scad>
use <../../sensor-workshop.scad>
$fn=48; // Match the existing carrier rim exactly.
eps=0.02;
variant_part="carrier"; // carrier, sensor, header
assembly_coordinates=false;
header_center=[header_first[0]+3*header_pitch,header_first[1]];
pocket=[header_body[0]+2*header_clearance,header_body[1]+2*header_clearance];

module personal_carrier() {
    difference() {
        union() {
            // Same mating rim, plate thickness and thermal bridges as workshop v0.6.
            translate([wall+fit_clearance,wall+fit_clearance,carrier_z])
                rounded_box([case_width-2*(wall+fit_clearance),case_depth-2*(wall+fit_clearance),carrier_thickness],corner_radius-wall-fit_clearance);
            translate([header_center[0]-pocket[0]/2-header_wall,header_center[1]-pocket[1]/2-header_wall,retainer_z])
                cube([pocket[0]+2*header_wall,pocket[1]+2*header_wall,carrier_z-retainer_z+eps]);
            for(p=retainer_centers) translate([p[0],p[1],retainer_z])
                cylinder(h=carrier_z-retainer_z+eps,d=retainer_boss_d);
        }
        for(p=case_mounts) translate([p[0],p[1],carrier_z-eps]) cylinder(h=carrier_thickness+2*eps,d=3.4);
        translate([13.5,29,carrier_z-eps]) rounded_box([7.5,9,carrier_thickness+2*eps],1.2);
        thermal_slots();
        // Loose pocket. Metal washers close its underside without squeezing the body.
        translate([header_center[0]-pocket[0]/2,header_center[1]-pocket[1]/2,retainer_z-eps])
            cube([pocket[0],pocket[1],header_seat_z-retainer_z+eps]);
        hull() {
            translate([header_center[0]-wire_window[0]/2,header_center[1]-wire_window[1]/2,header_seat_z-eps])
                cube([wire_window[0],wire_window[1],eps]);
            translate([header_center[0]-wire_window_top[0]/2,header_center[1]-wire_window_top[1]/2,carrier_z+carrier_thickness])
                cube([wire_window_top[0],wire_window_top[1],eps]);
        }
        for(p=retainer_centers) translate([p[0],p[1],retainer_z-eps]) cylinder(h=retainer_pilot_depth+eps,d=m2_pilot);
        for(p=strain_slots) translate([p[0]-1.7,p[1]-.8,carrier_z-eps]) cube([3.4,1.6,carrier_thickness+2*eps]);
        translate([50,54,carrier_z+.45]) rotate([180,0,0]) linear_extrude(.5)
            text("BARE SCD30",size=3,font="Liberation Sans:style=Bold");
    }
}
module bare_sensor() {
    // Conservative mechanical envelope, NOT a vendor manufacturing model.
    // Leave the whole backside clear, including the RH/T device and its opening.
    difference() {
        translate([bare_origin[0],bare_origin[1]-bare_size[1],bare_origin[2]-bare_front_envelope])
            cube([bare_size[0],bare_size[1],bare_front_envelope+bare_back_envelope]);
        for(i=[0:6]) translate([header_first[0]+i*header_pitch,header_first[1],bare_origin[2]-bare_front_envelope-eps])
            cylinder(h=bare_front_envelope+bare_back_envelope+2*eps,d=1);
    }
}
module header_model() {
    translate([header_center[0]-header_body[0]/2,header_center[1]-header_body[1]/2,header_seat_z-header_body[2]]) cube(header_body);
    for(i=[0:6]) translate([header_first[0]+i*header_pitch-header_pin_width/2,header_first[1]-header_pin_width/2,header_seat_z-header_body[2]-header_long_leg])
        cube([header_pin_width,header_pin_width,header_body[2]+header_long_leg+header_short_leg]);
}
if(variant_part=="sensor") bare_sensor();
else if(variant_part=="header") header_model();
else if(assembly_coordinates) personal_carrier();
else translate([0,case_depth,carrier_z+carrier_thickness]) rotate([180,0,0]) personal_carrier();
