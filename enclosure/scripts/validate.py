#!/usr/bin/env python3
"""Validate exported print solids, reference integrity and nominal clearances."""
import hashlib
import json
from pathlib import Path
import trimesh
import pymupdf
from render_review import ROOT, CAD, PARAMS as p

report={'status':'passed','units':'mm','print_parts':{},'clearances':{},'references':0}
for name in ['base','lid','pod','shade','foot_front','foot_rear','button','coupon']:
    path=CAD/'stl'/f'{name}.stl'
    m=trimesh.load_mesh(path)
    bodies=len(m.split())
    assert m.is_watertight and m.is_winding_consistent and m.volume>0,name
    assert bodies==(8 if name=='coupon' else 1),(name,bodies)
    assert abs(m.bounds[0,2])<.002,(name,m.bounds.tolist())
    report['print_parts'][name]={'watertight':True,'bodies':bodies,'size_mm':m.extents.round(3).tolist(),
                                'solid_volume_mm3':round(m.volume,2),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def gap(name,value,minimum=0):
    assert value>minimum,(name,value,minimum)
    report['clearances'][name]={'nominal_mm':round(value,3),'required_greater_than_mm':minimum}

gap('SCD30 underside pins to tray floor',p['scd30_origin'][2]-2.935-p['pod_origin'][2]-p['pod_floor'])
gap('SCD30 top to shade roof',p['pod_roof_z']-p['scd30_origin'][2]-8.57)
gap('Shade roof to main housing air gap',p['base_z']-p['pod_roof_z']-p['pod_roof_thickness'])
gap('RTC underside holder to main floor',p['rtc_origin'][2]-3.2-p['base_z']-p['floor_thickness'])
gap('Light board QT sockets to lid',p['case_top']-p['light_origin'][2]-p['pcb_thickness']-3)
gap('Light sensor top to lid underside',p['case_top']-p['light_origin'][2]-p['pcb_thickness']-2.35)
gap('Light board underside to battery top',p['light_origin'][2]-p['battery_center'][2]-p['battery_diameter']/2)
gap('Button plunger free gap',p['feather_origin'][1]-1.9-p['button_stem_end'])
gap('Main pack length to end stops',76-p['battery_length'])
gap('Switch provisional body to retention plate',17.5-p['switch_origin'][0]-p['switch_envelope'][0])

for name,bearing,length,nut_bottom,nut_top,blind_bottom in [
    ('M3 x 50 case bolts',78.4,50,31.4,33.8,22),
    ('M3 x 25 tray bolts',36.4,25,12,14.4,10)]:
    tip=bearing-length
    assert tip<nut_bottom<nut_top<bearing and tip>blind_bottom,name
    report.setdefault('fastener_stacks',{})[name]={'tip_z_mm':round(tip,2),'nut_z_mm':[nut_bottom,nut_top],'fully_traverses_nut':True}

for entry in json.loads((ROOT/'hardware/reference/manifest.json').read_text()):
    path=ROOT/'hardware/reference'/entry['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'],str(path)
    report['references']+=1
with pymupdf.open(CAD/'design-review.pdf') as doc:
    assert len(doc)==7
    report['review_pdf_pages']=len(doc)
report['limitations']=['No physical parts or printed samples tested.',
    'Simplified board envelopes do not represent every SMD component or cable plug.',
    'STL checks do not prove printer tolerances, assembly accessibility or sensor accuracy.',
    'Local battery, inline switch body, cable slack and button stroke require physical checks.',
    'Vendor component STLs contain open surfaces and are unsuitable as a watertight collision proof.']
(CAD/'generated/validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
