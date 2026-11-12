// Sensor Workshop v0.1. Prototype: fit coupons and physical checks required.
// Original enclosure design. Board XY derived from Adafruit CC BY-SA sources.
include <parameters.scad>
include <generated/boards.scad>

/* [View] */
view = "assembled"; // [assembled, exploded, section_front, section_side, open, print, collision, coupon]
part = "all"; // [all, base, lid, pod, shade, foot_front, foot_rear, button, coupon]
show_components = true;
show_wires = true;
use_vendor_models = false; // downloaded vendor STLs, optional
assembly_coordinates = false; // export individual parts in their assembled positions
$fn = 48;
eps = 0.02;

assert(battery_diameter <= 20 && battery_length <= 72,
       "Battery exceeds v0.1 bay. Revise cradles, end stops and clearance checks.");
assert(case_top-light_origin[2]-pcb_thickness >= 3.2,
       "Light-board QT connectors require >=3.2 mm overhead clearance.");
assert(scd30_origin[2]-2.935 > pod_origin[2]+pod_floor,
       "SCD30 underside pins intersect tray floor.");

module rounded_box(size,r=3) {
    linear_extrude(size[2]) offset(r=r)
        translate([r,r]) square([size[0]-2*r,size[1]-2*r]);
}
module hex_hole(h,af=m3_nut_af) {
    rotate([0,0,30]) cylinder(h=h,d=af/cos(30),$fn=6);
}
module ring(size,t,r,h) {
    difference() {
        rounded_box([size[0],size[1],h],r);
        translate([t,t,-eps]) rounded_box([size[0]-2*t,size[1]-2*t,h+2*eps],max(0.3,r-t));
    }
}
module y_cylinder(h,d) { rotate([-90,0,0]) cylinder(h=h,d=d); }
module board_transform(which) {
    if(which=="feather") translate(feather_origin) rotate([-90,0,0]) children();
    if(which=="rtc") translate(rtc_origin) children();
    if(which=="light") translate(light_origin) children();
    if(which=="scd30") translate(scd30_origin) children();
}
module vertical_boss(p,z0,z1,d=4.6,pilot=m2_pilot) {
    translate([p[0],p[1],z0]) difference() {
        cylinder(h=z1-z0,d=d);
        translate([0,0,-eps]) cylinder(h=z1-z0+2*eps,d=pilot);
    }
}
module front_boss(p) {
    x=feather_origin[0]+p[0]; z=feather_origin[2]-p[1];
    difference() {
        hull() {
            translate([x,wall-eps,z]) y_cylinder(feather_origin[1]-wall+eps,4.3);
            translate([x-2.15,wall-eps,z-7]) cube([4.3,0.4,7]);
        }
        translate([x,0.9,z]) y_cylinder(feather_origin[1]+1,m2_pilot);
    }
}

module battery_saddle(x) {
    difference() {
        translate([x-4,battery_center[1]-12.5,base_z+floor_thickness-eps])
            rounded_box([8,25,battery_center[2]+1-base_z-floor_thickness+eps],1);
        translate([x-5,battery_center[1],battery_center[2]]) rotate([0,90,0])
            cylinder(h=10,d=battery_diameter+0.8);
    }
}
module base() {
    difference() {
        union() {
            translate([0,0,base_z]) difference() {
                rounded_box([case_width,case_depth,case_top-base_z],corner_radius);
                translate([wall,wall,floor_thickness])
                    rounded_box([case_width-2*wall,case_depth-2*wall,case_top-base_z],corner_radius-wall);
            }
            for(p=leg_mounts) translate([p[0],p[1],base_z])
                cylinder(h=case_top-base_z,d=10);
            for(p=feather_holes) front_boss(p);
            for(p=rtc_holes) vertical_boss([rtc_origin[0]+p[0],rtc_origin[1]+p[1]],base_z+floor_thickness-eps,rtc_origin[2],5.2);
            for(x=[32,80]) battery_saddle(x);
            // End stops allow 76 mm axial space, plus open cable exits above.
            for(x=[17,94]) translate([x,58,base_z+floor_thickness-eps])
                rounded_box([2,16,6],0.8);
            // Adjustable inline-switch back support with tie slots.
            translate([17.5,26,base_z+floor_thickness-eps]) cube([2.4,32,25]);
            // Cable-coil tie points, inside main compartment.
            for(x=[32,62]) translate([x,34,base_z+floor_thickness-eps])
                difference() { cube([5,10,4]); translate([1,2,-eps]) cube([3,6,5]); }
        }
        // Display opening exposes active area; retains a rim over glass edges.
        translate([feather_origin[0]+11.8,-eps,feather_origin[2]-19.55])
            cube([30,wall+2*eps,16.5]);
        for(p=feather_buttons) translate([feather_origin[0]+p[0],-eps,feather_origin[2]-p[1]])
            y_cylinder(wall+2*eps,button_hole);
        translate([feather_origin[0]+feather_reset[0],-eps,feather_origin[2]-feather_reset[1]])
            y_cylinder(wall+2*eps,2);
        // USB-C plug envelope; a generous access cutout, not just socket width.
        translate([-eps,3.8,51]) cube([wall+2*eps,12.4,14.8]);
        // Universal switch access; body retained with ties, not a guessed snap fit.
        translate([-eps,30,46]) cube([wall+2*eps,24,14]);
        for(y=[29,51]) translate([16.5,y,47]) cube([5,3,12]);
        // Upper electronics exhausts; separated from the lower sensing chamber.
        for(x=[22:8:94]) translate([x,case_depth-wall-eps,66]) cube([4,wall+2*eps,6]);
        for(p=leg_mounts) {
            translate([p[0],p[1],base_z-eps]) cylinder(h=case_top-base_z+2*eps,d=m3_clearance);
            translate([p[0],p[1],base_z-eps]) cylinder(h=1.4,d=8.4);
        }
        for(p=pod_mounts) translate([p[0],p[1],base_z-eps])
            cylinder(h=floor_thickness+2*eps,d=m3_clearance);
        // Two straps wrap the battery's circumference through these slots.
        for(x=[32,80]) for(y=[53,78.5])
            translate([x-strap_width/2-0.3,y-1.1,base_z-eps]) cube([strap_width+0.6,2.2,floor_thickness+2*eps]);
        // Offset from the pod roof slot; wire bends in the intervening air gap.
        translate([14,39,base_z-eps]) cube([10,6,floor_thickness+2*eps]);
    }
}

module optic_aperture() {
    x=light_origin[0]+light_optic[0]; y=light_origin[1]+light_optic[1];
    hull() {
        translate([x-6,y-3,case_top-eps]) cube([12,6,0.04]);
        translate([x-8.5,y-6,case_top+lid_thickness]) cube([17,12,0.04]);
    }
}
module lid() {
    difference() {
        union() {
            translate([0,0,case_top]) rounded_box([case_width,case_depth,lid_thickness],corner_radius);
            // Short locating tabs avoid mounting towers and cable connectors.
            for(x=[26,62]) for(y=[wall+fit_clearance,case_depth-wall-fit_clearance-1.2])
                translate([x,y,case_top-1.6]) cube([14,1.2,1.8]);
            for(p=veml7700_holes)
                vertical_boss([light_origin[0]+p[0],light_origin[1]+p[1]],light_origin[2]+pcb_thickness,case_top+0.05,4.6);
            // Opaque light well shields the sensing face from internal LEDs.
            translate([light_origin[0]+light_optic[0]-7.5,light_origin[1]+light_optic[1]-4,light_origin[2]+pcb_thickness+0.15])
                ring([15,8],1.2,1,case_top-light_origin[2]-pcb_thickness-0.15+0.05);
        }
        optic_aperture();
        for(p=leg_mounts) translate([p[0],p[1],case_top-eps])
            cylinder(h=lid_thickness+2*eps,d=m3_clearance);
        // Blind pilot extension into lid, leaving >=1.5 mm outer skin.
        for(p=veml7700_holes) translate([light_origin[0]+p[0],light_origin[1]+p[1],case_top-1])
            cylinder(h=1.9,d=m2_pilot);
    }
}

module vent_cuts(inset,z0,height) {
    // Segmented horizontal slots preserve vertical ribs and corner fasteners.
    x0=pod_origin[0]+inset; y0=pod_origin[1]+inset;
    sx=pod_size[0]-2*inset; sy=pod_size[1]-2*inset;
    for(x=[x0+12:14:x0+sx-15]) for(y=[y0-0.1,y0+sy-pod_wall-0.1])
        translate([x,y,z0]) cube([10,pod_wall+0.2,height]);
    for(y=[y0+11:13:y0+sy-14]) for(x=[x0-0.1,x0+sx-pod_wall-0.1])
        translate([x,y,z0]) cube([pod_wall+0.2,9,height]);
}
module pod() {
    difference() {
        union() {
            translate(pod_origin) rounded_box([pod_size[0],pod_size[1],pod_floor],4);
            // Outer inlets LOW; inner inlets HIGH: no downward sunlight path.
            for(inset=[0,pod_baffle_inset]) difference() {
                translate([pod_origin[0]+inset,pod_origin[1]+inset,pod_origin[2]+pod_floor-eps])
                    ring([pod_size[0]-2*inset,pod_size[1]-2*inset],pod_wall,max(1,4-inset),pod_roof_z-pod_origin[2]-pod_floor+eps);
                vent_cuts(inset,inset==0?13:21,5);
            }
            for(p=pod_mounts) translate([p[0],p[1],pod_origin[2]])
                cylinder(h=pod_roof_z-pod_origin[2],d=8);
            for(p=scd30_holes)
                vertical_boss([scd30_origin[0]+p[0],scd30_origin[1]+p[1]],pod_origin[2]+pod_floor-eps,scd30_origin[2],4.6);
        }
        for(p=pod_mounts) {
            translate([p[0],p[1],pod_origin[2]-eps]) cylinder(h=20,d=m3_clearance);
            translate([p[0],p[1],pod_origin[2]-eps]) hex_hole(4.4+eps);
        }
    }
}
module shade() {
    difference() {
        union() {
            translate([pod_origin[0]-3,pod_origin[1]-3,pod_roof_z])
                rounded_box([pod_size[0]+6,pod_size[1]+6,pod_roof_thickness],5);
            for(p=pod_mounts) translate([p[0],p[1],pod_roof_z+pod_roof_thickness-eps])
                cylinder(h=base_z-pod_roof_z-pod_roof_thickness+eps,d=8);
        }
        for(p=pod_mounts) translate([p[0],p[1],pod_roof_z-eps])
            cylinder(h=base_z-pod_roof_z+2*eps,d=m3_clearance);
        translate([27,39,pod_roof_z-eps]) cube([9,6,pod_roof_thickness+2*eps]);
    }
}

module foot(rear=false) {
    shift=rear?foot_splay:-foot_splay;
    difference() {
        union() {
            hull() {
                translate([0,shift,0]) cylinder(h=2,d=16);
                translate([0,0,base_z-1.2]) cylinder(h=1.2,d=12);
            }
            translate([0,0,base_z-eps]) cylinder(h=1.2+eps,d=8);
        }
        translate([0,0,base_z-12]) cylinder(h=14,d=m3_clearance);
        translate([0,0,base_z-2.6]) hex_hole(4);
    }
}
module button() {
    // Local axis is Y, front outside at negative Y. Printed axis vertical.
    union() {
        translate([0,-button_protrusion,0]) y_cylinder(button_protrusion+0.1,6);
        translate([0,0,0]) y_cylinder(wall+0.75,button_neck);
        translate([0,wall,0]) y_cylinder(0.7,button_flange);
        translate([0,wall+0.65,0]) y_cylinder(button_stem_end-wall-0.65,2.8);
    }
}
module buttons() {
    for(p=feather_buttons) translate([feather_origin[0]+p[0],0,feather_origin[2]-p[1]]) button();
}

module pcb(size,holes) {
    difference() {
        rounded_box([size[0],size[1],pcb_thickness],2.5);
        for(h=holes) translate([h[0],h[1],-0.1]) cylinder(h=pcb_thickness+0.2,d=h[2]);
    }
}
module qt_socket(p) { translate([p[0]-2.3,p[1]-3.1,pcb_thickness]) cube([4.6,6.2,3]); }
module feather_model() {
    if(use_vendor_models) color("seagreen") import("../hardware/reference/vendor/feather/model.stl");
    else {
        color("#194746") pcb(feather_size,feather_holes);
        color("#343b42") translate([11.291,2.503,-1.9]) cube([31,17.6,1.9]);
        color("#3ac5c2") translate([12.891,3.903,-1.92]) cube([24.9,14.8,0.05]);
        color("silver") translate([-1.213,6.96,pcb_thickness]) cube([7.2,8.94,3.2]);
        color("#d7dbd8") translate([28.4,3.6,pcb_thickness]) cube([17,15.6,2.5]);
        color("#efcc73") translate([45.4,3.6,pcb_thickness]) cube([5.4,15.6,0.6]);
        color("ivory") qt_socket([23.622,11.43]);
        color("ivory") translate([6.8,14.8,pcb_thickness]) cube([8,7.5,4.77]);
        for(p=concat(feather_buttons,[feather_reset])) color("#b2b8b8")
            translate([p[0]-2.3,p[1]-1.4,-1.9]) cube([4.6,2.8,1.9]);
    }
}
module scd30_model() {
    if(use_vendor_models) color("#c9a66b") import("../hardware/reference/vendor/scd30/model.stl");
    else {
        color("#174845") pcb(scd30_size,scd30_holes);
        color("#c9a66b") translate([8.38,1,pcb_thickness]) cube([35,23,6.97]);
        color("#e0e0d2") for(y=[8.89,16.51]) qt_socket([2.667,y]);
        color("silver") translate([44,5,-2.935]) cube([1,15,2.935]);
    }
}
module rtc_model() {
    if(use_vendor_models) color("#6f70a4") import("../hardware/reference/vendor/rtc/model.stl");
    else {
        color("#405058") pcb(rtc_size,rtc_holes);
        color("#303335") translate([7.5,2,pcb_thickness]) cube([10.4,7.5,2.93]);
        color("silver") translate([12.7,10.795,-3.2]) cylinder(h=3.2,d=13);
        color("ivory") for(x=[2.54,22.86]) qt_socket([x,8.89]);
    }
}
module light_model() {
    color("#243e50") pcb(veml7700_size,veml7700_holes);
    color("#303438") translate([light_optic[0]-3.4,light_optic[1]-1.5,pcb_thickness]) cube([6.8,3,2.35]);
    color("#8ab3ca") translate([light_optic[0]-1.5,light_optic[1]-0.75,pcb_thickness+2.35]) cube([3,1.5,0.01]);
    color("ivory") for(x=[2.667,22.733]) qt_socket([x,8.89]);
}
module battery_model() {
    color("#5589b4") translate(battery_center) rotate([0,90,0])
        cylinder(h=battery_length,d=battery_diameter,center=true);
}
module tube(points,d=2) {
    for(i=[0:len(points)-2]) hull() {
        translate(points[i]) sphere(d=d,$fn=12);
        translate(points[i+1]) sphere(d=d,$fn=12);
    }
}
module wires() {
    // Suggested routing envelopes only; bend radii and plug bodies need fit checks.
    color("#d7a63e") tube([[29,12,58.6],[25,20,58.6],[60,22,53],[70,39,47],[77,39,47]]);
    color("#d7a63e") tube([[101,39,47],[106,49,57],[103,53,74],[98,53,74]]);
    color("#d7a63e") tube([[74,53,74],[65,49,69],[30,46,60],[19,42,38],[19,42,32],[31,42,32],[31,42,25],[31,45,20],[35.5,45,20]]);
    color("#c74a42") tube([[92,66,50],[96,60,50],[62,35,46],[46,35,46],[46,46,46],[60,46,46],[60,36,46],[18,42,52]]);
    color("#343434") tube([[18,42,54],[26,35,53],[28,20,56],[19,17,65]]);
}
module components() {
    board_transform("feather") feather_model();
    board_transform("rtc") rtc_model();
    board_transform("light") light_model();
    board_transform("scd30") scd30_model();
    battery_model();
    color("#3b4248") translate(switch_origin) rounded_box(switch_envelope,3);
}
module printed_parts(with_lid=true) {
    color("#e5e8e3") base();
    if(with_lid) color("#edf0e9") lid();
    color("#4c696c") pod();
    color("#bdc7c3") shade();
    for(i=[0:3]) color("#4c696c") translate([leg_mounts[i][0],leg_mounts[i][1],0]) foot(i>=2);
    color("#e2ae44") buttons();
}
module assembly() {
    printed_parts(view!="open");
    if(show_components) components();
    if(show_wires) wires();
}
module exploded() {
    color("#e5e8e3") base();
    translate([0,0,32]) { color("#edf0e9") lid(); board_transform("light") light_model(); }
    translate([0,0,-8]) color("#bdc7c3") shade();
    translate([0,0,-38]) { color("#4c696c") pod(); board_transform("scd30") scd30_model(); }
    for(i=[0:3]) color("#4c696c") translate([leg_mounts[i][0]+(i%2==0?-16:16),leg_mounts[i][1],-22]) foot(i>=2);
    board_transform("feather") feather_model();
    board_transform("rtc") rtc_model();
    battery_model();
    translate([0,-14,0]) color("#e2ae44") buttons();
}
module coupon() {
    // Independent coupons: verify the actual boards before a full case print.
    for(i=[0:3]) let(sizes=[feather_size,scd30_size,veml7700_size,rtc_size],
        holes=[feather_holes,scd30_holes,veml7700_holes,rtc_holes],
        pos=[[0,0],[0,36],[64,0],[64,36]])
        translate([pos[i][0],pos[i][1],0]) difference() {
            union() {
                rounded_box([sizes[i][0]+4,sizes[i][1]+4,1.6],2);
                for(p=holes[i]) translate([p[0]+2,p[1]+2,1.6]) cylinder(h=4,d=4.3);
            }
            for(p=holes[i]) translate([p[0]+2,p[1]+2,-eps]) cylinder(h=6,d=m2_pilot);
        }
    translate([0,73,0]) difference() {
        rounded_box([42,16,5],2);
        for(i=[0:3]) translate([7+i*9,8,-eps]) cylinder(h=6,d=1.6+i*0.1);
    }
    translate([50,73,0]) difference() {
        rounded_box([42,16,5],2);
        for(i=[0:3]) translate([6+i*10,8,1.5]) hex_hole(4,5.5+i*0.1);
    }
    // Match the main display's 30 mm bridge before committing to the housing.
    translate([100,0,0]) difference() {
        cube([36,5,12]); translate([3,-eps,-eps]) cube([30,5+2*eps,10]);
    }
    translate([100,16,0]) difference() {
        rounded_box([28,28,3],2);
        translate([14,14,-eps]) cylinder(h=3+2*eps,d=battery_diameter+0.8);
    }
}
module single_part(name) {
    if(name=="base") translate([0,0,-base_z]) base();
    if(name=="lid") translate([0,case_depth,case_top+lid_thickness]) rotate([180,0,0]) lid();
    if(name=="pod") translate([-pod_origin[0],-pod_origin[1],-pod_origin[2]]) pod();
    if(name=="shade") translate([-pod_origin[0]+3,-pod_origin[1]+3,-pod_roof_z]) shade();
    if(name=="foot_front") translate([8,20,0]) foot(false);
    if(name=="foot_rear") translate([8,8,0]) foot(true);
    if(name=="button") translate([3,3,button_protrusion]) rotate([90,0,0]) button();
    if(name=="coupon") coupon();
}

module positioned_part(name) {
    if(name=="base") base();
    if(name=="lid") lid();
    if(name=="pod") pod();
    if(name=="shade") shade();
    if(name=="feet") for(i=[0:3]) translate([leg_mounts[i][0],leg_mounts[i][1],0]) foot(i>=2);
    if(name=="buttons") buttons();
    if(name=="feather") board_transform("feather") feather_model();
    if(name=="scd30") board_transform("scd30") scd30_model();
    if(name=="rtc") board_transform("rtc") rtc_model();
    if(name=="light") board_transform("light") light_model();
    if(name=="battery") battery_model();
    if(name=="switch") translate(switch_origin) rounded_box(switch_envelope,3);
    if(name=="wires") wires();
}

if(part!="all" && assembly_coordinates) positioned_part(part);
else if(part!="all") single_part(part);
else if(view=="exploded") exploded();
else if(view=="section_front") intersection() { assembly(); translate([-30,42,-60]) cube([200,120,220]); }
else if(view=="section_side") intersection() { assembly(); translate([48,-30,-60]) cube([150,180,220]); }
else if(view=="collision") intersection() { printed_parts(); components(); }
else if(view=="coupon") coupon();
else if(view=="print") {
    single_part("base");
    translate([120,0,0]) single_part("lid");
    translate([0,95,0]) single_part("pod");
    translate([90,95,0]) single_part("shade");
    for(i=[0:3]) translate([180+i%2*22,95+floor(i/2)*40,0]) single_part(i<2?"foot_front":"foot_rear");
    for(i=[0:2]) translate([0+i*10,152,0]) single_part("button");
} else assembly();
