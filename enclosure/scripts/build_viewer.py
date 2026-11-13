#!/usr/bin/env python3
"""Build one offline HTML file from the positioned OpenSCAD meshes.

Each printed piece, board, battery, strap and fastener is independently visible.
Hardware shapes are nominal assembly illustrations, not fabrication models.
"""
import base64
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh
from render_review import CAD, PARAMS, COLORS, load_scene


def box(size, center):
    m = trimesh.creation.box(extents=size)
    m.apply_translation(center)
    return m


def cylinder(radius, height, center, sections=24):
    m = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    m.apply_translation(center)
    return m


def screw(point, length, diameter, direction=(0, 0, -1)):
    # Local +Z points from the bearing face into the screw shaft.
    shaft = cylinder(diameter / 2, length, [0, 0, length / 2])
    head = cylinder(diameter, diameter * .7, [0, 0, -diameter * .35])
    m = trimesh.util.concatenate([shaft, head])
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], direction))
    m.apply_translation(point)
    return m


def tie_mesh(x):
    # Rectangular 2.5 × 0.5 mm ribbon with rounded bends, through each cradle tunnel.
    yz=np.array([[37,55.1],[63,55.1],[63,38],[59,32],[54,30],[46,30],[41,32],[37,38]],float)
    points=[]
    for i,b in enumerate(yz):
        a=yz[(i-1)%len(yz)];c=yz[(i+1)%len(yz)]
        d=min(1.,np.linalg.norm(a-b)/3,np.linalg.norm(c-b)/3)
        start=b+(a-b)/np.linalg.norm(a-b)*d;end=b+(c-b)/np.linalg.norm(c-b)*d
        for t in np.linspace(0,1,8):points.append((1-t)**2*start+2*(1-t)*t*b+t*t*end)
    points=np.array(points);tangent=np.roll(points,-1,axis=0)-np.roll(points,1,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    n=np.c_[-tangent[:,1],tangent[:,0]]
    vertices=[]
    for p,v in zip(points,n):
        for dx,dn in [(-1.25,-.25),(1.25,-.25),(1.25,.25),(-1.25,.25)]:vertices.append([x+dx,*(p+v*dn)])
    faces=[]
    for i in range(len(points)):
        for j in range(4):
            a=i*4+j;b=i*4+(j+1)%4;c=((i+1)%len(points))*4+(j+1)%4;d=((i+1)%len(points))*4+j
            faces.extend([[a,b,c],[a,c,d]])
    ribbon=trimesh.Trimesh(vertices=vertices,faces=faces)
    ribbon.fix_normals()
    head=box([4.5,4,3],[x,50,29.5])
    return trimesh.util.concatenate([ribbon,head])


def main():
    scene=load_scene()
    # Coin holder ring lets the independent coin cell be inspected from below.
    z=PARAMS['rtc_origin'][2]
    coin_center=[PARAMS['rtc_origin'][0]-10.795,PARAMS['rtc_origin'][1]+12.7,z-1.9]
    top=trimesh.intersections.slice_mesh_plane(scene['rtc'],[0,0,1],[0,0,z],cap=True)
    holder=trimesh.creation.annulus(r_min=6.05,r_max=6.5,height=3.2,sections=36)
    holder.apply_translation([coin_center[0],coin_center[1],z-1.6])
    scene['rtc']=trimesh.util.concatenate([top,holder])
    items=[]
    def add(key,label,group,mesh,color,delta,note,parent=None,cable=False):
        packed=np.concatenate([mesh.triangles,np.repeat(mesh.face_normals[:,None,:],3,axis=1)],axis=2).astype('<f4')
        items.append(dict(id=key,label=label,group=group,color=color,delta=delta,note=note,parent=parent,cable=cable,
                          bounds=mesh.bounds.tolist(),count=len(mesh.faces)*3,data=base64.b64encode(packed.tobytes()).decode('ascii')))
    deltas={'shell':[0,0,0],'carrier':[0,0,-46],'feather':[0,0,-80],'feather_frame':[0,0,-80],'light':[0,0,-18],
            'rtc':[25,0,-18],'scd30':[0,0,-65],'battery':[0,22,-22]}
    defs=[
        ('shell','Shell + straight feet + skirt','Printed enclosure','One print: roof, straight feet, open-bottom skirt, mounts and battery cradles. Print roof-down.'),
        ('carrier','Bottom carrier plate','Printed enclosure','One carrier with four thermal bridges around the SCD30 mounting island. Two closure screws retain this plate and the Feather frame.'),
        ('feather_frame','Removable Feather mounting frame','Printed enclosure','Attach the Feather with two front-access screws on the table. Slide upward through the open bottom; the carrier captures its lower ends. Print flat rear face down.'),
        ('feather','ESP32-S3 Reverse TFT Feather','Electronics','Real buttons accessible through the front slot. Two screws fasten to the removable frame OUTSIDE the housing; no sideways driver inside the box.'),
        ('light','VEML7700 light sensor','Electronics','Faces upward through the roof aperture. Two screws and two locating pins.'),
        ('rtc','DS3231 RTC + holder','Electronics','Rotated 90° so QT sockets face front/rear. Two screws, two washers.'),
        ('scd30','SCD30 · facing downward','Electronics','Mounted under the carrier. The underside is open; the shallow skirt gives shade.'),
        ('battery','Protected 18650 pack','Electronics','Local pack envelope Ø20 × 72 mm; two soft zip ties in printed cradles. Direct battery connection.')]
    for key,label,group,note in defs:add(key,label,group,scene[key],COLORS[key],deltas[key],note)
    add('display','Display face','_attached',scene['display'],COLORS['display'],deltas['feather'],'',parent='feather')
    add('coin','CR1220 backup cell','Electronics',cylinder(6,2,coin_center),'#c1c7cb',[25,0,-26],'Local non-rechargeable backup cell.')
    boards=json.loads((CAD/'generated/boards.json').read_text())
    for board,key in [('feather','feather'),('scd30','scd30'),('rtc','rtc'),('veml7700','light')]:
        origin=np.array(PARAMS[key+'_origin'])
        indices=range(2) if key=='rtc' else PARAMS['board_screw_indices']
        for i in indices:
            x,y,_=boards[board]['holes'][i]
            if key=='feather':point=origin+[x,0,-y];direction=[0,1,0]
            elif key=='scd30':point=origin+[x,-y,-1.6];direction=[0,0,1]
            elif key=='rtc':point=origin+[-y,x,-.5];direction=[0,0,1]
            else:point=origin+[x,y,0];direction=[0,0,1]
            add(f'{key}-screw-{i}',f'{key.upper()} screw {i+1} · M2 × 5','Fasteners',screw(point,5,2,direction),'#a3adb4',deltas[key],'Two screws per board; the four-hole boards also have two printed locating pins.')
            if key=='rtc':
                m=trimesh.creation.annulus(r_min=1.1,r_max=2.5,height=.5,sections=24);m.apply_translation(origin+[-y,x,-.25])
                add(f'rtc-washer-{i}',f'RTC washer {i+1}','Fasteners',m,'#b9c0c2',deltas[key],'Thin M2 washer around the board’s 3 mm hole.')
    for i,p in enumerate(PARAMS['case_mounts']):
        add(f'case-screw-{i}',f'Closure screw {i+1} · M3 × 8','Fasteners',screw([*p,PARAMS['carrier_z']],8,3,[0,0,1]),'#a3adb4',[0,0,-58],'Threads into a printed pilot. No nuts or heat-set inserts.')
    for i,x in enumerate(PARAMS['battery_saddles']):
        add(f'tie-{i}',f'Battery zip tie {i+1}','Wiring',tie_mesh(x),'#717b78',deltas['battery'],'2.5 mm soft nylon tie; secure gently around the protected pack, without compression.')
    for c in json.loads((CAD/'generated/cable-metadata.json').read_text()):
        add(c['id'],c['label'],'_attached' if c['parent'] else 'Wiring',scene[c['mesh']],c['color'],[0,0,0],c['note'],parent=c['parent'],cable=True)
    count=sum(x['group']!='_attached' for x in items)
    meta=dict(version='0.3',units='mm',size=[92,66,60.8],parts=items,
              source_sha256=hashlib.sha256((CAD/'sensor-workshop.scad').read_bytes()+(CAD/'parameters.scad').read_bytes()).hexdigest())
    template=(CAD/'viewer/template.html').read_text()
    result=template.replace('__MODEL_JSON__',json.dumps(meta,separators=(',',':'))).replace('__VIEWER_JS__',(CAD/'viewer/viewer.js').read_text())
    (CAD/'model.html').write_text(result)
    print(f'model.html: {count} selectable components, three printed parts, {len(result)/1024/1024:.1f} MB offline')


if __name__=='__main__':main()
