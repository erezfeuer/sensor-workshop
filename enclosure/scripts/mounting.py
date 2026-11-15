"""Nominal optional mounting illustration; no printed mounting accessories.

The tie follows the convex outline of case + pole at the band height. This
checks a plausible route, not tension, grip, compression or load capacity.
"""
import trimesh
from shapely.geometry import Point, box
from shapely.ops import unary_union


def mounting_example(p):
    w,d,r=p['case_width'],p['case_depth'],p['corner_radius']
    body=box(r,r,w-r,d-r).buffer(r,quad_segs=12)
    # The strap bears on the original rounded corners, between raised shoulders.
    radius=p['mount_example_pole_diameter']/2
    pole_xy=[w/2,d+p['mount_example_pad_thickness']+radius]
    pole_outline=Point(pole_xy).buffer(radius,quad_segs=24)
    hull=unary_union([body,pole_outline]).convex_hull
    # 0.2 mm illustrative surface clearance; 1.2 mm nominal tie thickness.
    inner=hull.buffer(.2,quad_segs=12)
    outer=hull.buffer(1.4,quad_segs=12)
    strap=trimesh.creation.extrude_polygon(outer.difference(inner),height=p['mount_band_width'],engine='earcut')
    strap.apply_translation([0,0,p['mount_band_z']-p['mount_band_width']/2])
    head=trimesh.creation.box(extents=[5.2,7.2,8])
    head.apply_translation([w+2.7,22,p['mount_band_z']])
    strap=trimesh.boolean.union([strap,head],engine='manifold')
    pole=trimesh.creation.cylinder(radius=radius,height=110,sections=96)
    pole.apply_translation([*pole_xy,p['mount_band_z']])
    pad=trimesh.creation.box(extents=[18,p['mount_example_pad_thickness'],16])
    pad.apply_translation([w/2,d+p['mount_example_pad_thickness']/2,p['mount_band_z']])
    return {'mount_tie':strap,'mount_pole':pole,'mount_pad':pad}, {
        'pole_diameter_mm':p['mount_example_pole_diameter'],
        'pad_thickness_mm':p['mount_example_pad_thickness'],
        'tie_width_mm':p['mount_band_width'],
        'corner_guides':4,
        'guide_depth_mm':p['mount_groove_depth'],
        'illustrated_loop_length_mm':round(hull.buffer(.8,quad_segs=12).exterior.length,1),
        'note':'Loop length excludes locking-head allowance and the free tail needed to thread and tighten. This is not a load rating.'}
