// Sensor Workshop v0.2. Two printed parts; source-based prototype.
// Board-derived geometry: Adafruit CC BY-SA 3.0; see reference/ATTRIBUTION.md.
include <parameters.scad>
include <generated/boards.scad>
include <generated/cables.scad>

/* [View] */
view = "assembled"; // [assembled, exploded, open, underside, section_front, section_side, print, coupon, collision]
part = "all"; // [all, shell, carrier, coupon]
show_components = true;
show_wires = true;
use_vendor_models = false;
assembly_coordinates = false;
$fn = 48;
eps = 0.02;

assert(battery_diameter <= 20 && battery_length <= 72,"Revise the bay for a larger local pack.");
assert(scd30_origin[2]+2.935 < carrier_z,"SCD30 underside pins intersect carrier.");
assert(scd30_origin[2]-8.57 > skirt_bottom,"Keep the sensing body above the skirt edge.");

module rounded_box(size,r=3) {
    linear_extrude(size[2]) offset(r=r)
        translate([r,r]) square([size[0]-2*r,size[1]-2*r]);
}
module ring(size,t,r,h) {
    difference() {
        rounded_box([size[0],size[1],h],r);
        translate([t,t,-eps]) rounded_box([size[0]-2*t,size[1]-2*t,h+2*eps],max(.3,r-t));
    }
}
module y_cylinder(h,d) {rotate([-90,0,0]) cylinder(h=h,d=d);}
module board_transform(which) {
    if(which=="feather") translate(feather_origin) rotate([-90,0,0]) children();
    if(which=="rtc") translate(rtc_origin) rotate([0,0,90]) children();
    if(which=="light") translate(light_origin) children();
    if(which=="scd30") translate(scd30_origin) rotate([180,0,0]) children();
}
function rtc_xy(p) = [rtc_origin[0]-p[1],rtc_origin[1]+p[0]];
module boss(xy,z0,z1,d=4.8,pilot=m2_pilot) {
    translate([xy[0],xy[1],z0]) difference() {
        cylinder(h=z1-z0,d=d);
        if(pilot>0) translate([0,0,-eps]) cylinder(h=z1-z0+2*eps,d=pilot);
    }
}
module front_mount(p,pinned=false) {
    x=feather_origin[0]+p[0]; z=feather_origin[2]-p[1];
    difference() {
        hull() {
            translate([x,wall-eps,z]) y_cylinder(feather_origin[1]-wall+eps,4.3);
            // Gusset grows from the roof side when shell is printed upside-down.
            translate([x-2.15,wall-eps,z]) cube([4.3,.4,4]);
        }
        if(!pinned) translate([x,.75,z]) y_cylinder(feather_origin[1]+.1,m2_pilot);
    }
    if(pinned) translate([x,feather_origin[1]-eps,z]) y_cylinder(locating_height+eps,locating_pin);
}
module roof_mount(p,origin,pinned=false) {
    xy=[origin[0]+p[0],origin[1]+p[1]];
    boss(xy,origin[2]+pcb_thickness,case_top+.05,4.8,pinned?0:m2_pilot);
    if(pinned) translate([xy[0],xy[1],origin[2]+pcb_thickness-locating_height])
        cylinder(h=locating_height+.05,d=locating_pin);
}
module battery_saddle(x) {
    difference() {
        translate([x-3,battery_center[1]-12.5,battery_center[2]-1])
            cube([6,25,case_top-battery_center[2]+1+.05]);
        translate([x-4,battery_center[1],battery_center[2]]) rotate([0,90,0])
            cylinder(h=8,d=battery_diameter+.8);
        // One short bridge across X, rather than holes through the exterior roof.
        translate([x-tie_slot_width/2,battery_center[1]-13,tie_tunnel_z])
            cube([tie_slot_width,26,1.8]);
    }
}
module optic_opening() {
    xy=[light_origin[0]+light_optic[0],light_origin[1]+light_optic[1]];
    hull() {
        translate([xy[0]-6,xy[1]-3,case_top-eps]) cube([12,6,.04]);
        translate([xy[0]-8.5,xy[1]-6,case_top+roof_thickness]) cube([17,12,.04]);
    }
}
module shell() {
    difference() {
        union() {
            // Closed top, continuous sides, open skirt underneath.
            translate([0,0,skirt_bottom]) ring([case_width,case_depth],wall,corner_radius,case_top-skirt_bottom+.05);
            translate([0,0,case_top]) rounded_box([case_width,case_depth,roof_thickness],corner_radius);
            // Four straight corner feet are portions of the same wall, not separate pieces.
            intersection() {
                ring([case_width,case_depth],wall,corner_radius,skirt_bottom+.05);
                for(x=[0,case_width-foot_span]) for(y=[0,case_depth-foot_span])
                    translate([x,y,0]) cube([foot_span,foot_span,skirt_bottom+.1]);
            }
            // Carrier seats against this narrow continuous shoulder.
            translate([wall-.1,wall-.1,carrier_z+carrier_thickness])
                ring([case_width-2*wall+.2,case_depth-2*wall+.2],1.4,corner_radius-wall+.1,1.4);
            for(p=case_mounts) translate([p[0],p[1],carrier_z+carrier_thickness])
                cylinder(h=case_top-carrier_z-carrier_thickness+.05,d=7.6);
            for(i=[0:3]) front_mount(feather_holes[i],i==1 || i==2);
            for(i=[0:3]) roof_mount(veml7700_holes[i],light_origin,i==1 || i==2);
            for(p=rtc_holes) boss(rtc_xy(p),rtc_origin[2]+pcb_thickness,case_top+.05,5.2);
            // Internal light well; sensing package remains clear on every side.
            translate([light_origin[0]+light_optic[0]-7.5,light_origin[1]+light_optic[1]-4,light_origin[2]+pcb_thickness+.15])
                ring([15,8],1.2,1,case_top-light_origin[2]-pcb_thickness-.15+.05);
            for(x=battery_saddles) battery_saddle(x);
            // 76 mm axial bay; lead exits below these short upper end stops.
            for(x=[6.5,84]) translate([x,46,45]) cube([1.5,8,case_top-45+.05]);
        }
        optic_opening();
        // Recess the inside of the front rim, leaving 0.25 mm in front of the TFT glass.
        translate([feather_origin[0]+11.05,1.65,feather_origin[2]-20.35]) cube([31.6,3,18.1]);
        translate([feather_origin[0]+12.6,-eps,feather_origin[2]-19.3]) cube([27,wall+2*eps,16]);
        // A single slot provides finger/nail access to all three real PCB buttons.
        translate([feather_origin[0]+7.62-3.5,-eps,feather_origin[2]-22.43]) cube([7,wall+2*eps,22]);
        translate([feather_origin[0]+feather_reset[0]-2.6,1.65,feather_origin[2]-feather_reset[1]-1.7]) cube([5.2,2.5,3.4]);
        translate([feather_origin[0]+feather_reset[0],-eps,feather_origin[2]-feather_reset[1]]) y_cylinder(wall+2*eps,2);
        translate([-eps,2.7,38.5]) cube([wall+2*eps,10.8,14]);
        for(x=[35,43,51,59]) translate([x,case_depth-wall-eps,48]) cube([4,wall+2*eps,8]);
        for(p=case_mounts) translate([p[0],p[1],carrier_z+carrier_thickness-eps]) cylinder(h=9,d=m3_pilot);
        for(i=board_screw_indices) let(p=veml7700_holes[i])
            translate([light_origin[0]+p[0],light_origin[1]+p[1],case_top-1]) cylinder(h=1.9,d=m2_pilot);
        for(p=rtc_holes) let(xy=rtc_xy(p)) translate([xy[0],xy[1],case_top-1]) cylinder(h=1.9,d=m2_pilot);
    }
}
module carrier() {
    margin=wall+fit_clearance;
    difference() {
        union() {
            translate([margin,margin,carrier_z])
                rounded_box([case_width-2*margin,case_depth-2*margin,carrier_thickness],corner_radius-margin);
            for(i=[0:3]) let(p=scd30_holes[i], xy=[scd30_origin[0]+p[0],scd30_origin[1]-p[1]], pinned=i==1 || i==2) {
                boss(xy,scd30_origin[2],carrier_z+.05,4.8,pinned?0:m2_pilot);
                if(pinned) translate([xy[0],xy[1],scd30_origin[2]-locating_height]) cylinder(h=locating_height+.05,d=locating_pin);
            }
        }
        for(p=case_mounts) translate([p[0],p[1],carrier_z-eps]) cylinder(h=carrier_thickness+2*eps,d=3.4);
        for(i=board_screw_indices) let(p=scd30_holes[i]) translate([scd30_origin[0]+p[0],scd30_origin[1]-p[1],carrier_z-eps]) cylinder(h=.8,d=m2_pilot);
        translate([13.5,29,carrier_z-eps]) rounded_box([7.5,9,carrier_thickness+2*eps],1.2);
    }
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
    color("#5589b4") translate(battery_center) rotate([0,90,0]) cylinder(h=battery_length,d=battery_diameter,center=true);
}
module components() {
    board_transform("feather") feather_model();
    board_transform("rtc") rtc_model();
    board_transform("light") light_model();
    board_transform("scd30") scd30_model();
    battery_model();
}
module assembly() {
    if(view!="open") color("#e5e8e3") shell();
    color("#4f7777") carrier();
    if(show_components) components();
    if(show_wires) cables();
}
module exploded() {
    color("#e5e8e3") shell();
    translate([0,0,-46]) color("#4f7777") carrier();
    translate([0,0,-65]) board_transform("scd30") scd30_model();
    translate([0,-28,-5]) board_transform("feather") feather_model();
    translate([0,0,-18]) board_transform("light") light_model();
    translate([25,0,-18]) board_transform("rtc") rtc_model();
    translate([0,22,-22]) battery_model();
}
module coupon() {
    // Shared setup gauges, not extra pieces per student device.
    for(i=[0:3]) let(sizes=[feather_size,scd30_size,veml7700_size,rtc_size],
        holes=[feather_holes,scd30_holes,veml7700_holes,rtc_holes],pos=[[0,0],[0,36],[64,0],[64,36]])
        translate([pos[i][0],pos[i][1],0]) difference() {
            union() {
                rounded_box([sizes[i][0]+4,sizes[i][1]+4,1.6],2);
                for(j=[0:len(holes[i])-1]) let(p=holes[i][j]) {
                    translate([p[0]+2,p[1]+2,1.6]) cylinder(h=4,d=4.8);
                    if(i!=3 && (j==1 || j==2)) translate([p[0]+2,p[1]+2,5.6-eps]) cylinder(h=locating_height+eps,d=locating_pin);
                }
            }
            for(j=[0:len(holes[i])-1]) if(i==3 || j==0 || j==3) let(p=holes[i][j])
                translate([p[0]+2,p[1]+2,-eps]) cylinder(h=6,d=m2_pilot);
        }
    translate([0,73,0]) difference() {
        rounded_box([42,16,6],2);
        for(i=[0:3]) translate([7+i*9,8,-eps]) cylinder(h=7,d=1.6+i*.1);
    }
    translate([50,73,0]) difference() {
        rounded_box([42,16,8],2);
        for(i=[0:3]) translate([7+i*9,8,-eps]) cylinder(h=9,d=2.4+i*.1);
    }
    translate([100,0,0]) difference() {cube([33,5,12]);translate([3,-eps,-eps]) cube([27,5+2*eps,10]);}
    translate([100,16,0]) difference() {rounded_box([28,28,3],2);translate([14,14,-eps]) cylinder(h=4,d=battery_diameter+.8);}
}
module single_part(name) {
    if(name=="shell") translate([0,case_depth,case_top+roof_thickness]) rotate([180,0,0]) shell();
    if(name=="carrier") translate([0,case_depth,carrier_z+carrier_thickness]) rotate([180,0,0]) carrier();
    if(name=="coupon") coupon();
}
module positioned_part(name) {
    if(name=="shell") shell();
    if(name=="carrier") carrier();
    if(name=="feather") board_transform("feather") feather_model();
    if(name=="rtc") board_transform("rtc") rtc_model();
    if(name=="light") board_transform("light") light_model();
    if(name=="scd30") board_transform("scd30") scd30_model();
    if(name=="battery") battery_model();
}
if(part!="all" && assembly_coordinates) positioned_part(part);
else if(part!="all") single_part(part);
else if(view=="exploded") exploded();
else if(view=="coupon") coupon();
else if(view=="section_front") intersection(){assembly();translate([-10,33,-80]) cube([150,80,200]);}
else if(view=="section_side") intersection(){assembly();translate([43,-10,-80]) cube([100,100,200]);}
else if(view=="collision") intersection(){union(){shell();carrier();}components();}
else if(view=="print"){single_part("shell");translate([100,0,0]) single_part("carrier");}
else if(view=="underside") rotate([180,0,0]) assembly();
else assembly();
