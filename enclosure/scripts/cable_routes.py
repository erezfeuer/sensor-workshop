#!/usr/bin/env python3
"""Smooth coloured cable illustrations, shared by OpenSCAD, PDF and HTML.

Connector entry directions follow the PCB orientation. Flexible routing is a
review illustration; supplier cable length and bend clearance need real parts.
"""
import json
import re
from pathlib import Path
import numpy as np
import trimesh
from scipy.interpolate import CubicHermiteSpline

CAD=Path(__file__).resolve().parents[1]
P={m[1]:json.loads(m[2]) for line in (CAD/'parameters.scad').read_text().splitlines()
   if (m:=re.match(r'(\w+)\s*=\s*(.*?);',line))}


def smooth(points, samples=100):
    a=np.asarray(points,float)
    t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(a,axis=0),axis=1))]
    tangent=np.gradient(a,t,axis=0)
    return CubicHermiteSpline(t,a,tangent)(np.linspace(0,t[-1],samples))


def tube(points,radius=.28,sides=8):
    path=np.asarray(points)
    tangent=np.gradient(path,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    normals=[]
    n=np.cross(tangent[0],[0,0,1] if abs(tangent[0,2])<.9 else [0,1,0]);n/=np.linalg.norm(n)
    for t in tangent:
        n=n-t*np.dot(n,t);n/=np.linalg.norm(n);normals.append(n.copy())
    n=np.array(normals);b=np.cross(tangent,n)
    angles=np.arange(sides)*2*np.pi/sides
    vertices=(path[:,None,:]+radius*(np.cos(angles)[None,:,None]*n[:,None,:]+np.sin(angles)[None,:,None]*b[:,None,:])).reshape(-1,3)
    faces=[]
    for i in range(len(path)-1):
        for j in range(sides):
            a=i*sides+j;c=i*sides+(j+1)%sides;d=c+sides;e=a+sides
            faces.extend([[a,c,d],[a,d,e]])
    for j in range(1,sides-1):
        faces.extend([[0,j+1,j],[(len(path)-1)*sides,(len(path)-1)*sides+j,(len(path)-1)*sides+j+1]])
    return trimesh.Trimesh(vertices=vertices,faces=faces)


def routes():
    # Endpoints are the cable side of nominal plug bodies, in assembly coordinates.
    fz=P['feather_origin'][2]-11.43
    rtc_shift=P['rtc_origin'][1]-12
    return [
        dict(id='qt1',label='QT · Feather → RTC',length=100,spread=[0,0,1],points=[
            [23.522,7.4,fz],[19,7.4,fz],[16,13,44],[23,24,39],
            [40,26,39],[55,23,43],[64,22,44],[67,16,48],[70.11,5.3+rtc_shift,55.1],[70.11,8.44+rtc_shift,55.1]],
            plugs=[([3.8,2,5.4],[25.422,7.4,fz]),([5.4,3.8,2],[70.11,10.34+rtc_shift,55.1])]),
        dict(id='qt2',label='QT · RTC → light sensor',length=50,spread=[1,0,0],points=[
            [70.11,40.96+rtc_shift,55.1],[70.11,44,55.1],[67.5,45,55.2],
            [67.6,37.5,57.3],[67.6,29,57.3],[64,25.89,56.4],[58.833,25.89,56.4]],
            plugs=[([5.4,3.8,2],[70.11,39.06+rtc_shift,55.1]),([3.8,5.4,2],[56.933,25.89,56.4])]),
        dict(id='qt3',label='QT · Light sensor → SCD30',length=100,spread=[0,1,0],points=[
            [26.567,25.89,56.4],[22,25.89,56.4],[15.5,28,51],
            [14.5,34,44],[17,37,35],[17,34,27],[17,33,22],[14,34.11,16.9],[17.567,34.11,16.9]],
            plugs=[([3.8,5.4,2],[28.467,25.89,56.4]),([3.8,5.4,2],[19.467,34.11,16.9])]),
        dict(id='battery_lead',label='Battery lead · open frame notch',length=None,spread=[0,1,0],points=[
            [9.8,50,41],[7.5,50,41],[7.5,41,38],[10,32,34],
            [16.795,23,31],[16.795,19,29],[16.795,15,28.9],
            [16.795,12,28.7],[16.795,9.2,28.9],[16.795,8.3,30.896]],
            plugs=[([6.4,3.2,3.8],[16.795,8.3,32.796])])
    ]


def build():
    scene=CAD/'generated/scene';scene.mkdir(parents=True,exist_ok=True)
    for path in scene.glob('cable_*.stl'):path.unlink()
    entries=[];scad=['// Generated smooth cable illustrations. Not fabrication geometry.','module cables() {']
    for route in routes():
        path=smooth(route['points'])
        colors=['#30383b','#c55349','#4986ad','#d4ad4a'] if route['id'].startswith('qt') else ['#c55349','#30383b']
        # Parallel wire offsets twist gradually between the two plug orientations.
        first=np.asarray(route['spread'],float)
        last=np.array([1,0,0]) if route['id'] in ['qt1','battery_lead'] else np.array([0,1,0]) if route['id']=='qt2' else first
        spacing=.95 if route['id'].startswith('qt') else 1.1
        offsets=np.linspace(-spacing,spacing,len(colors))
        parent=route['id']
        for i,(color,off) in enumerate(zip(colors,offsets)):
            blend=np.linspace(0,1,len(path))[:,None]
            pts=path+off*((1-blend)*first+blend*last)
            mesh=tube(pts,.28 if route['id'].startswith('qt') else 1.0)
            key='cable_'+parent+('_'+str(i))
            (scene/(key+'.stl')).write_bytes(trimesh.exchange.stl.export_stl(mesh))
            entries.append(dict(mesh=key,id=parent if i==0 else key,parent=None if i==0 else parent,
                label=route['label'],color=color,cable=True,
                note='Smooth routing illustration; '+(str(route['length'])+' mm trial lead. ' if route['length'] else 'Lay the connected lead in the open frame notch; no threading or unplugging is needed to release it from the frame. Two 2 mm OD wires are illustrated. Leave slack above the carrier. ')+'Check bend radius and slack on the pilot.'))
            # Low-overhead OpenSCAD polyhedron; no thousands of Boolean hull operations.
            scad.append('color("'+color+'") polyhedron(points='+json.dumps(np.round(mesh.vertices,4).tolist(),separators=(',',':'))+',faces='+json.dumps(mesh.faces.tolist(),separators=(',',':'))+',convexity=4);')
        for i,(size,center) in enumerate(route['plugs']):
            m=trimesh.creation.box(extents=size);m.apply_translation(center)
            key='cable_'+parent+'_plug'+str(i)
            (scene/(key+'.stl')).write_bytes(trimesh.exchange.stl.export_stl(m))
            entries.append(dict(mesh=key,id=key,parent=parent,label=route['label'],color='#ece8d9',cable=True,note='Nominal connector plug envelope.'))
            scad.append('color("#ece8d9") translate('+json.dumps(center)+') cube('+json.dumps(size)+',center=true);')
    scad.append('}')
    (CAD/'generated/cables.scad').write_text('\n'.join(scad)+'\n')
    (CAD/'generated/cable-metadata.json').write_text(json.dumps(entries,indent=2)+'\n')
    measures=[{'id':r['id'],'illustrated_centerline_mm':round(float(np.linalg.norm(np.diff(smooth(r['points']),axis=0),axis=1).sum()),1),'trial_lead_mm':r['length']} for r in routes()]
    (CAD/'generated/cable-lengths.json').write_text(json.dumps(measures,indent=2)+'\n')
    print(json.dumps(measures,indent=2))


if __name__=='__main__':build()
