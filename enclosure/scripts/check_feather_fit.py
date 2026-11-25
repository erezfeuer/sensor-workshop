#!/usr/bin/env python3
"""Check Feather STL hole/pin centres against the fitted v0.5 print and vendor STEP.

Also check all detailed manufacturer component solids, including the two LEDs
omitted from the earlier simplified board. FreeCAD is used only to prepare the cache.
"""
import hashlib
import io
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import warnings

ROOT=Path(__file__).resolve().parents[2]
CAD=ROOT/'enclosure'
CACHE=CAD/'generated/scene/feather-vendor'
SOURCE=ROOT/'hardware/reference/vendor/feather/model.step'
MANIFEST=json.loads((ROOT/'hardware/reference/manifest.json').read_text())
REF=next(r for r in MANIFEST if r['path']=='vendor/feather/model.step')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==REF['sha256']

if '--prepare' in sys.argv:
    sys.path.insert(0,str(Path(sys.executable).resolve().parent.parent/'lib'))
    import FreeCAD,Part,MeshPart
    model=Part.read(str(SOURCE));CACHE.mkdir(parents=True,exist_ok=True)
    data={'source_sha256':REF['sha256'],'solids':[],'pcb_holes':[]}
    for i,b in enumerate(model.Solids):
        mesh=MeshPart.meshFromShape(Shape=b,LinearDeflection=.08,AngularDeflection=.3,Relative=False)
        mesh.write(str(CACHE/f'{i:03}.stl'))
        data['solids'].append({'id':i,'triangles':mesh.CountFacets})
        if i==0:
            for face in b.Faces:
                s=face.Surface
                if isinstance(s,Part.Cylinder) and abs(s.Axis.z)>.99 and 1<s.Radius<1.3:
                    data['pcb_holes'].append([s.Center.x,s.Center.y,2*s.Radius])
    (CACHE/'source.json').write_text(json.dumps(data,indent=2)+'\n')
    sys.exit(0)

import numpy as np
import trimesh
warnings.filterwarnings('ignore',category=RuntimeWarning,module='trimesh.triangles')
if not (CACHE/'source.json').exists() or json.loads((CACHE/'source.json').read_text())['source_sha256']!=REF['sha256']:
    fc=os.environ.get('FREECAD_PYTHON','/Applications/FreeCAD.app/Contents/Resources/bin/python')
    CACHE.mkdir(parents=True,exist_ok=True)
    with (CACHE/'prepare.log').open('w') as log:
        subprocess.run([fc,str(Path(__file__).resolve()),'--prepare'],stdout=log,stderr=subprocess.STDOUT,check=True)
reference=json.loads((CACHE/'source.json').read_text())

def historic(commit):
    data=subprocess.check_output(['git','show',commit+':enclosure/stl/feather_frame.stl'],cwd=ROOT)
    return trimesh.load_mesh(io.BytesIO(data),file_type='stl'),hashlib.sha256(data).hexdigest()
old,old_hash=historic('0766233')
previous,previous_hash=historic('c84ad37')
new=trimesh.load_mesh(CAD/'stl/feather_frame.stl')

def centres(mesh,z,diameter):
    section=mesh.section(plane_normal=[0,0,1],plane_origin=[0,0,z]);found=[]
    for poly in section.discrete:
        lo,hi=poly.min(0),poly.max(0)
        if np.allclose((hi-lo)[:2],diameter,atol=.002):found.append(((lo+hi)/2)[:2])
    return np.array(sorted(found,key=lambda x:x[0]))

version=json.loads(re.search(r'enclosure_version\s*=\s*(.*?);',(CAD/'parameters.scad').read_text()).group(1))
report={'status':'passed','version':version,'source_sha256':REF['sha256'],
    'fitted_v05_stl_sha256':old_hash,'rejected_v06_stl_sha256':previous_hash,
    'current_stl_sha256':hashlib.sha256((CAD/'stl/feather_frame.stl').read_bytes()).hexdigest(),
    'axes':'print XY = assembly XZ','locations':{},'component_checks':[],
    'limitations':['Nominal manufacturer geometry and STL checks, not print distortion, seating force or screw-torque qualification.',
        'Clearance tests use tessellated STEP solids at 0.08 mm linear deflection.']}
for kind,z,d in [('screw_pilots',10.3,1.8),('locating_pins',10.8,1.9)]:
    a=centres(old,z,d);b=centres(previous,z,d);c=centres(new,z,d)
    assert len(a)==len(b)==len(c)==2,(kind,a,b,c)
    assert np.allclose(a,b,atol=.001) and np.allclose(a,c,atol=.001),(kind,a,b,c)
    report['locations'][kind]={'xy_mm':c.round(5).tolist(),'maximum_change_from_v05_mm':float(np.max(np.abs(a-c)))}
    for x,z in c:
        assert min(np.linalg.norm(np.array([6+h[0],57-h[1]])-[x,z]) for h in reference['pcb_holes'])<.0015
# Restore the old contact diameters; local component reliefs may remove material.
slab=trimesh.creation.box([100,80,.04]);slab.apply_translation([35,45,10.55])
a=trimesh.boolean.intersection([old,slab],engine='manifold')
b=trimesh.boolean.intersection([new,slab],engine='manifold')
assert .9*a.volume<b.volume<=a.volume+.001
assert abs(trimesh.boolean.intersection([a,b],engine='manifold').volume-b.volume)<.001
report['board_contact_footprints_within_v05']=True
# Preserve the complete working interface: both pins, four cylindrical lands
# and pilot mouths, through 2 mm behind the PCB. Compare actual STL solids.
band=trimesh.creation.box([100,80,3.6]);band.apply_translation([35,45,10.4001])
old_band=trimesh.boolean.intersection([old,band],engine='manifold')
new_band=trimesh.boolean.intersection([new,band],engine='manifold')
common=trimesh.boolean.intersection([old_band,new_band],engine='manifold')
assert abs(old_band.volume-new_band.volume)<.001
assert abs(common.volume-old_band.volume)<.001
report['complete_front_interface_matches_v05']={'depth_behind_pcb_mm':2,
    'includes':['both original locating pins','all four original contact lands','both screw pilot mouths'],
    'symmetric_difference_mm3':round(old_band.volume+new_band.volume-2*common.volume,7)}
# Invert print transform and apply manufacturer-board transform independently.
t=np.array([[1,0,0,0],[0,0,-1,16.5],[0,1,0,0],[0,0,0,1.]])
frames={key:mesh.copy() for key,mesh in [('v05',old),('v06',previous),('current',new)]}
for frame in frames.values():frame.apply_transform(t)
vendor_transform=np.array([[1,0,0,6],[0,0,1,4.3],[0,-1,0,57],[0,0,0,1.]])
regressions=[]
for p in sorted(CACHE.glob('*.stl')):
    mesh=trimesh.load_mesh(p);assert mesh.is_volume,p
    mesh.apply_transform(vendor_transform)
    volumes={}
    for key,frame in frames.items():
        v=0.
        if not (np.any(mesh.bounds[1]<frame.bounds[0]) or np.any(frame.bounds[1]<mesh.bounds[0])):
            result=trimesh.boolean.intersection([mesh,frame],engine='manifold');v=abs(float(result.volume))
        volumes[key]=round(v,7)
    assert volumes['current']<.0001,('Detailed board component collision',p.stem,volumes)
    if volumes['v06']>=.0001:regressions.append({'vendor_solid':int(p.stem),'intersection_mm3':volumes})
    report['component_checks'].append({'vendor_solid':int(p.stem),'new_intersection_mm3':volumes['current']})
assert len(regressions)==6,regressions
assert all(r['intersection_mm3']['v05']<.0001 for r in regressions)
report['v06_led_interferences_removed']=regressions
report['vendor_solid_count']=len(reference['solids'])
(CAD/'generated/feather-fit-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: old hole/pin centres; contact footprints within v0.5; all',len(reference['solids']),'vendor solids clear; six v0.6 LED overlaps removed.')
