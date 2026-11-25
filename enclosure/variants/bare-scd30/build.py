#!/usr/bin/env python3
"""Build the personal snap carrier, three-file print set and offline viewer."""
import argparse
import base64
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import warnings
from urllib.request import Request, urlopen

HERE=Path(__file__).resolve().parent
CAD=HERE.parents[1]
ROOT=CAD.parent
sys.path.insert(0,str(CAD/'scripts'))
import numpy as np
import trimesh
from build_viewer import box
from render_review import rasterize, COLORS
import matplotlib.pyplot as plt
from matplotlib.path import Path as PlotPath
warnings.filterwarnings('ignore',category=RuntimeWarning,module='trimesh.triangles')
P={}
for path in (CAD/'parameters.scad',HERE/'parameters.scad'):
    for line in path.read_text().splitlines():
        m=re.match(r'(\w+)\s*=\s*(.*?);',line)
        if m:P[m[1]]=json.loads(m[2])
PRINT=ROOT/'prototype-stls/bare-scd30'
SCENE=HERE/'generated/scene'

def export(assembled):
    dest=SCENE/'carrier.stl' if assembled else PRINT/'02-sensor-carrier-bare-scd30.stl'
    result=subprocess.run(['openscad','--export-format','binstl','-o',str(dest),'-D',
        'assembly_coordinates='+str(assembled).lower(),str(HERE/'carrier.scad')],capture_output=True,text=True)
    log=result.stdout+result.stderr
    (SCENE/('carrier-scene.log' if assembled else 'carrier-print.log')).write_text(log)
    if result.returncode or 'WARNING:' in log or 'ERROR:' in log:raise RuntimeError(log)
    print('EXPORTED',dest.relative_to(ROOT),flush=True)

def overlap(a,b):
    if np.any(a.bounds[1]<b.bounds[0]) or np.any(b.bounds[1]<a.bounds[0]):return 0.
    m=trimesh.boolean.intersection([a,b],engine='manifold')
    return abs(float(m.volume)) if len(m.faces) else 0.

def load_scene():
    scene={p.stem:trimesh.load_mesh(p) for p in (CAD/'generated/scene').glob('*.stl')}
    scene['carrier']=trimesh.load_mesh(SCENE/'carrier.stl')
    raw=[trimesh.load_mesh(p) for p in sorted((SCENE/'sensor-parts').glob('*.stl'))]
    assert len(raw)==25
    trimesh.util.concatenate(raw).export(SCENE/'sensor-local.stl')
    matrix=np.diag([1.,-1.,-1.,1.]);matrix[:3,3]=P['bare_origin']
    for i,m in enumerate(raw):
        m.apply_transform(matrix);scene[f'scd30-part-{i:02}']=m
    scene['scd30']=trimesh.util.concatenate(raw)
    scene['scd30'].export(SCENE/'sensor.stl')
    return scene

def validate(scene):
    report={'status':'passed','variant':P['variant_version'],'units':'mm','print_parts':{},'checks':[],
        'limitations':['Nominal CAD geometry, not print-fit, insertion-force, retention, fatigue or thermal qualification.',
            'Original cable illustration retained unchanged; it does not specify the soldered lead geometry.']}
    expected={'01-shell.stl','02-sensor-carrier-bare-scd30.stl','03-feather-frame.stl'}
    assert {p.name for p in PRINT.iterdir()}==expected
    for name in sorted(expected):
        path=PRINT/name;m=trimesh.load_mesh(path)
        assert m.is_watertight and m.is_winding_consistent and m.volume>0 and len(m.split())==1,name
        assert abs(m.bounds[0,2])<.002,name
        report['print_parts'][name]={'watertight':True,'bodies':1,'size_mm':m.extents.round(3).tolist(),
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    for name in ('01-shell.stl','03-feather-frame.stl'):
        assert (PRINT/name).read_bytes()==(ROOT/'production-stls'/name).read_bytes()
    old=trimesh.load_mesh(CAD/'generated/scene/carrier.stl')
    mask=box([110,80,1.8],[46,33,25.5]);island=box([60,35,5],[46,31,25])
    mask=trimesh.boolean.difference([mask,island],engine='manifold')
    a=trimesh.boolean.intersection([old,mask],engine='manifold')
    b=trimesh.boolean.intersection([scene['carrier'],mask],engine='manifold')
    assert abs(a.volume-b.volume)<.002 and overlap(a,b)>a.volume-.002
    report['closure_interface_matches_workshop']=True
    fixed=['shell','feather_frame','feather','light','rtc','battery']
    sensor=[n for n in scene if n.startswith('scd30-part-')]
    def clear(a,b):
        v=overlap(scene[a],scene[b]);assert v<.001,(a,b,v)
        report['checks'].append({'a':a,'b':b,'intersection_mm3':round(v,6)})
    for a in ['carrier']+sensor:
        for b in fixed:clear(a,b)
    for part in sensor:clear('carrier',part)
    # Check actual carrier removal. Vendor meshes can overlap one another, so
    # their union is used solely as a collision solid, not to change the model.
    sensor_union=trimesh.boolean.union([scene[n] for n in sensor],engine='manifold')
    moving=trimesh.util.concatenate([scene['carrier'],sensor_union])
    for dz in np.linspace(-40,0,81):
        candidate=moving.copy();candidate.apply_translation([0,0,dz])
        for name in fixed:assert overlap(candidate,scene[name])<.001,('Carrier removal',dz,name)
    report['carrier_removal']={'poses':81,'checks':486,'travel_mm':40}
    report['snap_capture']={'clips':3,'pcb_mm':P['bare_pcb_thickness'],
        'capture_gap_mm':P['bare_pcb_thickness']+2*P['snap_face_gap'],
        'clip_widths_mm':P['snap_widths'],'clip_wall_mm':P['snap_wall'],
        'face_clearance_mm':P['snap_face_gap'],'side_clearance_mm':P['snap_side_gap'],
        'lip_overlap_mm':P['snap_overlap'],'additional_sensor_fasteners':0,
        'exact_step_report':'sensor-step-checks.json'}
    exact=json.loads((HERE/'generated/sensor-step-checks.json').read_text())
    assert exact['status']=='passed' and len(exact['clips'])==3
    assert exact['parameters_sha256']==hashlib.sha256((HERE/'parameters.scad').read_bytes()).hexdigest()
    report['sensor_to_desk_mm']=round(float(scene['scd30'].bounds[0,2]),3)
    report['sensor_back_to_plate_mm']=round(P['carrier_z']-scene['scd30'].bounds[1,2],3)
    report['references_verified']=0
    for ref in json.loads((HERE/'references.json').read_text()):
        assert hashlib.sha256((ROOT/ref['path']).read_bytes()).hexdigest()==ref['sha256']
        report['references_verified']+=1
    (HERE/'generated/validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS geometry:',len(report['checks']),'clearance pairs; 486 removal checks; exact STEP snap checks.',flush=True)

def pack(item,mesh):
    values=np.concatenate([mesh.triangles,np.repeat(mesh.face_normals[:,None,:],3,axis=1)],axis=2).astype('<f4')
    return {**item,'bounds':mesh.bounds.tolist(),'count':len(mesh.faces)*3,'data':base64.b64encode(values.tobytes()).decode('ascii')}

def sensor_color(i):
    return '#3c7056' if i==23 else '#bba16d' if i in (3,4,24) else '#41494b'

def viewer(scene):
    html=(CAD/'model.html').read_text()
    original=json.loads(re.search(r'<script id="model-data" type="application/json">(.*?)</script>',html,re.S)[1])
    meta={**original}
    parts=[dict(p) for p in original['parts'] if not p['id'].startswith('scd30-screw')]
    sensor_item=next(p for p in parts if p['id']=='scd30')
    for i,item in enumerate(parts):
        if item['id']=='carrier':
            parts[i]=pack({**item,'label':'Personal carrier · snap-in SCD30',
                'note':'Strengthened edge latches: 1.6 mm walls, wider clear-edge clips and 0.65 mm retaining lips. A 1.8 mm capture gap reduces play. Print flat upper face down.'},scene['carrier'])
        elif item['id']=='scd30':
            parts[i]=pack({**item,'label':'Bare Sensirion SCD30 · detailed model','color':sensor_color(23),
                'note':'Official Sensirion STEP geometry, including components on both PCB sides. The three latches engage clear PCB edges; the optical body stays free.'},scene['scd30-part-23'])
        elif item['id']=='qt3':
            item['note']='Original cable illustration retained. This personal bare sensor uses a soldered lead; its joints and actual routing are not modelled.'
    for i in range(25):
        if i==23:continue
        parts.append(pack({**sensor_item,'id':f'scd30-part-{i:02}','group':'_attached','parent':'scd30',
            'color':sensor_color(i),'note':''},scene[f'scd30-part-{i:02}']))
    # The user's original line is preserved byte for byte, including its plug meshes.
    for item in parts:
        if item['id']=='qt3' or item.get('parent')=='qt3':
            before=next(p for p in original['parts'] if p['id']==item['id'])
            assert all(item[k]==before[k] for k in ('data','bounds','count'))
    meta.update(version=P['variant_version'],variant='bare-scd30',parts=parts,
        source_sha256=hashlib.sha256((HERE/'carrier.scad').read_bytes()+(HERE/'parameters.scad').read_bytes()).hexdigest())
    template=(CAD/'viewer/template.html').read_text()
    template=template.replace('A solderless workshop device.','Personal prototype · snap-in bare SCD30.')
    template=template.replace('10 screws · no nuts.','8 screws · 2 RTC washers · no nuts.')
    template=template.replace('Board mounting holes come from manufacturer PCB files. Electronics are simplified clearance models; wires and fasteners are assembly guides.',
        'The bare SCD30 uses detailed manufacturer STEP geometry; its PCB edges snap into this personal carrier. Other electronics are simplified clearance models. The original cable illustration is retained; solder joints are not modelled.')
    template=template.replace('Derived board geometry: Adafruit Industries, CC BY-SA 3.0.',
        'Bare SCD30 geometry: Sensirion AG (official STEP). Other derived board geometry: Adafruit Industries, CC BY-SA 3.0.')
    result=template.replace('__MODEL_JSON__',json.dumps(meta,separators=(',',':'))).replace('__VIEWER_JS__',(CAD/'viewer/viewer.js').read_text()).replace('__VERSION__',P['variant_version']).replace('__LIGHT_SENSOR__',P['light_sensor'].upper())
    (HERE/'model.html').write_text(result)
    print('VIEWER:',sum(p['group']!='_attached' for p in parts),'selectable components',flush=True)

def section(ax,scene,x):
    for key in ['carrier']+[f'scd30-part-{i:02}' for i in range(25)]:
        sec=scene[key].section(plane_origin=[x,0,0],plane_normal=[1,0,0])
        if sec is None:continue
        polys=[np.asarray(p)[:,[1,2]] for p in sec.discrete if len(p)>3]
        polys.sort(key=lambda a:abs(np.sum(a[:,0]*np.roll(a[:,1],1)-a[:,1]*np.roll(a[:,0],1))),reverse=True)
        prior=[]
        for poly in polys:
            depth=sum(PlotPath(old).contains_point(poly[0]) for old in prior)
            ax.fill(poly[:,0],poly[:,1],color='white' if depth%2 else COLORS[key],ec='#334c50',lw=.6)
            prior.append(poly)
    ax.set(aspect='equal',xlabel='Y (mm)',ylabel='Z above desk (mm)');ax.grid(alpha=.15)

def drawing(scene):
    COLORS.update({f'scd30-part-{i:02}':sensor_color(i) for i in range(25)})
    chosen={k:v for k,v in scene.items() if k=='carrier' or k.startswith('scd30-part-')}
    rasterize(chosen,'Bare SCD30 · snap-in carrier','Three integral edge latches · optical chamber and both PCB sides stay clear',HERE/'renders/carrier.png',eye=(-.5,-1,-.85))
    rasterize({'carrier':scene['carrier']},'Snap carrier · sensor hidden',
        'Three ramps guide the PCB into loose edge captures · one plain side stop',HERE/'renders/snap-detail.png',eye=(-.5,-1,-.85))
    rasterize({k:v for k,v in chosen.items() if k!='carrier'},'Bare SCD30 · detailed manufacturer model',
        'PCB back shown: underside parts are included in the clearance checks',HERE/'renders/sensor-back.png',eye=(-.4,-.6,.85))
    fig,axes=plt.subplots(1,2,figsize=(13.5,8))
    section(axes[0],scene,49)
    axes[0].set(xlim=(16,44),ylim=(10,27),title='Section through front latch · X = 49 mm')
    axes[0].annotate('PCB captured at the edge',xy=(19,16.2),xytext=(24,12),fontsize=9,arrowprops=dict(arrowstyle='->'))
    axes[0].annotate('Open space behind sensor',xy=(29,21),xytext=(28,25.5),fontsize=9,arrowprops=dict(arrowstyle='->'))
    section(axes[1],scene,49)
    axes[1].set(xlim=(16.4,21),ylim=(13.5,19),title='Latch detail · same section')
    axes[1].annotate('Insertion ramp',xy=(18.75,14.1),xytext=(19.3,13.7),fontsize=9,arrowprops=dict(arrowstyle='->'))
    axes[1].annotate('0.1 mm face clearance',xy=(19.3,15.35),xytext=(19.3,14.7),fontsize=9,arrowprops=dict(arrowstyle='->'))
    axes[1].annotate('Back stop',xy=(19.4,17.3),xytext=(19.6,18.3),fontsize=9,arrowprops=dict(arrowstyle='->'))
    fig.suptitle('Bare SCD30 · integral snap holder',fontsize=19,x=.05,ha='left')
    fig.text(.05,.06,'Official Sensirion STEP geometry includes components on both PCB sides. Three clear PCB edges carry the module; the optical body stays free.\n'
        '1.6 mm PCB in a 1.8 mm capture gap; thicker 1.6 mm latch walls. Press at supported PCB edges; ease latches outward to release.\n'
        'Print upper face down, latches upward. PETG preferred for flexible latches. Nominal geometry checked; printed fit and retention remain untested.',fontsize=9,color='#526568')
    fig.subplots_adjust(left=.07,right=.97,top=.85,bottom=.2,wspace=.28)
    fig.savefig(HERE/'renders/mounting.png',dpi=170);fig.savefig(HERE/'mounting.pdf');plt.close(fig)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--skip-export',action='store_true');parser.add_argument('--skip-step',action='store_true');args=parser.parse_args()
    for folder in (PRINT,SCENE,HERE/'renders'):folder.mkdir(parents=True,exist_ok=True)
    for ref in json.loads((HERE/'references.json').read_text()):
        path=ROOT/ref['path']
        if not path.exists():
            data=urlopen(Request(ref['url'],headers={'User-Agent':'sensor-workshop-cad'}),timeout=45).read()
            assert hashlib.sha256(data).hexdigest()==ref['sha256'],ref['path']
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    if not args.skip_step:
        fc=os.environ.get('FREECAD_PYTHON','/Applications/FreeCAD.app/Contents/Resources/bin/python')
        with (SCENE/'prepare-sensor.log').open('w') as log:
            subprocess.run([fc,str(HERE/'prepare_sensor.py')],stdout=log,stderr=subprocess.STDOUT,check=True)
    if not args.skip_export:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(export,[False,True]))
    for name in ('01-shell.stl','03-feather-frame.stl'):shutil.copyfile(ROOT/'production-stls'/name,PRINT/name)
    scene=load_scene();validate(scene);viewer(scene);drawing(scene)

if __name__=='__main__':main()
