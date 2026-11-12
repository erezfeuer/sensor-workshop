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


def nut(point):
    # Annular hex prism; 5.5 mm across flats and 2.4 mm thick.
    outer = np.array([[np.cos(a), np.sin(a)] for a in np.arange(6) * np.pi / 3]) * (5.5 / np.sqrt(3))
    inner = outer / np.linalg.norm(outer, axis=1)[:, None] * 1.6
    vertices = np.vstack([np.c_[outer, np.zeros(6)], np.c_[inner, np.zeros(6)],
                          np.c_[outer, np.full(6, 2.4)], np.c_[inner, np.full(6, 2.4)]])
    faces = []
    for i in range(6):
        j = (i + 1) % 6
        for a, b, c, d in [(i, j, j+12, i+12), (i+6, i+18, j+18, j+6),
                            (i, i+6, j+6, j), (i+12, j+12, j+18, i+18)]:
            faces.extend([[a,b,c], [a,c,d]])
    m = trimesh.Trimesh(vertices=vertices, faces=faces)
    m.apply_translation(point)
    return m


def main():
    scene = load_scene()
    # Open the simplified coin holder so the independently selectable cell is visible from below.
    top = trimesh.intersections.slice_mesh_plane(scene['rtc'], [0,0,1], [0,0,44], cap=True)
    holder = trimesh.creation.annulus(r_min=6.05,r_max=6.5,height=3.2,sections=36)
    holder.apply_translation([88.7,40.795,42.4])
    scene['rtc'] = trimesh.util.concatenate([top,holder])
    items = []

    def add(key, label, group, mesh, color, delta, note):
        data = np.concatenate([mesh.triangles, np.repeat(mesh.face_normals[:, None, :], 3, axis=1)], axis=2).astype('<f4')
        items.append(dict(id=key, label=label, group=group, color=color, delta=delta,
                          note=note, bounds=mesh.bounds.tolist(), count=len(mesh.faces)*3,
                          data=base64.b64encode(data.tobytes()).decode('ascii')))

    defs = [
        ('base', 'Upper housing', 'Printed enclosure', [0,0,0], '112 × 84 mm; battery cradles, PCB bosses and cable slots.'),
        ('lid', 'Lid + optical well', 'Printed enclosure', [0,0,70], 'Top opening exposes the VEML7700. Opaque well reduces internal light leakage.'),
        ('shade', 'Sensor shade roof', 'Printed enclosure', [0,0,-22], '3.6 mm air gap below the electronics floor; offset cable openings.'),
        ('pod', 'Vented CO₂ sensor tray', 'Printed enclosure', [0,0,-66], 'Offset inner and outer vents shade the sensor and allow diffusion.'),
        ('feather', 'ESP32-S3 Reverse TFT Feather', 'Electronics', [0,-34,12], 'Adafruit 5691; screen and buttons face forward; USB-C faces left.'),
        ('light', 'VEML7700 light sensor', 'Electronics', [0,0,47], 'Adafruit 4162, flat STEMMA QT revision; mounted below the lid.'),
        ('rtc', 'DS3231 RTC + coin-cell holder', 'Electronics', [35,0,20], 'Adafruit 5188; two mounting holes. Holder envelope includes the CR1220.'),
        ('scd30', 'SCD30 CO₂ / temperature / humidity', 'Electronics', [0,0,-48], 'Adafruit 4867; allow clearance for pins below the PCB.'),
        ('battery', 'Protected 18650 battery pack', 'Electronics', [0,24,30], 'Local Israel purchase: Ø20 × 72 mm design envelope; prewired JST-PH.'),
        ('switch', 'Prewired battery switch', 'Electronics', [-30,0,15], 'Adafruit 3064: body size is provisional. Measure before final printing.'),
        ('wires', 'Cable routing guides', 'Wiring', [0,0,0], 'Illustrative routes only. Hidden while exploded; cables do not stretch.'),
    ]
    for key, label, group, delta, note in defs:
        add(key, label, group, scene[key], COLORS[key], delta, note)
    # Display is a submesh of the Feather, controlled by that board's checkbox.
    add('display', 'Display face', '_attached', scene['display'], COLORS['display'], [0,-34,12], '')
    for i, m in enumerate(sorted(scene['feet'].split(), key=lambda m: tuple(m.centroid[:2]))):
        x, y = m.centroid[:2]
        name = ('Left' if x<56 else 'Right') + (' front' if y<42 else ' rear')
        add(f'foot-{i}', name+' foot', 'Printed enclosure', m, COLORS['feet'], [-24 if x<56 else 24,-10 if y<42 else 10,-32], 'Printed foot with captive M3 nut and locating peg.')
    for i, m in enumerate(sorted(scene['buttons'].split(), key=lambda m: -m.centroid[2])):
        add(f'button-{i}', f'Button plunger {i+1}', 'Printed enclosure', m, COLORS['buttons'], [0,-54,0], 'Captured plunger; nominal 0.2 mm gap to the PCB switch. Check stroke physically.')
    for i, p in enumerate(PARAMS['leg_mounts']):
        add(f'case-bolt-{i}', f'Lid / foot bolt {i+1} · M3 × 50', 'Fasteners', screw([*p,78.4],50,3), '#a3adb4', [0,0,96], 'Simplified pan-head screw; length measured below the head.')
        delta=[-24 if p[0]<56 else 24,-10 if p[1]<42 else 10,-32]
        add(f'foot-nut-{i}', f'Foot captive nut {i+1} · M3', 'Fasteners', nut([*p,31.4]), '#a3adb4', delta, 'Nut pocket is 5.7 mm across flats; verify on coupon.')
    for i, p in enumerate(PARAMS['pod_mounts']):
        add(f'pod-bolt-{i}', f'Sensor tray bolt {i+1} · M3 × 25', 'Fasteners', screw([*p,36.4],25,3), '#a3adb4', [0,0,28], 'Clamps tray, shade and spacers to the main floor.')
        add(f'pod-nut-{i}', f'Tray captive nut {i+1} · M3', 'Fasteners', nut([*p,12]), '#a3adb4', [0,0,-66], 'Insert from underside of the tray; retained by the bolt.')
    boards=json.loads((CAD/'generated/boards.json').read_text())
    for board, key, delta in [('feather','feather',[0,-34,12]),('scd30','scd30',[0,0,-48]),('rtc','rtc',[35,0,20]),('veml7700','light',[0,0,47])]:
        origin=np.array(PARAMS[key+'_origin'])
        for i, (x,y,d) in enumerate(boards[board]['holes']):
            direction=(0,0,-1)
            point=origin+np.array([x,y,1.6])
            if key=='feather':
                point=origin+np.array([x,1.6,-y]);direction=(0,-1,0)
            if key=='light':
                point=origin+np.array([x,y,0]);direction=(0,0,1)
            if key=='rtc':point[2]+=.5
            add(f'{key}-screw-{i}', f'{key.upper()} screw {i+1} · M2 × 6', 'Fasteners', screw(point,6,2,direction), '#a3adb4', delta, 'Printed pilot hole; pre-thread and verify before student assembly.')
    for i,x in enumerate([32,80]):
        # Flexible strap loop is an assembly guide; keep slot fit distinct from battery envelope.
        mesh=trimesh.util.concatenate([box([8,1,24],[x,53,46]),box([8,1,24],[x,78.5,46]),box([8,25.5,1],[x,65.75,61]),box([8,25.5,1],[x,65.75,33.2])])
        add(f'strap-{i}', f'Battery strap {i+1}', 'Wiring', mesh, '#6e7580', [0,24,30], '8 mm hook-and-loop strap; schematic shape, conforms around the pack.')
    # A separate coin illustration lets the user inspect the local backup-cell purchase.
    add('coin', 'CR1220 backup cell', 'Electronics', cylinder(6,2,[88.7,40.795,42.1]), '#c1c7cb', [35,0,9], 'Local 3 V non-rechargeable CR1220; shown inside the RTC holder envelope.')
    for i,p in enumerate(boards['rtc']['holes']):
        # Thin M2 washer illustration, with an actual centre hole.
        mesh=trimesh.creation.annulus(r_min=1.1,r_max=2.5,height=.5,sections=24)
        mesh.apply_translation(np.array(PARAMS['rtc_origin'])+np.array([p[0],p[1],1.85]))
        add(f'rtc-washer-{i}', f'RTC washer {i+1} · M2', 'Fasteners', mesh, '#b9c0c2', [35,0,20], 'Spreads the M2 head load around the board’s 3 mm mounting hole.')
    meta=dict(version='0.1', units='mm', parts=items,
              source_sha256=hashlib.sha256((CAD/'sensor-workshop.scad').read_bytes()+(CAD/'parameters.scad').read_bytes()).hexdigest())
    template=(CAD/'viewer/template.html').read_text()
    result=template.replace('__MODEL_JSON__',json.dumps(meta,separators=(',',':')))
    result=result.replace('__VIEWER_JS__',(CAD/'viewer/viewer.js').read_text())
    path=CAD/'model.html';path.write_text(result)
    print(f'{path.name}: {len(items)-1} selectable components, {len(result)/1024/1024:.1f} MB; no external dependencies')


if __name__=='__main__':main()
