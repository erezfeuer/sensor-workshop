#!/usr/bin/env python3
"""Check the two-piece print set, assembled clearances and routed mesh envelopes."""
import hashlib
import itertools
import json
import warnings
import numpy as np
import trimesh
import pymupdf
from render_review import ROOT,CAD,PARAMS as p
from build_viewer import tie_mesh

warnings.filterwarnings('ignore',category=RuntimeWarning,module='trimesh.triangles')
report={'version':'0.2','status':'passed','units':'mm','print_parts':{},'clearances':{},'references':0}
assert {x.stem for x in (CAD/'stl').glob('*.stl')}=={'shell','carrier','coupon'}
for name in ['shell','carrier','coupon']:
    path=CAD/'stl'/f'{name}.stl';m=trimesh.load_mesh(path);bodies=len(m.split())
    assert m.is_watertight and m.is_winding_consistent and m.volume>0,name
    assert bodies==(8 if name=='coupon' else 1),(name,bodies)
    assert abs(m.bounds[0,2])<.002,(name,m.bounds.tolist())
    report['print_parts'][name]={'watertight':True,'bodies':bodies,'size_mm':m.extents.round(3).tolist(),
        'solid_volume_mm3':round(m.volume,2),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
report['printed_pieces_per_device']=2
report['fasteners']={'M2x5':8,'M3x8':2,'M2_washers':2,'nuts':0,'battery_ties':2}
report['footprint_reduction_percent']=round(100*(1-p['case_width']*p['case_depth']/(112*84)),2)

def gap(name,value):
    assert value>0,(name,value)
    report['clearances'][name]=round(value,3)

gap('SCD30 upward pins to carrier',p['carrier_z']-p['scd30_origin'][2]-2.935)
gap('SCD30 body to table',p['scd30_origin'][2]-8.57)
gap('SCD30 body above skirt lower edge',p['scd30_origin'][2]-8.57-p['skirt_bottom'])
gap('Light QT to roof',p['case_top']-p['light_origin'][2]-4.6)
gap('Light package to roof',p['case_top']-p['light_origin'][2]-3.95)
gap('RTC QT to roof',p['case_top']-p['rtc_origin'][2]-4.6)
gap('Feather PCB top to roof',p['case_top']-p['feather_origin'][2])
gap('TFT glass to recessed inside rim',p['feather_origin'][1]-1.9-1.65)
gap('Battery to carrier top',p['battery_center'][2]-p['battery_diameter']/2-p['carrier_z']-p['carrier_thickness'])
gap('Axial battery tolerance',76-p['battery_length'])
report['button_access_recess_mm']=round(p['feather_origin'][1]-1.9,2)
report['screw_engagement_mm']={
    'Feather M2x5':round(5-p['pcb_thickness'],2),
    'Light M2x5':round(5-p['pcb_thickness'],2),
    'RTC M2x5 with washer':round(5-p['pcb_thickness']-.5,2),
    'SCD30 M2x5':round(5-p['pcb_thickness'],2),
    'Carrier M3x8':round(8-p['carrier_thickness'],2)}
assert p['feather_origin'][1]+p['pcb_thickness']-5>.75 # stays inside the blind pilot
assert p['light_origin'][2]+5 < p['case_top']+p['roof_thickness']-1.0
assert p['scd30_origin'][2]-p['pcb_thickness']+5 < p['carrier_z']+p['carrier_thickness']-1.0

scene=CAD/'generated/scene'
meshes={n:trimesh.load_mesh(scene/(n+'.stl')) for n in ['shell','carrier','feather','light','rtc','scd30','battery']}
checks=[]
def check_pair(a,b,ma,mb):
    result=trimesh.boolean.intersection([ma,mb],engine='manifold')
    volume=abs(float(result.volume)) if len(result.faces) else 0.
    assert volume<.001,(a,b,volume,result.bounds.tolist())
    checks.append({'a':a,'b':b,'intersection_mm3':round(volume,6)})
for a,b in itertools.combinations(meshes,2):check_pair(a,b,meshes[a],meshes[b])
# All coloured wires and nominal plugs against solids, not just their centre lines.
for path in sorted(scene.glob('cable_*.stl')):
    m=trimesh.load_mesh(path)
    for name,other in meshes.items():check_pair(path.stem,name,m,other)
for i,x in enumerate(p['battery_saddles']):
    tie=tie_mesh(x)
    for name,other in meshes.items():check_pair(f'battery_tie_{i}',name,tie,other)
report['mesh_intersections']=checks
for e in json.loads((ROOT/'hardware/reference/manifest.json').read_text()):
    assert hashlib.sha256((ROOT/'hardware/reference'/e['path']).read_bytes()).hexdigest()==e['sha256']
    report['references']+=1
with pymupdf.open(CAD/'design-review.pdf') as pdf:
    assert len(pdf)==8
    report['review_pdf_pages']=len(pdf)
report['limitations']=['No real parts or printed samples tested.',
    'Simplified PCB/connector envelopes omit some small components and manufacturing tolerances.',
    'Cable curves are illustrative; trial lead lengths include unmodelled slack.',
    'Threads intentionally engage printed pilot walls; fasteners are not a collision-free fit claim.',
    'Physical button access, screwdriver access, battery fit and sensor thermal performance require a pilot.']
(CAD/'generated/validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'PASS: 2 printed pieces; {len(checks)} mesh intersections below 0.001 mm³; {report["references"]} references verified.')
