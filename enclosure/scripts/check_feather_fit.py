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
v08,v08_hash=historic('96883e0')
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
# Enlarging the screw collars must not move the seat plane or alter either pin.
# The old test froze the entire first 2 mm, unintentionally preserving the weak
# 3.2 mm stem. Preserve fitted datums, then independently require real material.
band=trimesh.creation.box([100,80,1.6]);band.apply_translation([35,45,11.4001])
old_band=trimesh.boolean.intersection([old,band],engine='manifold')
new_band=trimesh.boolean.intersection([new,band],engine='manifold')
common=trimesh.boolean.intersection([old_band,new_band],engine='manifold')
assert abs(old_band.volume-new_band.volume)<.001
assert abs(common.volume-old_band.volume)<.001
report['pins_and_board_seat_plane_unchanged']=True
removed=trimesh.boolean.difference([v08,new],engine='manifold')
assert abs(removed.volume)<.001,'Existing support was removed'
added=trimesh.boolean.difference([new,v08],engine='manifold')
report['v08_material_preserved']={'source_sha256':v08_hash,'removed_mm3':round(abs(removed.volume),7),
    'added_mm3':round(float(added.volume),4)}
report['screw_collar_sections']=[]
for index,xy in [(0,[8.54,54.46]),(3,[54.26,36.045])]:
    areas=[];before=[]
    for depth in np.linspace(.1,1.9,19):
        gauge=trimesh.creation.cylinder(radius=2.6,height=.04,sections=96)
        gauge.apply_translation([*xy,10.6-depth])
        area=abs(trimesh.boolean.intersection([new,gauge],engine='manifold').volume)/.04
        old_area=abs(trimesh.boolean.intersection([v08,gauge],engine='manifold').volume)/.04
        assert area>=15.5,('Thin screw collar',index,depth,area)
        assert area/old_area>=(1.5 if index==0 else 2.8),(index,depth,area,old_area)
        areas.append(area);before.append(old_area)
    assert min(before)<15.5,'This regression check must reject the v0.8 necks'
    report['screw_collar_sections'].append({'hole_index':index,'sample_count':len(areas),
        'depth_range_from_pcb_back_mm':[.1,1.9],'measurement_radius_mm':2.6,
        'minimum_required_plastic_section_mm2':15.5,
        'minimum_plastic_section_mm2':round(min(areas),3),
        'v08_minimum_plastic_section_mm2':round(min(before),3),
        'minimum_area_ratio':round(min(a/b for a,b in zip(areas,before)),3)})
# Invert print transform and apply manufacturer-board transform independently.
t=np.array([[1,0,0,0],[0,0,-1,16.5],[0,1,0,0],[0,0,0,1.]])
frames={key:mesh.copy() for key,mesh in [('v05',old),('v06',previous),('current',new)]}
for frame in frames.values():frame.apply_transform(t)
vendor_transform=np.array([[1,0,0,6],[0,0,1,4.3],[0,-1,0,57],[0,0,0,1.]])
added.apply_transform(t)
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
    if int(p.stem)!=0:
        # Check new material against conservative component boxes with 0.15 mm
        # clearance, independently of the two relief shapes used by the CAD.
        envelope=trimesh.creation.box(mesh.extents+.3)
        envelope.apply_translation(mesh.bounds.mean(0))
        clearance_overlap=abs(trimesh.boolean.intersection([added,envelope],engine='manifold').volume)
        assert clearance_overlap<.001,('New collar too close to component',p.stem,clearance_overlap)
    if volumes['v06']>=.0001:regressions.append({'vendor_solid':int(p.stem),'intersection_mm3':volumes})
    report['component_checks'].append({'vendor_solid':int(p.stem),'new_intersection_mm3':volumes['current']})
assert len(regressions)==6,regressions
assert all(r['intersection_mm3']['v05']<.0001 for r in regressions)
report['v06_led_interferences_removed']=regressions
report['vendor_solid_count']=len(reference['solids'])
report['new_collar_component_box_clearance_mm']=.15
(CAD/'generated/feather-fit-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: original hole/pin centres and seat plane; both front collars reinforced; v0.8 material retained;',len(reference['solids']),'vendor solids clear.')
