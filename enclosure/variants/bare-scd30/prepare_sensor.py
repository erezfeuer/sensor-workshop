#!/usr/bin/env python3
"""Run with FreeCAD's Python: tessellate official STEP and check snap contact zones."""
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import zipfile

# FreeCAD's bundled Python on macOS; ordinary FreeCAD Python setups also work.
sys.path.insert(0,str(Path(sys.executable).resolve().parent.parent/'lib'))
import FreeCAD as App
import Part
import MeshPart

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CACHE=ROOT/'hardware/reference/vendor/scd30-bare'
OUT=HERE/'generated/scene'
P={}
for path in (HERE.parents[1]/'parameters.scad',HERE/'parameters.scad'):
    for line in path.read_text().splitlines():
        m=re.match(r'(\w+)\s*=\s*(.*?);',line)
        if m:P[m[1]]=json.loads(m[2])
ref=next(r for r in json.loads((HERE/'references.json').read_text()) if 'step_member' in r)
archive=ROOT/ref['path']
assert hashlib.sha256(archive.read_bytes()).hexdigest()==ref['sha256']
with zipfile.ZipFile(archive) as z:data=z.read(ref['step_member'])
assert hashlib.sha256(data).hexdigest()==ref['step_sha256']
(CACHE/'model.step').write_bytes(data)
model=Part.read(str(CACHE/'model.step'))
assert len(model.Solids)==25
# Proper rotation, not reflection. PCB back Z=0, front Z=1.6, outline 35 x 23.
m=App.Matrix()
m.A11=1;m.A12=0;m.A13=0;m.A14=16.05
m.A21=0;m.A22=0;m.A23=-1;m.A24=8.3
m.A31=0;m.A32=1;m.A33=0;m.A34=-1.55
solids=[]
for solid in model.Solids:
    b=solid.copy();b.transformShape(m);solids.append(b)
OUT.mkdir(parents=True,exist_ok=True)
mesh_folder=OUT/'sensor-parts';mesh_folder.mkdir(exist_ok=True)
info=[]
for i,b in enumerate(solids):
    mesh=MeshPart.meshFromShape(Shape=b,LinearDeflection=.12,AngularDeflection=.55,Relative=False)
    mesh.write(str(mesh_folder/f'part-{i:02}.stl'))
    info.append({'part':i,'triangles':mesh.CountFacets,'volume_mm3':round(b.Volume,6)})

def prism(points):
    w=P['snap_width']
    poly=[App.Vector(-w/2,y,z) for y,z in points]
    return Part.Face(Part.makePolygon(poly+[poly[0]])).extrude(App.Vector(w,0,0))

g=P['snap_side_gap'];t=P['snap_wall'];o=P['snap_overlap']
f=P['snap_face_gap'];h=P['bare_pcb_thickness'];r=P['bare_origin'][2]-P['carrier_z']
leaf=prism([(g,r-.02),(g+t+.7,r-.02),(g+t+.7,r+.3),(g+t,r+1.3),
    (g+t,P['snap_tip_z']),(g,P['snap_tip_z']),(-o,2.05),(-o,h+f),(g,h+f)])
pad=prism([(g,r-.02),(g+t,r-.02),(g+t,-f),(-.55,-f),(-.55,-.65),(g,-1.45)])
snap=leaf.fuse(pad)
clips=[]
for x,y,angle in P['snap_locations']:
    c=snap.copy();c.rotate(App.Vector(),App.Vector(0,0,1),angle);c.translate(App.Vector(x,y,0));clips.append(c)
guide=Part.makeBox(2,3,h+f-r+.02,App.Vector(35+g,P['guide_y']-1.5,r-.02))
report={'status':'passed','source_step_sha256':ref['step_sha256'],'solid_count':25,'mesh':info,
    'normalization':{'x':'raw X + 16.05','y':'8.3 - raw Z','z':'raw Y - 1.55'},
    'clips':[],'limitations':['Exact nominal STEP geometry; received board revision and print tolerances require a fit check.',
        'Opening check translates a clip outwards; it does not simulate bending, force, strain or fatigue.']}
for i,c in enumerate(clips+[guide]):
    distances=[]
    for j,b in enumerate(solids):
        v=c.common(b).Volume
        assert v<.00001,('Solid collision',i,j,v)
        if j!=23:distances.append(c.distToShape(b)[0])
    if i==3:continue
    captures=[]
    for dz in (-.35,.35):
        pcb=solids[23].copy();pcb.translate(App.Vector(0,0,dz))
        v=c.common(pcb).Volume
        assert v>.05,('Clip does not capture PCB',i,dz,v)
        captures.append(round(v,5))
    # Check where the insertion ramp can contact the moving sensor. All contact
    # must be on the PCB solid; all optical/electronic solids must remain clear.
    for dz in (0,.4,.8,1.2,1.6,2,2.5,3,4,6,10):
        for j,b in enumerate(solids):
            if j==23:continue
            moving=b.copy();moving.translate(App.Vector(0,0,dz))
            assert c.common(moving).Volume<.00001,('Insertion hits component',i,j,dz)
    angle=math.radians(P['snap_locations'][i][2])
    opened=c.copy();opened.translate(App.Vector(-math.sin(angle)*.8,math.cos(angle)*.8,0))
    for dz in (0,.4,.8,1.2,1.6,2,2.5,3,4,6,10):
        for j,b in enumerate(solids):
            moving=b.copy();moving.translate(App.Vector(0,0,dz))
            assert opened.common(moving).Volume<.00001,('Open-clip path blocked',i,j,dz)
    report['clips'].append({'location':P['snap_locations'][i],
        'minimum_clearance_to_non_pcb_solids_mm':round(min(distances),4),
        'pcb_capture_intersections_mm3':captures,'opening_checked_mm':.8,
        'insertion_poses':11})
report['side_guide_minimum_sensor_clearance_mm']=round(min(guide.distToShape(b)[0] for b in solids),4)
(HERE/'generated/sensor-step-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: exact STEP solids, three edge snaps, body clearances and nominal opening path.')
