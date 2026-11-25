#!/usr/bin/env python3
"""Check the three-piece print set, assembled clearances and routed mesh envelopes."""
import hashlib
import itertools
import json
import warnings
import numpy as np
import trimesh
import pymupdf
from render_review import ROOT,CAD,PARAMS as p
from build_viewer import tie_mesh
from mounting import mounting_example

warnings.filterwarnings('ignore',category=RuntimeWarning,module='trimesh.triangles')
boards=json.loads((CAD/'generated/boards.json').read_text())
light=boards[p['light_sensor']]
assert boards['tsl2591']['holes']==boards['veml7700']['holes']
assert boards['tsl2591']['size']==boards['veml7700']['size']
for connector in ('CONN3','CONN4'):
    assert boards['tsl2591']['elements'][connector]==boards['veml7700']['elements'][connector]
report={'version':p['enclosure_version'],'light_sensor':p['light_sensor'],'status':'passed','units':'mm','print_parts':{},'clearances':{},'references':0}
assert {x.stem for x in (CAD/'stl').glob('*.stl')}=={'shell','carrier','feather_frame','coupon'}
for name in ['shell','carrier','feather_frame','coupon']:
    path=CAD/'stl'/f'{name}.stl';m=trimesh.load_mesh(path);bodies=len(m.split())
    assert m.is_watertight and m.is_winding_consistent and m.volume>0,name
    assert bodies==(8 if name=='coupon' else 1),(name,bodies)
    assert abs(m.bounds[0,2])<.002,(name,m.bounds.tolist())
    report['print_parts'][name]={'watertight':True,'bodies':bodies,'size_mm':m.extents.round(3).tolist(),
        'solid_volume_mm3':round(m.volume,2),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
report['printed_pieces_per_device']=3
report['fasteners']={'M2x5':8,'M3x8':2,'M2_washers':2,'nuts':0,'battery_ties':2}
report['footprint_reduction_percent']=round(100*(1-p['case_width']*p['case_depth']/(112*84)),2)

def gap(name,value):
    assert value>0,(name,value)
    report['clearances'][name]=round(value,3)

gap('SCD30 upward pins to carrier',p['carrier_z']-p['scd30_origin'][2]-2.935)
gap('SCD30 body to table',p['scd30_origin'][2]-8.57)
gap('SCD30 body above skirt lower edge',p['scd30_origin'][2]-8.57-p['skirt_bottom'])
gap('Light QT to roof',p['case_top']-p['light_origin'][2]-4.6)
gap('Light package to roof',p['case_top']-p['light_origin'][2]-p['pcb_thickness']-light['package_size'][2])
gap('RTC QT to roof',p['case_top']-p['rtc_origin'][2]-4.6)
gap('Feather PCB top to roof',p['case_top']-p['feather_origin'][2])
gap('TFT glass to recessed inside rim',p['feather_origin'][1]-1.9-1.65)
gap('Battery to carrier top',p['battery_center'][2]-p['battery_diameter']/2-p['carrier_z']-p['carrier_thickness'])
gap('Nominal battery left end to side wall',p['battery_center'][0]-p['battery_length']/2-p['wall'])
gap('Nominal battery right end to side wall',p['case_width']-p['wall']-p['battery_center'][0]-p['battery_length']/2)
report['battery_retention']='Two cradle ties; no end stops. Axial slip and lead strain must be checked on the pilot.'
report['button_access_recess_mm']=round(p['feather_origin'][1]-1.9,2)
report['screw_engagement_mm']={
    'Feather M2x5':round(5-p['pcb_thickness'],2),
    'Light M2x5':round(5-p['pcb_thickness'],2),
    'RTC M2x5 with washer':round(5-p['pcb_thickness']-.5,2),
    'SCD30 M2x5':round(5-p['pcb_thickness'],2),
    'Carrier M3x8':round(8-p['carrier_thickness'],2)}
assert p['feather_origin'][1]+p['pcb_thickness']+p['feather_pilot_depth'] < 16.5
assert p['light_origin'][2]+5 < p['case_top']+p['roof_thickness']-1.0
assert p['scd30_origin'][2]-p['pcb_thickness']+5 < p['carrier_z']+p['carrier_thickness']-1.0

scene=CAD/'generated/scene'
meshes={n:trimesh.load_mesh(scene/(n+'.stl')) for n in ['shell','carrier','feather_frame','feather','light','rtc','scd30','battery']}
checks=[]
def check_pair(a,b,ma,mb):
    result=trimesh.boolean.intersection([ma,mb],engine='manifold')
    volume=abs(float(result.volume)) if len(result.faces) else 0.
    assert volume<.001,(a,b,volume,result.bounds.tolist())
    checks.append({'a':a,'b':b,'intersection_mm3':round(volume,6)})
for a,b in itertools.combinations(meshes,2):check_pair(a,b,meshes[a],meshes[b])
# Verify the deeper blind pilots and measure material through the reinforced
# threaded section. Cross-sectional area is geometry, not a torque rating.
report['feather_mounts']={'pilot_diameter_mm':p['m2_pilot'],'pilot_depth_mm':p['feather_pilot_depth'],
    'root_diameter_mm':p['feather_root_diameter'],'contact_land_length_mm':p['feather_contact_length'],
    'back_material_mm':round(16.5-p['feather_origin'][1]-p['pcb_thickness']-p['feather_pilot_depth'],3),
    'assumed_5_5mm_under_head_screw_tip_clearance_mm':round(p['feather_pilot_depth']-(5.5-p['pcb_thickness']),3),
    'sections':[],'removal_strength_tested':False}
for i in p['board_screw_indices']:
    x,y,_=boards['feather']['holes'][i]
    center=np.array([p['feather_origin'][0]+x,p['feather_origin'][1]+p['pcb_thickness'],p['feather_origin'][2]-y])
    bore=trimesh.creation.cylinder(radius=p['m2_pilot']/2-.05,height=p['feather_pilot_depth']-.04,sections=32)
    bore.apply_transform(trimesh.geometry.align_vectors([0,0,1],[0,1,0]))
    bore.apply_translation(center+[0,p['feather_pilot_depth']/2,0])
    check_pair(f'feather_blind_pilot_{i}','feather_frame',bore,meshes['feather_frame'])
    cap=trimesh.creation.box(extents=[1,.2,1]);cap.apply_translation(center+[0,p['feather_pilot_depth']+.12,0])
    solid=trimesh.boolean.intersection([cap,meshes['feather_frame']],engine='manifold')
    assert abs(solid.volume-cap.volume)<.001,('Blind pilot lacks end material',i)
    slab=trimesh.creation.box(extents=[9,.02,9]);slab.apply_translation(center+[0,2,0])
    section=trimesh.boolean.intersection([slab,meshes['feather_frame']],engine='manifold')
    area=float(section.volume)/.02
    old_diameter=4.3 if i<2 else 3.2
    old_area=np.pi*(old_diameter**2-p['m2_pilot']**2)/4
    assert area>old_area*1.5,('Insufficient reinforcement at threaded section',i,area,old_area)
    report['feather_mounts']['sections'].append({'hole_index':i,'depth_from_pcb_back_mm':2,
        'plastic_section_mm2':round(area,2),'v05_nominal_section_mm2':round(old_area,2),
        'area_ratio':round(area/old_area,2)})
# A vertical pencil of light over the whole TSL2591 array must reach the sky.
# This catches a misplaced window even if the short sensor package fits below it.
ox,oy=np.array(p['light_origin'][:2])+light['optic']
z=p['light_origin'][2]+p['pcb_thickness']+light['package_size'][2]+.02
height=p['case_top']+p['roof_thickness']+1-z
aperture=trimesh.creation.box(extents=[1.0,1.0,height]);aperture.apply_translation([ox,oy,z+height/2])
check_pair('light_vertical_optical_path','shell',aperture,meshes['shell'])
report['light_board']={'board_size_mm':light['size'],'holes':light['holes'],
    'qt_variants_share_outline_holes_and_sockets':True,
    'optic_center_board_mm':light['optic'],'optic_center_case_mm':[ox,oy],
    'package_size_mm':light['package_size'],'ancillary_envelope_height_mm':2.0 if p['light_sensor']=='tsl2591' else None,
    'vertical_optical_path_clear':True,'photometric_response_validated':False}
# All coloured wires and nominal plugs against solids, not just their centre lines.
for path in sorted(scene.glob('cable_*.stl')):
    m=trimesh.load_mesh(path)
    for name,other in meshes.items():check_pair(path.stem,name,m,other)
for i,x in enumerate(p['battery_saddles']):
    tie=tie_mesh(x)
    for name,other in meshes.items():check_pair(f'battery_tie_{i}',name,tie,other)
mounts,route=mounting_example(p)
for name,m in mounts.items():
    for other,mesh in meshes.items():check_pair(name,other,m,mesh)
for a,b in itertools.combinations(mounts,2):check_pair(a,b,mounts[a],mounts[b])
report['mounting_example']=route
gap('Mount band to front button opening',p['feather_origin'][2]-22.43-p['mount_band_z']-p['mount_band_width']/2)
gap('Mount band to USB opening',38.5-p['mount_band_z']-p['mount_band_width']/2)
gap('Mount band above carrier',p['mount_band_z']-p['mount_band_width']/2-p['carrier_z']-p['carrier_thickness'])
report['mounting_example']['side_wall_behind_guides_mm']=p['wall']
gap('Corner shoulder to USB opening',38.5-(p['mount_band_z']+p['mount_groove_width']/2+2*p['mount_groove_bevel']+p['mount_guide_land']))
gap('Front corner guide to button opening',p['feather_origin'][0]+7.62-3.5-p['corner_radius']-p['mount_corner_run'])
report['corner_guide_checks']=[]
for sx,sy in itertools.product([0,1],repeat=2):
    radius=p['corner_radius']+p['mount_groove_depth']/2
    v=p['corner_radius']-radius/np.sqrt(2)
    xy=[p['case_width']-v if sx else v,p['case_depth']-v if sy else v]
    for sign in [-1,1]:
        z=p['mount_band_z']+sign*(p['mount_groove_width']/2+p['mount_groove_bevel']+p['mount_guide_land']/2)
        gauge=trimesh.creation.box(extents=[.3,.3,.3]);gauge.apply_translation([*xy,z])
        solid=trimesh.boolean.intersection([gauge,meshes['shell']],engine='manifold')
        assert abs(solid.volume-gauge.volume)<.001,('Missing corner shoulder',sx,sy,sign)
    groove=trimesh.creation.box(extents=[.3,.3,.3]);groove.apply_translation([*xy,p['mount_band_z']])
    check_pair(f'corner_channel_{sx}_{sy}','shell',groove,meshes['shell'])
    report['corner_guide_checks'].append({'corner':[sx,sy],'upper_and_lower_shoulders':True,'channel_clear':True})
report['mesh_intersections']=checks
for e in json.loads((ROOT/'hardware/reference/manifest.json').read_text()):
    assert hashlib.sha256((ROOT/'hardware/reference'/e['path']).read_bytes()).hexdigest()==e['sha256']
    report['references']+=1
with pymupdf.open(CAD/'design-review.pdf') as pdf:
    assert len(pdf)==9
    report['review_pdf_pages']=len(pdf)
report['limitations']=['Earlier shell printed well in PLA; unidentified screws fitted v0.5. v0.7 removes v0.6 LED interference and retains original mounting centres. Revised seating and removal durability need a physical trial.',
    'Simplified PCB/connector envelopes omit some small components and manufacturing tolerances.',
    'Cable curves are illustrative; trial lead lengths include unmodelled slack.',
    'Threads intentionally engage printed pilot walls; fasteners are not a collision-free fit claim.',
    'Physical button access, screwdriver access, battery fit and sensor thermal performance require a pilot.']
(CAD/'generated/validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'PASS: 3 printed pieces; {len(checks)} mesh intersections below 0.001 mm³; {report["references"]} references verified.')
