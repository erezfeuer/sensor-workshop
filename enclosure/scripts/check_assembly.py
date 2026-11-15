#!/usr/bin/env python3
"""Sample the actual insertion path and screwdriver shafts, in millimetres.

Rigid nominal envelopes only. No cable sweep, hand model or tolerance simulation.
"""
import json
import warnings
import numpy as np
import trimesh
from render_review import CAD, PARAMS as p
from build_viewer import screw, box
warnings.filterwarnings('ignore',category=RuntimeWarning,module='trimesh.triangles')

def overlap(a,b):
    if np.any(a.bounds[1]<b.bounds[0]) or np.any(b.bounds[1]<a.bounds[0]):return 0.
    mesh=trimesh.boolean.intersection([a,b],engine='manifold')
    return abs(float(mesh.volume)) if len(mesh.faces) else 0.

scene=CAD/'generated/scene'
meshes={n:trimesh.load_mesh(scene/(n+'.stl')) for n in ['shell','carrier','feather_frame','feather','light','rtc','scd30','battery']}
boards=json.loads((CAD/'generated/boards.json').read_text())
moving=[meshes['feather_frame'],meshes['feather']]
for i in p['board_screw_indices']:
    x,y,_=boards['feather']['holes'][i]
    moving.append(screw(np.array(p['feather_origin'])+[x,0,-y],5,2,[0,1,0]))
unit=trimesh.boolean.union(moving,engine='manifold')
max_intersection=0;checks=0
for dz in np.linspace(-80,0,161):
    candidate=unit.copy();candidate.apply_translation([0,0,dz])
    for name in ['shell','light','rtc','battery']:
        volume=overlap(candidate,meshes[name]);checks+=1
        assert volume<.001,('Feather insertion',dz,name,volume)
        max_intersection=max(max_intersection,volume)
report={'status':'passed','sampled_path':{'axis':'+Z into shell','start_offset_mm':-80,'end_offset_mm':0,
    'step_mm':.5,'poses':161,'checks':checks,'max_intersection_mm3':round(max_intersection,6),
    'moving_parts':['Feather','mounting frame','two installed M2x5 screws'],
    'obstacles':['shell including rails','light sensor','RTC','battery'],
    'removed':['carrier and attached SCD30','closure screws','unplugged battery and QT leads']},'screwdriver_checks':[]}

# A merely tangent rail can pass the nominal test but bind in a real print.
# Small rigid offsets check that the model has play; they do not model shrinkage.
for dz in [-40,-20,-5,0]:
    for dx,dy in [(-.1,-.1),(-.1,.1),(.1,-.1),(.1,.1)]:
        candidate=unit.copy();candidate.apply_translation([dx,dy,dz])
        for name in ['shell','light','rtc','battery']:
            assert overlap(candidate,meshes[name])<.001,('Feather sliding margin',dx,dy,dz,name)
report['sliding_margin_check']={'xy_offsets_mm':[-.1,.1],'z_offsets_mm':[-40,-20,-5,0],
    'checks':64,'note':'Small rigid offsets, not a model of print tolerances or deformation.'}

# Pre-thread ties in the empty shell. Check both the short feed and a direct
# path from the open bottom to the emerging tail, not merely a finished loop.
front=p['battery_center'][1]-12.5
tie_z=p['tie_tunnel_z']+p['tie_slot_height']/2
reach_start=front+p['tie_eyelet_length']+1
reach_end=front+24
base=p['carrier_z']+p['carrier_thickness']
report['battery_tie_access']=[]
for x in p['battery_saddles']:
    feed_start=front-10;feed_end=reach_start+3
    feed=box([2.5,feed_end-feed_start,.8],[x,(feed_start+feed_end)/2,tie_z])
    reach=box([2.5,reach_end-reach_start,tie_z+.4-base],[x,(reach_start+reach_end)/2,(base+tie_z+.4)/2])
    for name,envelope in [('front feed',feed),('tail access from below',reach)]:
        assert overlap(envelope,meshes['shell'])<.001,('battery tie',x,name)
    report['battery_tie_access'].append({'cradle_x_mm':x,'closed_feed_length_mm':p['tie_eyelet_length'],
        'slot_mm':[p['tie_slot_width'],p['tie_slot_height']],
        'checks':['2.5 x 0.8 mm straight tie feed','open vertical access to tail behind eyelet'],
        'stage':'Empty shell, before boards and battery; rigid envelopes, not a finger or flexible-tie simulation.'})

report['other_insertion_paths']=[]
for label,parts,obstacles in [
    ('Carrier with SCD30',['carrier','scd30'],['shell','feather_frame','feather','light','rtc','battery']),
    ('Battery before carrier closure',['battery'],['shell','feather_frame','feather','light','rtc'])]:
    moving=trimesh.boolean.union([meshes[n] for n in parts],engine='manifold')
    max_volume=0
    for dz in np.linspace(-40,0,81):
        candidate=moving.copy();candidate.apply_translation([0,0,dz])
        for name in obstacles:
            volume=overlap(candidate,meshes[name])
            assert volume<.001,(label,dz,name,volume)
            max_volume=max(max_volume,volume)
    report['other_insertion_paths'].append({'assembly':label,'axis':'+Z','poses':81,'step_mm':.5,
        'checks':81*len(obstacles),'max_intersection_mm3':round(max_volume,6),
        'note':'Loose wires/ties are moved aside by the assembler and are not swept.'})

def shaft(point,direction,diameter=3,length=100):
    # Bearing plane is just beyond the tool tip. Shaft goes AWAY from the screw.
    m=trimesh.creation.cylinder(radius=diameter/2,height=length,sections=24)
    m.apply_translation([0,0,-length/2-.05])
    m.apply_transform(trimesh.geometry.align_vectors([0,0,1],direction))
    m.apply_translation(point)
    return m

for key,board in [('light','veml7700'),('rtc','rtc')]:
    for i in (range(2) if key=='rtc' else p['board_screw_indices']):
        x,y,_=boards[board]['holes'][i]
        point=np.array(p[key+'_origin'])+([-y,x,-.5] if key=='rtc' else [x,y,0])
        tool=shaft(point,[0,0,1])
        # The roof boards precede battery installation. Check with the Feather in place too.
        for other in ['shell','feather_frame','feather','light','rtc']:
            assert overlap(tool,meshes[other])<.001,(key,i,'tool hits',other)
        report['screwdriver_checks'].append({'screw':f'{key}-{i}','shaft_diameter_mm':3,'shaft_length_mm':100,'approach':'straight from open bottom; battery and carrier absent'})
for i,xy in enumerate(p['case_mounts']):
    tool=shaft([*xy,p['carrier_z']],[0,0,1],4)
    for other in meshes:assert overlap(tool,meshes[other])<.001,('closure tool',i,other)
    report['screwdriver_checks'].append({'screw':f'closure-{i}','shaft_diameter_mm':4,'shaft_length_mm':100,'approach':'straight from below, assembled device'})
for i in p['board_screw_indices']:
    x,y,_=boards['feather']['holes'][i]
    tool=shaft(np.array(p['feather_origin'])+[x,0,-y],[0,1,0])
    for other in ['feather_frame','feather']:assert overlap(tool,meshes[other])<.001,('outside Feather screw',i,other)
    report['screwdriver_checks'].append({'screw':f'feather-{i}','shaft_diameter_mm':3,'shaft_length_mm':100,'approach':'from display face, frame and board outside case'})
report['limitations']=['Sampled nominal rigid-motion check, not a continuous clearance proof.',
    'Print tolerance, flex, omitted small components, real screw heads, hands and driver handles need a physical pilot.',
    'Both Feather leads must be unplugged before withdrawal; cable deformation is not simulated.',
    'SCD30 is screwed to its carrier outside the housing.']
(CAD/'generated/assembly-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
