#!/usr/bin/env python3
"""Build the personal three-file print set, check its fit and make an offline viewer."""
import argparse
import base64
import concurrent.futures
import hashlib
import itertools
import json
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
from build_viewer import box, screw
from cable_routes import tube, smooth
from battery_ties import ribbon_mesh
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

def export(job):
    part,assembled=job
    dest=SCENE/(part+'.stl') if assembled else PRINT/'02-sensor-carrier-bare-scd30.stl'
    result=subprocess.run(['openscad','--export-format','binstl','-o',str(dest),'-D',f'variant_part="{part}"',
        '-D','assembly_coordinates='+str(assembled).lower(),str(HERE/'carrier.scad')],capture_output=True,text=True)
    log=result.stdout+result.stderr
    (SCENE/(part+('-scene' if assembled else '-print')+'.log')).write_text(log)
    if result.returncode or 'WARNING:' in log or 'ERROR:' in log:raise RuntimeError(log)
    print('EXPORTED',dest.relative_to(ROOT),flush=True)

def overlap(a,b):
    if np.any(a.bounds[1]<b.bounds[0]) or np.any(b.bounds[1]<a.bounds[0]):return 0.
    m=trimesh.boolean.intersection([a,b],engine='manifold')
    return abs(float(m.volume)) if len(m.faces) else 0.

def load_scene():
    scene={p.stem:trimesh.load_mesh(p) for p in (CAD/'generated/scene').glob('*.stl') if not p.stem.startswith('cable_qt3')}
    scene['carrier']=trimesh.load_mesh(SCENE/'carrier.stl')
    scene['scd30']=trimesh.load_mesh(SCENE/'sensor.stl')
    scene['scd30-header']=trimesh.load_mesh(SCENE/'header.stl')
    for i,xy in enumerate(P['retainer_centers']):
        w=trimesh.creation.annulus(r_min=P['retainer_washer'][0]/2,r_max=P['retainer_washer'][1]/2,
            height=P['retainer_washer'][2],sections=48)
        w.apply_translation([*xy,P['retainer_z']-P['retainer_washer'][2]/2])
        scene[f'scd30-washer-{i}']=w
        scene[f'scd30-screw-{i}']=screw([*xy,P['retainer_z']-P['retainer_washer'][2]],5,2,[0,0,1])
    # The pigtail has ONE QT plug, at the light board. Four insulated solder joints
    # sit above the header; the unmodelled service loop is fitted by the assembler.
    scene['personal_plug']=box([3.8,5.4,2],[28.467,25.89,56.4])
    for i,pin in enumerate((1,0,3,2)): # black GND, red VDD, blue SDA, yellow SCL
        x=P['header_first'][0]+pin*P['header_pitch']
        offset=(i-1.5)*.65
        points=[[26.567,25.89+offset,56.4],[22,25.89+offset,56.4],[15.5,28+offset,51],
            [14.5,34+offset,44],[17,37+offset,35],[20,32+offset,29],
            [23.5,31+offset,28],[x,33+offset,28],[x,36.6,27]]
        scene[f'personal_wire_{i}']=tube(smooth(points),.28)
    # Separate strain-relief tie, away from the sensor. Smooth corners leave the
    # vertical legs inside the paired carrier slots. Nominal loose loop only.
    points=np.array([[28,23.2],[28,28.4],[29,29.2],[33,29.2],[34,28.4],[34,23.2],[33.2,22.5],[28.8,22.5]])
    loop=[]
    for i,b in enumerate(points):
        a=points[i-1];c=points[(i+1)%len(points)]
        start=b+(a-b)/np.linalg.norm(a-b)*.25;end=b+(c-b)/np.linalg.norm(c-b)*.25
        for t in np.linspace(0,1,5):loop.append((1-t)**2*start+2*(1-t)*t*b+t*t*end)
    scene['scd30-strain-tie']=trimesh.util.concatenate([ribbon_mesh(23.5,loop,closed=True,thickness=.6),box([4,3,2],[23.5,31,22.5])])
    return scene

def validate(scene):
    report={'status':'passed','variant':P['variant_version'],'units':'mm','print_parts':{},'checks':[],
        'limitations':['Nominal CAD checks, not print-fit, clamp-retention, solder-joint or thermal qualification.',
            'Bare sensor uses a conservative envelope; header body and washer dimensions must be measured.',
            'Wires show nominal routes; service slack and insulation are checked during assembly.']}
    expected={'01-shell.stl','02-sensor-carrier-bare-scd30.stl','03-feather-frame.stl'}
    assert {p.name for p in PRINT.iterdir()}==expected
    for name in expected:
        path=PRINT/name;m=trimesh.load_mesh(path)
        assert m.is_watertight and m.is_winding_consistent and m.volume>0 and len(m.split())==1,name
        assert abs(m.bounds[0,2])<.002,name
        report['print_parts'][name]={'watertight':True,'bodies':1,'size_mm':m.extents.round(3).tolist(),
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    for name in ('01-shell.stl','03-feather-frame.stl'):
        assert (PRINT/name).read_bytes()==(ROOT/'production-stls'/name).read_bytes()
    # The closure interface is identical above the original carrier plane outside
    # the sensor island. Include the locating rim and both M3 through-holes.
    old=trimesh.load_mesh(CAD/'generated/scene/carrier.stl')
    mask=box([110,80,1.8],[46,33,25.5])
    island=box([60,35,5],[46,31,25])
    mask=trimesh.boolean.difference([mask,island],engine='manifold')
    a=trimesh.boolean.intersection([old,mask],engine='manifold')
    b=trimesh.boolean.intersection([scene['carrier'],mask],engine='manifold')
    # Exclude the underside-only marking from the comparison by the Z mask.
    assert abs(a.volume-b.volume)<.002,('Closure interface changed',a.volume,b.volume)
    assert overlap(a,b)>a.volume-.002
    report['closure_interface_matches_workshop']=True
    fixed=['shell','feather_frame','feather','light','rtc','battery']
    personal=['carrier','scd30','scd30-header','scd30-strain-tie']+[f'scd30-{kind}-{i}' for kind in ('washer','screw') for i in range(2)]
    def clear(a,b,ma=None,mb=None):
        v=overlap(scene[a] if ma is None else ma,scene[b] if mb is None else mb)
        assert v<.001,(a,b,v)
        report['checks'].append({'a':a,'b':b,'intersection_mm3':round(v,6)})
    for a in personal:
        for b in fixed:clear(a,b)
    for a,b in itertools.combinations(personal,2):
        # Threads intentionally cut into the carrier pilots; exclude only that pair.
        if a=='carrier' and b.startswith('scd30-screw'):continue
        clear(a,b)
    for name in [n for n in scene if n.startswith(('personal_','cable_'))]:
        for other in personal+fixed:
            if name.startswith('personal_wire_') and other=='scd30-header':
                pin=(1,0,3,2)[int(name.rsplit('_',1)[1])]
                joint=box([1.4,1.4,1.4],[P['header_first'][0]+pin*P['header_pitch'],P['header_first'][1],27])
                away=trimesh.boolean.difference([scene[other],joint],engine='manifold')
                clear(name,other,mb=away) # Only its own soldered pin may contact the wire.
            else:clear(name,other)
    report['intentional_contacts']='Screw threads in printed pilots; each pigtail wire at its own header-pin solder joint only.'
    # Steel washers must geometrically retain the plastic header, yet leave its
    # cavity untouched. Force a downward removal and check the stop engagement.
    center=[P['header_first'][0]+3*P['header_pitch'],P['header_first'][1],P['header_seat_z']-P['header_body'][2]/2]
    body=box(P['header_body'],center)
    drop=body.copy();drop.apply_translation([0,0,-.6])
    catches=[]
    for i in range(2):
        v=overlap(drop,scene[f'scd30-washer-{i}']);assert v>.1,('Washer does not capture header',i,v)
        catches.append(round(v,3))
    up=body.copy();up.apply_translation([0,0,.2]);assert overlap(up,scene['carrier'])>.1
    worst_catch=[]
    for dx,dy in itertools.product((-.2,.2),repeat=2):
        shifted=scene['scd30-header'].copy();shifted.apply_translation([dx,dy,0])
        assert overlap(shifted,scene['carrier'])<.001,('Header pin side play',dx,dy)
        for i in range(2):
            assert overlap(shifted,scene[f'scd30-washer-{i}'])<.001,('Washer contacts pin',dx,dy,i)
            displaced=drop.copy();displaced.apply_translation([dx,dy,0])
            v=overlap(displaced,scene[f'scd30-washer-{i}']);assert v>.1,('Header can escape',dx,dy,i,v)
            worst_catch.append(v)
    for axis in (0,1):
        for sign in (-1,1):
            shifted=body.copy();shifted.apply_translation(np.eye(3)[axis]*sign*.5)
            assert overlap(shifted,scene['carrier'])>.1,('Header pocket lacks side stop',axis,sign)
    report['header_capture']={'nominal_vertical_play_mm':round(P['header_seat_z']-P['header_body'][2]-P['retainer_z'],3),
        'side_clearance_mm':P['header_clearance'],'washers_stop_downward_motion_mm3':catches,
        'end_seat_width_mm':round((P['header_body'][0]-P['wire_window'][0])/2,3)}
    report['header_capture']['xy_offsets_checked_mm']=[-.2,.2]
    report['header_capture']['minimum_capture_overlap_mm3']=round(min(worst_catch),3)
    # Feed the pre-soldered lead's single plug through the empty pocket edge-on.
    for z in np.linspace(18,30,25):
        plug=box([5.4,2,3.8],[center[0],center[1],z])
        assert overlap(plug,scene['carrier'])<.001,('QT plug feed',z)
    report['qt_plug_feed']={'poses':25,'oriented_plug_mm':[5.4,2,3.8]}
    # Entire carrier/header/sensor/retainers can be lowered out of the existing case.
    moving=trimesh.util.concatenate([scene[n] for n in personal])
    for dz in np.linspace(-40,0,81):
        candidate=moving.copy();candidate.apply_translation([0,0,dz])
        for name in fixed:assert overlap(candidate,scene[name])<.001,('Carrier removal',dz,name)
    report['carrier_removal']={'poses':81,'checks':486,'travel_mm':40}
    for i,xy in enumerate(P['retainer_centers']):
        tool=trimesh.creation.cylinder(radius=1.5,height=100,sections=24)
        tool.apply_translation([*xy,P['retainer_z']-P['retainer_washer'][2]-50-.05])
        assert overlap(tool,scene['scd30'])<.001,('Driver reaches sensor',i)
    report['straight_screwdriver_access']=True
    report['sensor_to_desk_mm']=round(float(scene['scd30'].bounds[0,2]),3)
    report['sensor_to_carrier_underside_mm']=round(P['carrier_z']-scene['scd30'].bounds[1,2],3)
    report['sensor_to_washer_mm']=round(P['retainer_z']-P['retainer_washer'][2]-scene['scd30'].bounds[1,2],3)
    report['header_long_leg_protrusion_below_pcb_mm']=round(P['bare_origin'][2]-P['bare_pcb_thickness']-(P['header_seat_z']-P['header_body'][2]-P['header_long_leg']),3)
    report['references_verified']=0
    for ref in json.loads((HERE/'references.json').read_text()):
        assert hashlib.sha256((ROOT/ref['path']).read_bytes()).hexdigest()==ref['sha256']
        report['references_verified']+=1
    (HERE/'generated/validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS geometry:',len(report['checks']),'clearance pairs; 486 removal checks; header capture.',flush=True)

def pack(item,mesh):
    values=np.concatenate([mesh.triangles,np.repeat(mesh.face_normals[:,None,:],3,axis=1)],axis=2).astype('<f4')
    return {**item,'bounds':mesh.bounds.tolist(),'count':len(mesh.faces)*3,'data':base64.b64encode(values.tobytes()).decode('ascii')}

def viewer(scene):
    html=(CAD/'model.html').read_text()
    meta=json.loads(re.search(r'<script id="model-data" type="application/json">(.*?)</script>',html,re.S)[1])
    parts=[p for p in meta['parts'] if not (p['id'].startswith('scd30-screw') or p['id']=='qt3' or p.get('parent')=='qt3')]
    for i,item in enumerate(parts):
        if item['id'] in ('carrier','scd30'):
            item=pack(item,scene[item['id']])
            if item['id']=='carrier':item.update(label='Personal carrier · BARE SCD30',note='Header pocket and two wide-washer retainers. Print upper face down. This part replaces the workshop carrier for this personal prototype only.')
            else:item.update(label='Bare Sensirion SCD30 · envelope',note='35 × 23 mm bare module; cavity faces down. Supported by its seven contact pins only. This conservative envelope is not the detailed sensor shape.')
            parts[i]=item
    def add(key,label,group,color,delta,note,parent=None,cable=False):
        parts.append(pack(dict(id=key,label=label,group=group,color=color,delta=delta,note=note,parent=parent,
            cable=cable,defaultVisible=True,capX=None),scene[key]))
    add('scd30-header','SCD30 7-pin header','Electronics','#484e51',[0,0,-56],
        'Standard 2.54 mm pitch; approximately 17.78 × 2.54 × 2.54 mm plastic body. Long legs face sensor; short legs carry the soldered lead.')
    add('scd30-strain-tie','Pigtail strain-relief tie','Wiring','#717b78',[0,0,-46],
        'One extra 2.5 mm nylon tie through the paired slots. Holds insulated cable, away from sensor body and solder joints. Nominal loose-loop illustration.')
    for i in range(2):
        add(f'scd30-washer-{i}',f'Header retainer washer {i+1} · Ø8 mm','Fasteners','#b9c0c2',[0,0,-72],
            'M2 large flat washer: 2.2 mm bore, 8 mm OD, 0.5 mm thick. Captures header plastic without touching sensor.')
        add(f'scd30-screw-{i}',f'Header retainer screw {i+1} · M2 × 5','Fasteners','#a3adb4',[0,0,-78],
            'Two existing sensor screws move to these stout carrier bosses. Tighten to the printed stop, never onto the sensor.')
    for i,color in enumerate(('#30383b','#c55349','#4986ad','#d4ad4a')):
        add(f'personal_wire_{i}','Soldered QT pigtail · light → bare SCD30','Wiring' if i==0 else '_attached',color,[0,0,0],
            'One QT plug at the light board; four insulated solder joints at the header. Add a service loop and a strain-relief tie. Nominal routing only.',
            parent=None if i==0 else 'personal_wire_0',cable=True)
    add('personal_plug','QT plug at light board','_attached','#ece8d9',[0,0,0],'',parent='personal_wire_0',cable=True)
    meta.update(version=P['variant_version'],variant='bare-scd30',parts=parts,
        source_sha256=hashlib.sha256((HERE/'carrier.scad').read_bytes()+(HERE/'parameters.scad').read_bytes()).hexdigest())
    template=(CAD/'viewer/template.html').read_text()
    template=template.replace('A solderless workshop device.','Personal prototype with a soldered SCD30 pigtail.')
    template=template.replace('10 screws · no nuts.','10 screws · 4 washers · no nuts.')
    template=template.replace('Board mounting holes come from manufacturer PCB files.','The bare SCD30 hangs from a captured 7-pin header; its body is not clamped. Other board patterns come from manufacturer files.')
    result=template.replace('__MODEL_JSON__',json.dumps(meta,separators=(',',':'))).replace('__VIEWER_JS__',(CAD/'viewer/viewer.js').read_text()).replace('__VERSION__',P['variant_version']).replace('__LIGHT_SENSOR__',P['light_sensor'].upper())
    (HERE/'model.html').write_text(result)
    print('VIEWER:',sum(p['group']!='_attached' for p in parts),'selectable components',flush=True)

def drawing(scene):
    COLORS.update({'scd30-header':'#484e51','scd30-strain-tie':'#717b78',**{f'scd30-{kind}-{i}':'#b9c0c2' for kind in ('washer','screw') for i in range(2)}})
    COLORS.update({f'personal_wire_{i}':c for i,c in enumerate(('#30383b','#c55349','#4986ad','#d4ad4a'))})
    COLORS['personal_plug']='#ece8d9'
    chosen={k:v for k,v in scene.items() if k in ('carrier','scd30','scd30-header') or k.startswith(('scd30-washer','scd30-screw'))}
    rasterize(chosen,'Personal carrier · bare SCD30','Header retained by two wide washers · sensing body faces down · no body clamp',HERE/'renders/carrier.png',eye=(-.5,-1,-.85))
    rasterize({k:v for k,v in chosen.items() if k!='scd30'},'Header mount · sensor hidden',
        'Two wide washers retain the header plastic · screw heads and sensor body stay separate',HERE/'renders/header-mount.png',eye=(-.4,1,-.85))
    fig,axes=plt.subplots(1,2,figsize=(13.5,8))
    ax=axes[0]
    for key in ('carrier','scd30','scd30-header','scd30-washer-0','scd30-screw-0'):
        section=scene[key].section(plane_origin=[33,0,0],plane_normal=[1,0,0])
        if section is None:continue
        polys=[np.asarray(p)[:,[1,2]] for p in section.discrete if len(p)>3]
        polys.sort(key=lambda a:abs(np.sum(a[:,0]*np.roll(a[:,1],1)-a[:,1]*np.roll(a[:,0],1))),reverse=True)
        prior=[]
        for poly in polys:
            depth=sum(PlotPath(old).contains_point(poly[0]) for old in prior)
            ax.fill(poly[:,0],poly[:,1],color='white' if depth%2 else COLORS[key],ec='#334c50',lw=.6)
            prior.append(poly)
    ax.set(xlim=(30,46),ylim=(10,29),aspect='equal',xlabel='Y (mm): front ← → rear',ylabel='Z above desk (mm)',title='True section at X = 33 mm')
    ax.annotate('Header body',xy=(36.6,22.5),xytext=(31,28),fontsize=9,arrowprops=dict(arrowstyle='->'))
    ax.annotate('Wide washer\nretains header',xy=(37.1,20.95),xytext=(41,16),fontsize=9,arrowprops=dict(arrowstyle='->'))
    ax.text(30.4,12.8,'Sensor envelope\n(no clamping contact)',fontsize=9)
    ax.grid(alpha=.15)
    ax=axes[1]
    ax.add_patch(plt.Rectangle((0,0),35,23,fc='#f3ecd9',ec='#736548'))
    ax.add_patch(plt.Rectangle((3,3.5),28,16,fc='#d1bf94',ec='#736548'))
    labels=['VDD','GND','SCL','SDA','RDY','PWM','SEL']
    for i,label in enumerate(labels):
        x=1.4+i*2.54
        ax.add_patch(plt.Circle((x,21.6),.5,color='#334c50'))
        ax.text(x,24,label,rotation=60,ha='left',fontsize=9)
    ax.text(17.5,11.5,'OPTICAL CAVITY\nfaces down when installed',ha='center',va='center',fontsize=11)
    ax.set(xlim=(-2,37),ylim=(-2,31),aspect='equal',title='Cavity-side view · contact order',xlabel='Module length 35 mm',ylabel='Width 23 mm')
    ax.set_xticks([]);ax.set_yticks([])
    fig.suptitle('Bare SCD30 · personal mounting and wiring reference',fontsize=19,x=.05,ha='left')
    fig.text(.05,.06,'3 separate prints. Reuse the v0.6 shell and reinforced frame; replace the carrier. Sensor shown as a conservative clearance envelope.\n'
        'QT: red → VDD, black → GND, yellow → SCL, blue → SDA. Leave RDY/PWM/SEL unconnected; verify labels and continuity.\n'
        'Capture only the header plastic. Solder outside the print; insulate joints and secure the cable to the strain-relief slots. Physical fit remains untested.',fontsize=9,color='#526568')
    fig.subplots_adjust(left=.07,right=.97,top=.85,bottom=.2,wspace=.3)
    fig.savefig(HERE/'renders/mounting.png',dpi=170);fig.savefig(HERE/'mounting.pdf');plt.close(fig)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--skip-export',action='store_true');args=parser.parse_args()
    for folder in (PRINT,SCENE,HERE/'renders'):folder.mkdir(parents=True,exist_ok=True)
    for ref in json.loads((HERE/'references.json').read_text()):
        path=ROOT/ref['path']
        if not path.exists():
            data=urlopen(Request(ref['url'],headers={'User-Agent':'sensor-workshop-cad'}),timeout=45).read()
            assert hashlib.sha256(data).hexdigest()==ref['sha256'],ref['path']
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    if not args.skip_export:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(export,[('carrier',False),('carrier',True),('sensor',True),('header',True)]))
    for name in ('01-shell.stl','03-feather-frame.stl'):shutil.copyfile(ROOT/'production-stls'/name,PRINT/name)
    scene=load_scene();validate(scene);viewer(scene);drawing(scene)

if __name__=='__main__':main()
