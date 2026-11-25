#!/usr/bin/env python3
"""Audit every installed mounting feature directly in the released print STLs.

Source coordinates are read independently from the pinned vendor Eagle files.
Depths come from axial intersections with STL triangles, not nominal SCAD depths.
"""
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import warnings
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
CAD=ROOT/'enclosure'
CACHE=CAD/'generated/scene/mounting-vendor'
if '--prepare' in sys.argv:
    sys.path.insert(0,str(Path(sys.executable).resolve().parent.parent/'lib'))
    import FreeCAD,Part,MeshPart
    manifest=json.loads((ROOT/'hardware/reference/manifest.json').read_text())
    for key in ('rtc','scd30'):
        ref=next(r for r in manifest if r['path']==f'vendor/{key}/model.step')
        path=ROOT/'hardware/reference'/ref['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==ref['sha256']
        model=Part.read(str(path));folder=CACHE/key;folder.mkdir(parents=True,exist_ok=True);bounds=[]
        for i,b in enumerate(model.Solids):
            mesh=MeshPart.meshFromShape(Shape=b,LinearDeflection=.08,AngularDeflection=.3,Relative=False)
            mesh.write(str(folder/f'{i:03}.stl'))
            bb=b.BoundBox;bounds.append([[bb.XMin,bb.YMin,bb.ZMin],[bb.XMax,bb.YMax,bb.ZMax]])
        (folder/'source.json').write_text(json.dumps({'sha256':ref['sha256'],'solids':len(model.Solids),'exact_bounds':bounds},indent=2)+'\n')
    sys.exit(0)

import numpy as np
import trimesh
P={}
for line in (CAD/'parameters.scad').read_text().splitlines():
    m=re.match(r'(\w+)\s*=\s*(.*?);',line)
    if m:P[m[1]]=json.loads(m[2])
warnings.filterwarnings('ignore',category=RuntimeWarning,module='trimesh.triangles')
manifest=json.loads((ROOT/'hardware/reference/manifest.json').read_text())

def manufacturer_holes(key):
    ref=next(r for r in manifest if r['path']==f'vendor/{key}/board.brd')
    path=ROOT/'hardware/reference'/ref['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==ref['sha256']
    b=ET.parse(path).find('./drawing/board')
    holes=[[float(h.get(k)) for k in ('x','y','drill')] for h in b.findall('./plain/hole') if float(h.get('drill'))>=2]
    for e in b.findall('./elements/element'):
        if 'MOUNTINGHOLE' not in e.get('package'):continue
        library=next(n for n in b.findall('./libraries/library') if n.get('name')==e.get('library'))
        pkg=next(n for n in library.findall('./packages/package') if n.get('name')==e.get('package'))
        for pad in pkg.findall('pad'):
            # All selected mounting pads are centred in their packages. Verify
            # this explicitly, rather than reusing the geometry extractor.
            assert abs(float(pad.get('x')))+abs(float(pad.get('y')))<1e-8
            holes.append([float(e.get('x')),float(e.get('y')),float(pad.get('drill'))])
    return sorted(holes),ref['sha256']

paths={'shell':ROOT/'production-stls/01-shell.stl',
    'carrier':ROOT/'production-stls/02-sensor-carrier.stl',
    'feather_frame':ROOT/'production-stls/03-feather-frame.stl',
    'personal_carrier':ROOT/'prototype-stls/bare-scd30/02-sensor-carrier-bare-scd30.stl'}
meshes={}
for name,path in paths.items():
    m=trimesh.load_mesh(path);assert m.is_volume and len(m.split())==1,name
    # Inverse of the released print orientations, into assembly coordinates.
    if name=='feather_frame':t=np.array([[1,0,0,0],[0,0,-1,16.5],[0,1,0,0],[0,0,0,1.]])
    else:
        t=np.diag([1.,-1.,-1.,1.]);t[:3,3]=[0,P['case_depth'],P['case_top']+P['roof_thickness'] if name=='shell' else P['carrier_z']+P['carrier_thickness']]
    m.apply_transform(t);meshes[name]=m
for name in ('01-shell.stl','03-feather-frame.stl'):
    assert (ROOT/'production-stls'/name).read_bytes()==(ROOT/'prototype-stls/bare-scd30'/name).read_bytes()

report={'status':'passed','version':P['enclosure_version'],'units':'mm',
    'print_sha256':{k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in paths.items()},
    'references':{},'features':[],'screw_access':[],
    'limitations':['Nominal STL dimensions; printer shrinkage, bore undersizing and the actual screw thread still require physical fitting.',
        'Screw heads use the existing nominal pan-head envelopes; actual purchased heads must fit within these envelopes.',
        'No cutting, drilling, slicing or modification of the released print geometry was performed by this audit.']}

def overlap(a,b):
    if np.any(a.bounds[1]<b.bounds[0]) or np.any(b.bounds[1]<a.bounds[0]):return 0.
    v=trimesh.boolean.intersection([a,b],engine='manifold')
    return abs(float(v.volume)) if len(v.faces) else 0.

def cylinder(xy,z0,z1,radius):
    m=trimesh.creation.cylinder(radius=radius,height=z1-z0,sections=48)
    m.apply_translation([*xy,(z0+z1)/2]);return m

def local_support(name):
    m=meshes[name].copy();t=np.eye(4)
    if name=='feather_frame':t[:3,:3]=[[1,0,0],[0,0,-1],[0,1,0]]
    m.apply_transform(t);return m,t

def measured_circle(mesh,xy,z,diameter):
    section=mesh.section(plane_normal=[0,0,1],plane_origin=[0,0,z]);candidates=[]
    assert section is not None,(xy,z)
    for poly in section.discrete:
        lo,hi=poly[:,:2].min(0),poly[:,:2].max(0)
        center=(lo+hi)/2
        if np.linalg.norm(center-xy)<.1 and np.max(np.abs(hi-lo-diameter))<.1:
            candidates.append((center,hi-lo))
    assert len(candidates)==1,('Missing or ambiguous bore/pin',xy,z,diameter,candidates)
    center,size=candidates[0]
    assert np.max(np.abs(center-xy))<.005,('Centre offset',xy,center)
    assert np.max(np.abs(size-diameter))<.005,('Wrong diameter',diameter,size)
    return {'center_xy':center.round(5).tolist(),'diameter_xy':size.round(5).tolist()}

def axial_surfaces(mesh,xy):
    # Intersect an axial line with all triangle faces, using XY barycentrics.
    tri=mesh.triangles;a=tri[:,1]-tri[:,0];b=tri[:,2]-tri[:,0];q=np.asarray(xy)-tri[:,0,:2]
    den=a[:,0]*b[:,1]-a[:,1]*b[:,0];valid=np.abs(den)>1e-10
    den=np.where(valid,den,1.)
    u=(q[:,0]*b[:,1]-q[:,1]*b[:,0])/den
    v=(a[:,0]*q[:,1]-a[:,1]*q[:,0])/den
    inside=valid&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)
    z=tri[:,0,2]+u*a[:,2]+v*b[:,2]
    return np.unique(np.round(z[inside],6))

def audit_pilot(label,name,support,diameter,screw_length,stack,board_hole=None):
    m,t=local_support(name);point=(t@np.r_[support,1])[:3];xy=point[:2];entry=point[2]
    hits=axial_surfaces(m,xy);ahead=hits[hits>entry+.01]
    assert len(ahead)>=2,(label,'No closed bore end',hits)
    depth=float(ahead[0]-entry);back=float(ahead[1]-ahead[0]);engagement=screw_length-stack
    assert depth-engagement>=.5,(label,'Screw bottoms out',depth,engagement)
    assert back>=1.0,(label,'Insufficient material behind bore',back)
    circles=[measured_circle(m,xy,z,diameter) for z in [entry+.15,entry+engagement/2,entry+depth-.1]]
    probe=cylinder(xy,entry+.01,entry+depth-.02,diameter/2-.02)
    assert overlap(probe,m)<.001,(label,'Blocked bore')
    cap=cylinder(xy,entry+depth+.02,entry+depth+.12,diameter/2-.05)
    assert abs(overlap(cap,m)-cap.volume)<.001,(label,'Bore cap incomplete')
    if board_hole is not None:assert board_hole>2.,(label,'M2 shaft blocked by PCB')
    row={'id':label,'part':name,'type':'screw pilot','assembly_center':list(support),
        'diameter_mm':diameter,'pcb_hole_mm':board_hole,'screw_under_head_mm':screw_length,
        'stack_mm':stack,'engagement_mm':round(engagement,3),'measured_depth_mm':round(depth,3),
        'tip_clearance_mm':round(depth-engagement,3),'solid_back_mm':round(back,3),'sections':circles}
    if diameter==P['m2_pilot']:row['conditional_5_5mm_under_head_tip_clearance_mm']=round(depth-(5.5-stack),3)
    report['features'].append(row);return row

def audit_pin(label,name,support,board_hole):
    m,t=local_support(name);point=(t@np.r_[support,1])[:3];xy=point[:2];entry=point[2]
    hits=axial_surfaces(m,xy);below=hits[hits<entry-.01]
    assert len(below)>=1,(label,hits)
    height=entry-float(below[-1]);assert abs(height-P['locating_height'])<.005,(label,height)
    circle=measured_circle(m,xy,entry-.5,P['locating_pin'])
    assert board_hole-P['locating_pin']>=.299,(label,'Pin too wide')
    assert P['pcb_thickness']-height>.3,(label,'Pin protrudes past PCB')
    # A solid base connection, not just a nominal locating-cylinder outline.
    core=cylinder(xy,entry-.7,entry+.2,.5)
    assert abs(overlap(core,m)-core.volume)<.001,(label,'Pin disconnected at root')
    report['features'].append({'id':label,'part':name,'type':'locating pin','assembly_center':list(support),
        'diameter_mm':P['locating_pin'],'pcb_hole_mm':board_hole,'height_mm':round(height,3),
        'diametral_clearance_mm':round(board_hole-P['locating_pin'],3),'section':circle})

boards={}
for key in ['feather',P['light_sensor'],'rtc','scd30','veml7700']:
    boards[key],report['references'][key]=manufacturer_holes(key)
assert boards[P['light_sensor']]==boards['veml7700']
report['veml7700_same_hole_pattern']=True
scene={key:trimesh.load_mesh(CAD/'generated/scene'/f'{key}.stl') for key in ['feather','light','rtc','scd30','battery']}
screw_rows=[]
for key,source,name in [('feather','feather','feather_frame'),('light',P['light_sensor'],'shell'),('rtc','rtc','shell'),('scd30','scd30','carrier')]:
    origin=np.array(P[key+'_origin']);normal=np.array([0.,1.,0.]) if key=='feather' else np.array([0.,0.,1.])
    for i,(x,y,d) in enumerate(boards[source]):
        if key=='feather':front=origin+[x,0,-y]
        elif key=='rtc':front=origin+[-y,x,0]
        elif key=='scd30':front=origin+[x,-y,-P['pcb_thickness']]
        else:front=origin+[x,y,0]
        support=front+normal*P['pcb_thickness'];label=f'{key}-{i+1}'
        if key=='rtc' or i in (0,3):
            washer=.5 if key=='rtc' else 0.
            audit_pilot(label,name,support,P['m2_pilot'],5,P['pcb_thickness']+washer,d)
            bearing=front-normal*washer
            screw_rows.append((label,name,key,bearing,normal,2.,5.,washer))
        else:audit_pin(label,name,support,d)

for i,xy in enumerate(P['case_mounts'],1):
    support=[*xy,P['carrier_z']+P['carrier_thickness']]
    audit_pilot(f'case-{i}','shell',support,P['m3_pilot'],8,P['carrier_thickness'])
    for name in ('carrier','personal_carrier'):
        mesh=meshes[name]
        sections=[measured_circle(mesh,xy,z,3.4) for z in [P['carrier_z']+.1,P['carrier_z']+P['carrier_thickness']-.1]]
        probe=cylinder(xy,P['carrier_z']-.1,P['carrier_z']+P['carrier_thickness']+.1,1.68)
        assert overlap(mesh,probe)<.001,(name,i,'Closure passage blocked')
        report['features'].append({'id':f'{name}-closure-{i}','part':name,'type':'through hole',
            'assembly_center':[*xy,P['carrier_z']],'diameter_mm':3.4,'sections':sections,
            'coaxial_with_shell_pilot':True,'M3_diametral_clearance_mm':.4})
    screw_rows.append((f'case-{i}','shell','case',np.array([*xy,P['carrier_z']]),np.array([0.,0.,1.]),3.,8.,0.))

# Check pan-head and straight screwdriver clearances at the intended assembly stage.
for label,name,key,bearing,normal,d,length,washer in screw_rows:
    transform=trimesh.geometry.align_vectors([0,0,1],normal)
    head=trimesh.creation.cylinder(radius=d,height=d*.7,sections=48)
    head.apply_translation([0,0,-d*.35-.01]);head.apply_transform(transform);head.apply_translation(bearing)
    tool=trimesh.creation.cylinder(radius=1.5 if d==2 else 2.,height=100,sections=32)
    tool.apply_translation([0,0,-50-.05]);tool.apply_transform(transform);tool.apply_translation(bearing)
    if key=='feather':obstacles={'frame':meshes[name],'PCB':scene[key]}
    elif key=='scd30':obstacles={'carrier':meshes[name],'PCB':scene[key]}
    elif key=='case':obstacles={**meshes,**scene}
    else:obstacles={'shell':meshes['shell'],'frame':meshes['feather_frame'],**{k:v for k,v in scene.items() if k not in ('battery','scd30')}}
    for obstacle,mesh in obstacles.items():
        assert overlap(head,mesh)<.001,(label,'Head collision',obstacle)
        assert overlap(tool,mesh)<.001,(label,'Driver collision',obstacle)
    if key=='rtc':
        w=trimesh.creation.annulus(r_min=1.1,r_max=2.5,height=.5,sections=48)
        w.apply_translation(bearing+normal*.25)
        for obstacle,mesh in obstacles.items():assert overlap(w,mesh)<.001,(label,'Washer collision',obstacle)
    report['screw_access'].append({'id':label,'head_diameter_mm':2*d,'head_height_mm':round(.7*d,3),
        'shaft_diameter_mm':3 if d==2 else 4,'clear':True,
        'stage':'Outside case' if key in ('feather','scd30') else 'Battery and carrier absent' if key!='case' else 'Assembled closure'})
# Detailed mechanical references catch omitted components around mounting pads.
# TSL2591 has PCB-derived component envelopes rather than a cached vendor STEP.
needs_prepare=False
for key in ('rtc','scd30'):
    ref=next(r for r in manifest if r['path']==f'vendor/{key}/model.step')
    meta=CACHE/key/'source.json'
    if not meta.exists() or json.loads(meta.read_text())['sha256']!=ref['sha256'] or 'exact_bounds' not in json.loads(meta.read_text()):needs_prepare=True
if needs_prepare:
    CACHE.mkdir(parents=True,exist_ok=True)
    with (CACHE/'prepare.log').open('w') as log:
        subprocess.run([os.environ.get('FREECAD_PYTHON','/Applications/FreeCAD.app/Contents/Resources/bin/python'),str(Path(__file__).resolve()),'--prepare'],stdout=log,stderr=subprocess.STDOUT,check=True)
report['detailed_board_clearances']=[]
feather_check=json.loads((CAD/'generated/feather-fit-checks.json').read_text())
assert feather_check['status']=='passed'
assert feather_check['current_stl_sha256']==report['print_sha256']['feather_frame']
report['detailed_board_clearances'].append({'board':'feather','solid_count':feather_check['vendor_solid_count'],
    'frame_clear':True,'existing_report':'feather-fit-checks.json','current_print_hash_matches':True})
# Preserve evidence of the newly found interference in the previously released shell.
previous_data=subprocess.check_output(['git','show','1e58663:production-stls/01-shell.stl'],cwd=ROOT)
previous_shell=trimesh.load_mesh(io.BytesIO(previous_data),file_type='stl')
old_t=np.diag([1.,-1.,-1.,1.]);old_t[:3,3]=[0,P['case_depth'],P['case_top']+P['roof_thickness']]
previous_shell.apply_transform(old_t)
report['v07_rtc_led_interferences_removed']=[]
for key in ('rtc','scd30'):
    source=json.loads((CACHE/key/'source.json').read_text());report['references'][key+'_step']=source['sha256']
    t=np.eye(4);t[:3,3]=P[key+'_origin']
    t[:3,:3]=[[0,-1,0],[1,0,0],[0,0,1]] if key=='rtc' else [[1,0,0],[0,-1,0],[0,0,-1]]
    support=meshes['shell' if key=='rtc' else 'carrier'];count=0;bounded=[]
    for path in sorted((CACHE/key).glob('*.stl')):
        part=trimesh.load_mesh(path)
        if not part.is_volume:
            # Some vendor tessellations have open seams. A complete bounding box
            # from the exact STEP is a conservative replacement for clearance.
            # Never repair holes or silently drop geometry to get a pass.
            bounds=np.asarray(source['exact_bounds'][int(path.stem)])
            part=trimesh.creation.box(bounds[1]-bounds[0]+.002)
            part.apply_translation(bounds.mean(0));bounded.append(int(path.stem))
        part.apply_transform(t)
        assert overlap(support,part)<.001,(key,path.stem,'Mounting plastic hits vendor component')
        if key=='rtc':
            old_volume=overlap(previous_shell,part)
            if old_volume>.001:report['v07_rtc_led_interferences_removed'].append({'solid':int(path.stem),'previous_intersection_mm3':round(old_volume,6),'new_intersection_mm3':0.0})
        for label,name,board,bearing,normal,d,length,washer in screw_rows:
            if board!=key:continue
            head=trimesh.creation.cylinder(radius=d,height=d*.7,sections=48)
            head.apply_translation([0,0,-d*.35-.01]);head.apply_translation(bearing)
            assert overlap(head,part)<.001,(label,path.stem,'Head hits vendor component')
            if washer:
                w=trimesh.creation.annulus(r_min=1.1,r_max=2.5,height=washer,sections=48)
                w.apply_translation(bearing+normal*washer/2)
                assert overlap(w,part)<.001,(label,path.stem,'Washer hits vendor component')
        count+=1
    assert count==source['solids']
    report['detailed_board_clearances'].append({'board':key,'solid_count':count,'mount_and_heads_clear':True,
        'exact_step_bounding_boxes_used_for_open_tessellations':bounded})
assert len(report['v07_rtc_led_interferences_removed'])==2
# The RTC relief leaves a continuous ring of material around the pilot mouth.
for row in report['features']:
    if row['id']=='rtc-1':
        ring=trimesh.creation.annulus(r_min=.92,r_max=2.05,height=.05,sections=48)
        ring.apply_translation(np.array(row['assembly_center'])+[0,0,.3])
        assert abs(overlap(ring,meshes['shell'])-ring.volume)<.001
        row['minimum_verified_mouth_wall_mm']=1.15
report['light_board_clearance']='TSL2591 uses the existing Eagle-derived pad/body envelopes with conservative component heights; no detailed STEP is cached.'
report['counts']={'board_mounting_centres':14,'case_fastening_axes':2,'screw_pilots':10,'locating_pins':6,
    'through_holes_across_both_carriers':4,'screw_head_and_driver_checks':len(screw_rows),
    'personal_variant_screws':8,'standard_variant_screws':10}
report['personal_bare_scd30']='Sensor snaps in; its factory PCB holes are not screw mounts. Both carrier closure holes are audited above.'
(CAD/'generated/mounting-hole-checks.json').write_text(json.dumps(report,indent=2)+'\n')
with (CAD/'generated/mounting-hole-checks.csv').open('w',newline='') as f:
    fields=['id','part','type','diameter_mm','pcb_hole_mm','measured_depth_mm','engagement_mm','tip_clearance_mm','solid_back_mm','height_mm','diametral_clearance_mm']
    writer=csv.DictWriter(f,fields,extrasaction='ignore');writer.writeheader();writer.writerows(report['features'])
print('PASS: 14 board centres, 10 pilots, 6 locating pins, both carriers\' closure holes, and all 10 screw-head/driver approaches.')
for row in report['features']:
    if row['type']=='screw pilot':print(row['id'],'depth',row['measured_depth_mm'],'tip clearance',row['tip_clearance_mm'])
