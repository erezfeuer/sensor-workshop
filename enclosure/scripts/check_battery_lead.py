#!/usr/bin/env python3
"""Check the open lead notch, free release, thicker wires and header clearance.

Nominal geometry only; flexible-wire handling and print fit need a real trial.
"""
import hashlib
import io
import json
import subprocess
import warnings
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
from render_review import ROOT, CAD, PARAMS as p
from cable_routes import routes, smooth, tube

warnings.filterwarnings('ignore',category=RuntimeWarning,module='trimesh.triangles')
scene=CAD/'generated/scene'
meshes={n:trimesh.load_mesh(scene/(n+'.stl')) for n in
        ('shell','carrier','feather_frame','feather','light','rtc','battery')}
frame=meshes['feather_frame']

def box(size,center):
    m=trimesh.creation.box(size);m.apply_translation(center);return m

def overlap(a,b):
    if np.any(a.bounds[1]<b.bounds[0]) or np.any(b.bounds[1]<a.bounds[0]):return 0.
    m=trimesh.boolean.intersection([a,b],engine='manifold')
    return abs(float(m.volume)) if len(m.faces) else 0.

old_data=subprocess.check_output(['git','show','48812bc:enclosure/stl/feather_frame.stl'],cwd=ROOT)
old=trimesh.load_mesh(io.BytesIO(old_data),file_type='stl')
old.apply_transform(np.array([[1,0,0,0],[0,0,-1,16.5],[0,1,0,0],[0,0,0,1.]]))
added=trimesh.boolean.difference([frame,old],engine='manifold')
x0,x1=p['feather_cable_notch_x'];y0,y1=p['feather_cable_bridge_y']
cover_top=p['carrier_z']+p['carrier_thickness']
assert abs(p['feather_cable_notch_top']-cover_top-4.1)<1e-6
assert abs(x1-x0-13)<1e-6
assert frame.is_volume and len(frame.split())==1

# A 5.2 x 2.4 mm two-wire envelope drops freely out of the open notch.
# Lateral positions demonstrate useful space, not just one precise route.
release_checks=0
for x in np.linspace(15,20,11):
    for z in np.linspace(29,23,25):
        gauge=box([5.2,5,2.4],[x,(y0+y1)/2,z])
        assert overlap(gauge,frame)<.001,('Cable cannot lift out',x,z)
        release_checks+=1
# The actual previous crossbar blocked this route: this is a regression check.
assert overlap(box([5.2,5,2.4],[17.5,14.5,27.6]),old)>1
# The raised bridge is substantial material, joining both ends of the notch.
for x in np.linspace(x0-1,x1+1,31):
    gauge=box([.2,3.8,2.8],[x,14.5,p['feather_cable_notch_top']+1.5])
    assert abs(overlap(gauge,frame)-gauge.volume)<.001,('Missing bridge',x)

# Reserve a full 2.54 mm square per header position, extending 12 mm behind
# the PCB. Derive pad centres independently from the actual vendor Eagle file.
board=ET.parse(ROOT/'hardware/reference/vendor/feather/board.brd').find('./drawing/board')
headers=[]
for name in ('JP1','JP3'):
    elem=next(e for e in board.findall('./elements/element') if e.get('name')==name)
    lib=next(l for l in board.findall('./libraries/library') if l.get('name')==elem.get('library'))
    pkg=next(k for k in lib.findall('packages/package') if k.get('name')==elem.get('package'))
    angle=np.deg2rad(float(elem.get('rot','R0')[1:]))
    r=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    for pad in pkg.findall('pad'):
        xy=r@np.array([float(pad.get('x')),float(pad.get('y'))])+[float(elem.get('x')),float(elem.get('y'))]
        x=p['feather_origin'][0]+xy[0];z=p['feather_origin'][2]-xy[1]
        gauge=box([2.54,12,2.54],[x,p['feather_origin'][1]+p['pcb_thickness']+6,z])
        assert overlap(gauge,added)<.001,('New bridge blocks header',name,pad.get('name'))
        headers.append([name,pad.get('name'),round(x,4),round(z,4)])
assert len(headers)==28
# Measure the exported bridge away from unchanged upright/post triangulations.
bridge=trimesh.boolean.intersection([frame,box([x1-x0-4,y1-y0,20],[(x0+x1)/2,(y0+y1)/2,30])],engine='manifold')
header_gap=min(row[3] for row in headers)-1.27-bridge.bounds[1,2]
assert header_gap>.63

# Check two 2.4 mm OD wires (the viewer shows 2 mm OD), including all vendor
# Feather solids. The ends follow the current illustrative routing.
obstacles={n:m for n,m in meshes.items() if n!='carrier'}
t=np.array([[1,0,0,6],[0,0,1,4.3],[0,-1,0,57],[0,0,0,1.]])
for file in sorted((scene/'feather-vendor').glob('*.stl')):
    m=trimesh.load_mesh(file);m.apply_transform(t);obstacles['vendor-'+file.stem]=m
assert len(obstacles)==192
route=next(r for r in routes() if r['id']=='battery_lead');path=smooth(route['points'])
blend=np.linspace(0,1,len(path))[:,None]
wires=[tube(path+off*((1-blend)*[0,1,0]+blend*[1,0,0]),1.2,16) for off in (-1.3,1.3)]
for wire in wires:
    for name,obstacle in obstacles.items():
        assert overlap(wire,obstacle)<.001,('Battery wire',name)
for dz in np.linspace(-40,0,81):
    plate=meshes['carrier'].copy();plate.apply_translation([0,0,dz])
    for wire in wires:assert overlap(wire,plate)<.001,('Carrier closes on wire',dz)

unchanged={}
for rel in ['production-stls/01-shell.stl','production-stls/02-sensor-carrier.stl',
            'prototype-stls/bare-scd30/01-shell.stl','prototype-stls/bare-scd30/02-sensor-carrier-bare-scd30.stl']:
    before=subprocess.check_output(['git','show','48812bc:'+rel],cwd=ROOT)
    now=(ROOT/rel).read_bytes();assert before==now,('Unexpected additional reprint',rel)
    unchanged[rel]=hashlib.sha256(now).hexdigest()
report=dict(status='passed',version=p['enclosure_version'],
    frame_sha256=hashlib.sha256((ROOT/'production-stls/03-feather-frame.stl').read_bytes()).hexdigest(),
    notch_width_mm=x1-x0,notch_clear_height_above_cover_mm=round(p['feather_cable_notch_top']-cover_top,3),
    bridge_height_depth_mm=[p['feather_cable_bridge_height'],y1-y0],upper_fillet_radius_mm=p['feather_cable_notch_radius'],
    open_toward_carrier=True,free_wire_release_checks=release_checks,release_gauge_xz_mm=[5.2,2.4],
    release_center_x_range_mm=[15,20],old_crossbar_blocked_release=True,
    header_keepouts={'count':len(headers),'square_width_mm':2.54,'depth_behind_pcb_mm':12,
        'new_material_only':True,'minimum_vertical_gap_mm':round(float(header_gap),3),'pads':headers},
    illustrated_wire_od_mm=2,checked_wire_od_mm=2.4,checked_wire_center_spacing_mm=2.6,
    wire_obstacle_checks=2*len(obstacles),carrier_closure_poses=81,
    unchanged_prints_from_48812bc=unchanged,
    limitations=['Nominal sampled geometry, not a simulation of flexible wires, handling or print tolerances.',
                 'The new brace clears header-column envelopes; this does not qualify every possible header or attached accessory.',
                 'The notch is deliberately open. Lay the lead in it with relaxed slack before closing.'])
(CAD/'generated/battery-lead-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'PASS: open 13 x 4.1 mm notch; {release_checks} free-release checks; 28 header reserves; 2.4 mm OD wires clear closing carrier.')
