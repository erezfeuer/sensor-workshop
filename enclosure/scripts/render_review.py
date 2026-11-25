#!/usr/bin/env python3
"""Software-render the exported CAD meshes and produce measured sections/PDF.

No OpenGL is required. Geometry comes from OpenSCAD's exported solids.
"""
import json
import os
import re
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "sensor-workshop-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.path import Path as PlotPath

ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / "enclosure"
RENDERS = CAD / "renders"
PARAMS = {}
for line in (CAD / "parameters.scad").read_text().splitlines():
    match = re.match(r"(\w+)\s*=\s*(.*?);", line)
    if match:
        PARAMS[match[1]] = json.loads(match[2])
COLORS = {"shell":"#dedfd8", "carrier":"#4f7777", "feather_frame":"#d39b59", "feather":"#2e6054", "scd30":"#bb975b", "rtc":"#817ba6", "light":"#527b95", "battery":"#5b91bd", "display":"#41c1bf"}
COLORS.update({'mount_tie':'#394749','mount_pole':'#9aa7a0','mount_pad':'#4e5458'})
if (CAD/"generated/cable-metadata.json").exists():
    COLORS.update({c["mesh"]:c["color"] for c in json.loads((CAD/"generated/cable-metadata.json").read_text())})

BG = np.array([247,248,245], dtype=np.uint8)
FONT = font_manager.findfont("DejaVu Sans")


def load_scene():
    scene = {p.stem: trimesh.load_mesh(p) for p in (CAD/"generated/scene").glob("*.stl")}
    # Display face overlay, aligned to the active-area coordinates from Eagle.
    x,y,z = PARAMS["feather_origin"]
    panel=trimesh.creation.box(extents=[24.9,0.04,14.8])
    panel.apply_translation([x+12.891+24.9/2,y-1.94,z-3.903-14.8/2])
    scene["display"] = panel
    return scene


def variant(source, kind):
    meshes={k:v.copy() for k,v in source.items()}
    if kind=="open":meshes.pop("shell")
    if kind=="exploded":
        for key,delta in {"carrier":[0,0,-46],"scd30":[0,0,-65],"feather":[0,0,-80],"feather_frame":[0,0,-80],"display":[0,0,-80],"light":[0,0,-18],"rtc":[25,0,-18],"battery":[0,22,-22]}.items():
            meshes[key].apply_translation(delta)
        meshes={k:v for k,v in meshes.items() if not k.startswith("cable_")}
    if kind=="feather_install":
        meshes={k:v for k,v in meshes.items() if k not in ("carrier","scd30") and not k.startswith("cable_")}
        for key in ("feather","feather_frame","display"):meshes[key].apply_translation([0,0,-65])
    if kind.startswith("section"):
        axis,cut = (1,33) if kind=="section_front" else (0,43)
        normal=np.eye(3)[axis]
        meshes={k:trimesh.intersections.slice_mesh_plane(m,normal,normal*cut) for k,m in meshes.items()}
        meshes={k:m for k,m in meshes.items() if len(m.faces)}
    return meshes


def rasterize(meshes, title, subtitle, out, eye=(-1,-1,0.85)):
    width,height=1600,1200
    direction=np.array(eye,dtype=float); direction/=np.linalg.norm(direction)
    right=np.cross([0,0,1],direction); right/=np.linalg.norm(right)
    up=np.cross(direction,right)
    basis=np.array([right,up,direction]).T
    vertices=np.vstack([m.vertices for m in meshes.values()])@basis
    lo,hi=vertices[:,:2].min(0),vertices[:,:2].max(0)
    scale=min(1300/(hi[0]-lo[0]),880/(hi[1]-lo[1]))
    center=(lo+hi)/2
    image=np.empty((height,width,3),dtype=np.uint8);image[:]=BG
    zbuffer=np.full((height,width),-np.inf)
    light=np.array([-0.5,-0.7,1.4]);light/=np.linalg.norm(light)
    for name,mesh in meshes.items():
        base=np.array(matplotlib.colors.to_rgb(COLORS[name]))*255
        projected=mesh.vertices@basis
        projected[:,0]=(projected[:,0]-center[0])*scale+width/2
        projected[:,1]=-(projected[:,1]-center[1])*scale+height/2+15
        normals=mesh.face_normals
        for index,face in enumerate(mesh.faces):
            if np.dot(normals[index],direction)<-0.0001:
                continue
            tri=projected[face]
            x0,x1=max(0,int(np.floor(tri[:,0].min()))),min(width-1,int(np.ceil(tri[:,0].max())))
            y0,y1=max(0,int(np.floor(tri[:,1].min()))),min(height-1,int(np.ceil(tri[:,1].max())))
            if x1<x0 or y1<y0:continue
            a,b,c=tri
            den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-8:continue
            xx,yy=np.meshgrid(np.arange(x0,x1+1)+0.5,np.arange(y0,y1+1)+0.5)
            wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
            wc=1-wa-wb
            zz=wa*a[2]+wb*b[2]+wc*c[2]
            depth=zbuffer[y0:y1+1,x0:x1+1]
            keep=(wa>=-1e-7)&(wb>=-1e-7)&(wc>=-1e-7)&(zz>depth)
            shade=0.62+0.38*max(0,np.dot(normals[index],light))
            region=image[y0:y1+1,x0:x1+1]
            region[keep]=(base*shade).astype(np.uint8)
            depth[keep]=zz[keep]
    result=Image.fromarray(image)
    draw=ImageDraw.Draw(result)
    draw.text((65,40),title,font=ImageFont.truetype(FONT,38),fill="#253f44")
    draw.text((66,96),subtitle,font=ImageFont.truetype(FONT,21),fill="#526568")
    draw.line((65,1125,1535,1125),fill="#c8d1cc",width=2)
    draw.text((65,1145),f"Sensor Workshop  |  v{PARAMS['enclosure_version']} · {PARAMS['light_sensor'].upper()} QT  |  CAD prototype — fit tests pending",font=ImageFont.truetype(FONT,19),fill="#526568")
    result.save(out)
    print("RENDER",out.name,flush=True)


def section_plot(ax, meshes, cut, title, dimensions=True):
    ax.set_title(title,fontsize=12,loc="left",pad=12)
    for key in ("shell","carrier","feather_frame","feather","display","scd30","rtc","light","battery"):
        mesh=meshes.get(key)
        if mesh is None:continue
        section=mesh.section(plane_origin=[cut,0,0],plane_normal=[1,0,0])
        if section is None:continue
        polys=[np.asarray(p)[:,[1,2]] for p in section.discrete if len(p)>3]
        polys.sort(key=lambda p:abs(np.sum(p[:,0]*np.roll(p[:,1],1)-p[:,1]*np.roll(p[:,0],1))),reverse=True)
        previous=[]
        for poly in polys:
            depth=sum(PlotPath(p).contains_point(poly[0]) for p in previous)
            color="white" if depth%2 else COLORS[key]
            ax.fill(poly[:,0],poly[:,1],color=color,edgecolor="#334c50",linewidth=0.55,
                    hatch="///" if key in ("shell","carrier","feather_frame") and depth%2==0 else None)
            previous.append(poly)
    ax.set_aspect("equal");ax.set_xlim(-7,82);ax.set_ylim(-7,75)
    ax.set_xlabel("Front ← Y (mm) → Rear");ax.set_ylabel("Z above desk (mm)")
    ax.grid(alpha=0.12);ax.set_axisbelow(True)
    if not dimensions:return
    for z,label in [(24,"Carrier"),(8,"Skirt edge")]:
        ax.annotate(label,xy=(66,z),xytext=(70,z+3),fontsize=7,
                    arrowprops=dict(arrowstyle="-",lw=.6,color="#526568"),color="#526568")
    ax.annotate("60.8 mm",xy=(77,0),xytext=(77,60.8),ha="center",va="center",rotation=90,
                fontsize=8,arrowprops=dict(arrowstyle="<->",lw=.8))


def drawings(scene):
    plt.rcParams.update({"font.size":9,"font.family":"DejaVu Sans"})
    fig,axes=plt.subplots(1,2,figsize=(13.5,8.8))
    section_plot(axes[0],scene,42.7,"SECTION A–A  ·  X = 42.7 mm")
    section_plot(axes[1],scene,68.205,"SECTION B–B  ·  X = 68.205 mm")
    axes[0].annotate("18650 envelope\nØ20 × 72",xy=(50,41),xytext=(48,69),fontsize=9,arrowprops=dict(arrowstyle="->",lw=.8))
    axes[0].annotate("SCD30 faces down\nOpen below",xy=(30,14),xytext=(3,2),fontsize=8,arrowprops=dict(arrowstyle="->",lw=.8))
    boards=json.loads((CAD/"generated/boards.json").read_text())
    optic_y=PARAMS['light_origin'][1]+boards[PARAMS['light_sensor']]['optic'][1]
    axes[0].annotate("Top light aperture",xy=(optic_y,58.4),xytext=(0,68),fontsize=8,arrowprops=dict(arrowstyle="->",lw=.8))
    axes[1].annotate("RTC / CR1220",xy=(PARAMS["rtc_origin"][1]+12.7,51),xytext=(1,67),fontsize=8,arrowprops=dict(arrowstyle="->",lw=.8))
    fig.suptitle("True CAD cross-sections",fontsize=20,x=.055,ha="left")
    fig.text(.055,.055,"The cuts are taken from the exported solids. Parts outside each cut plane are not projected into it.\nPrinted plastic is pale grey/teal. Pack dimensions are a design envelope; local battery, connector and finger access require a pilot check.",fontsize=9,color="#526568")
    fig.subplots_adjust(top=.86,bottom=.14,wspace=.27)
    fig.savefig(RENDERS/"sections.png",dpi=170)
    fig.savefig(CAD/"sections.pdf")
    plt.close(fig)

    boards=json.loads((CAD/"generated/boards.json").read_text())
    fig,axes=plt.subplots(2,2,figsize=(13.5,9))
    names={"feather":"Adafruit 5691 — Reverse TFT Feather", "scd30":"Adafruit 4867 — SCD30", "veml7700":"Adafruit 4162 — VEML7700 QT", "tsl2591":"Adafruit 1980 — TSL2591 QT", "rtc":"Adafruit 5188 — DS3231 QT"}
    for ax,key in zip(axes.flat,('feather','scd30',PARAMS['light_sensor'],'rtc')):
        b=boards[key]
        w,h=b["size"]
        ax.add_patch(plt.Rectangle((0,0),w,h,facecolor="#edf2ef",edgecolor="#355854",lw=1))
        for i,(x,y,d) in enumerate(b["holes"],1):
            ax.add_patch(plt.Circle((x,y),d/2,facecolor="white",edgecolor="#355854"))
            ax.text(x+(3 if x<w/2 else -3),y,f"{i}",ha="left" if x<w/2 else "right",va="center",fontsize=8)
        ax.plot(0,0,"+",color="#ae583f",ms=10)
        ax.set_title(names[key],loc="left",fontsize=11)
        ax.set_aspect("equal");ax.set_xlim(-3,w+3);ax.set_ylim(-3,h+3)
        ax.set_xlabel("Eagle X (mm)");ax.set_ylabel("Eagle Y (mm)");ax.grid(alpha=.15)
        rows="\n".join(f"{i}: ({x:g}, {y:g})  Ø{d:g}" for i,(x,y,d) in enumerate(b["holes"],1))
        ax.text(1.03,.9,f"PCB {w:g} × {h:g}\n\n{rows}",transform=ax.transAxes,va="top",fontsize=8)
    fig.suptitle("Mounting coordinates from the manufacturer PCB files",fontsize=18,x=.055,ha="left")
    fig.text(.055,.03,"Coordinates are unmirrored Eagle top-view coordinates; verify received board revision. Outline rectangles show overall extents.\nFeather: two Ø2.5 mm holes and two Ø2.2 mm holes. RTC: two mounting holes, not four. Source pins and hashes: hardware/reference/manifest.json.",fontsize=9,color="#526568")
    fig.subplots_adjust(left=.06,right=.82,bottom=.12,top=.88,wspace=.9,hspace=.55)
    fig.savefig(RENDERS/"mounting-drawings.png",dpi=170)
    fig.savefig(CAD/"mounting-drawings.pdf")
    plt.close(fig)


def feather_mount_drawing(scene):
    """Orientation reference and a true section through the antenna-end screw."""
    rasterize({'feather_frame':scene['feather_frame']},
        f"Reinforced Feather frame · v{PARAMS['enclosure_version']}",
        'Read the crossbar: USB arrow points left · SCREEN SIDE faces you',
        RENDERS/'feather-frame.png',eye=(-.4,-1,.6))
    fig,axes=plt.subplots(1,2,figsize=(13.5,8.8),gridspec_kw={'width_ratios':[1.1,1]})
    axes[0].imshow(np.asarray(Image.open(RENDERS/'feather-frame.png'))[145:1110,110:1510])
    axes[0].axis('off')
    axes[0].set_title('Mounting faces toward you · crossbar at the bottom',loc='left',fontsize=11,pad=12)
    axes[0].text(.5,-.06,'USB follows the engraved arrow. SCREEN SIDE faces you.\nSeat both chamfered locating pins before fitting the two screws.',
        transform=axes[0].transAxes,ha='center',va='top',fontsize=10,color='#334c50')
    boards=json.loads((CAD/'generated/boards.json').read_text())
    hole=boards['feather']['holes'][3]
    cut=PARAMS['feather_origin'][0]+hole[0]
    z=PARAMS['feather_origin'][2]-hole[1]
    front=PARAMS['feather_origin'][1]+PARAMS['pcb_thickness']
    ax=axes[1]
    section_plot(ax,{k:scene[k] for k in ('feather_frame','feather')},cut,
        f'True screw-axis section · X = {cut:g} mm',dimensions=False)
    ax.set(xlim=(3.4,18.2),ylim=(30.5,43),xlabel='PCB / front ← Y (mm) → rear face',ylabel='Z above desk (mm)')
    ax.add_patch(plt.Rectangle((front,z-1.6),16.5-front,3.2,fill=False,
        edgecolor='#9e483a',linewidth=1.2,linestyle='--',label='Previous Ø3.2 mm post outline'))
    ax.annotate('',xy=(front,32.2),xytext=(front+PARAMS['feather_pilot_depth'],32.2),
        arrowprops=dict(arrowstyle='<->',lw=1,color='#334c50'))
    ax.text(front+PARAMS['feather_pilot_depth']/2,31.4,'6 mm blind pilot · Ø1.8 unchanged',ha='center',fontsize=9)
    ax.annotate('Taper and broad root\nmerge into the upright',xy=(10,39.2),xytext=(11,41.4),
        ha='center',fontsize=9,arrowprops=dict(arrowstyle='->',lw=.8))
    ax.annotate('PCB',xy=(5.1,39.2),xytext=(4.9,42),ha='center',fontsize=9,
        arrowprops=dict(arrowstyle='->',lw=.8))
    ax.annotate('4.6 mm solid\nbehind the pilot',xy=(14.1,z),xytext=(14.8,33),ha='center',fontsize=9,
        arrowprops=dict(arrowstyle='->',lw=.8))
    ax.legend(loc='lower center',bbox_to_anchor=(.5,-.26),frameon=False,fontsize=8)
    fig.suptitle(f"Feather frame v{PARAMS['enclosure_version']} — reinforcement and orientation",fontsize=19,x=.05,ha='left')
    fig.text(.05,.065,'Reprint 03-feather-frame.stl from v0.5 or v0.6. Flat rear face on the bed; start with five perimeters at 0.4 mm nozzle / 0.2 mm layers.\n'
        'Old hole centres and contact diameters retained; LED reliefs and Ø6.4 mm roots keep the board clear and support the screws.\n'
        'The section shows actual CAD geometry, not a strength simulation. Gentle repeated fitting/removal still needs a physical trial.',
        fontsize=9,color='#526568')
    fig.subplots_adjust(left=.04,right=.97,top=.85,bottom=.23,wspace=.2)
    fig.savefig(RENDERS/'feather-mounting.png',dpi=170)
    fig.savefig(CAD/'feather-mounting.pdf')
    plt.close(fig)


def light_sensor_drawing(scene):
    """Board comparison and true roof section for the selected light sensor."""
    boards=json.loads((CAD/'generated/boards.json').read_text())
    board=boards[PARAMS['light_sensor']]
    ox,oy=board['optic']
    fig,axes=plt.subplots(1,2,figsize=(13.5,8))
    ax=axes[0]
    ax.add_patch(plt.Rectangle((0,0),*board['size'],fc='#e0ebe8',ec='#355854'))
    for x,y,d in board['holes']:
        ax.add_patch(plt.Circle((x,y),d/2,fc='white',ec='#355854'))
    for c in board['component_envelopes']:
        ax.add_patch(plt.Rectangle(c['xy_min'],*c['size'][:2],fc='#b5b7af',ec='#777b70',lw=.6))
        ax.text(c['xy_min'][0],c['xy_min'][1]+c['size'][1]+.2,c['name'],fontsize=6)
    for x in (2.667,22.733):
        ax.add_patch(plt.Rectangle((x-2.3,8.89-3.1),4.6,6.2,fc='#f4efe0',ec='#9f967f'))
    old=boards['veml7700']['optic']
    ax.add_patch(plt.Rectangle((old[0]-6,old[1]-3),12,6,fill=False,ec='#ae785a',ls='--',lw=1.5,label='VEML7700 roof opening'))
    ax.add_patch(plt.Rectangle((ox-6,oy-3),12,6,fill=False,ec='#176b79',lw=2,label='Selected roof opening'))
    ax.plot(ox,oy,'+',color='#176b79',ms=12)
    ax.annotate(f"{PARAMS['light_sensor'].upper()} optical centre\n({ox:g}, {oy:g}) mm",xy=(ox,oy),xytext=(11,-5),
        fontsize=9,ha='center',arrowprops=dict(arrowstyle='->',lw=.8))
    ax.set(xlim=(-2,28),ylim=(-7,21),aspect='equal',xlabel='PCB X (mm)',ylabel='PCB Y (mm)',title='Same mounting holes and QT sockets')
    ax.legend(loc='upper center',fontsize=8);ax.grid(alpha=.15)
    section_plot(axes[1],{k:scene[k] for k in ('shell','light')},PARAMS['light_origin'][0]+ox,'True section through optical centre')
    axes[1].set(xlim=(17,37),ylim=(52,64))
    axes[1].annotate('Flared roof opening',xy=(PARAMS['light_origin'][1]+oy,60.8),xytext=(18,63),
        fontsize=9,arrowprops=dict(arrowstyle='->',lw=.8))
    axes[1].annotate('Light well with component reliefs',xy=(PARAMS['light_origin'][1]+oy-3.4,57.7),xytext=(18,52.5),
        fontsize=8,arrowprops=dict(arrowstyle='->',lw=.8))
    fig.suptitle(f"Light-sensor fit · Adafruit {PARAMS['light_sensor'].upper()} QT · enclosure v{PARAMS['enclosure_version']}",fontsize=18,x=.055,ha='left')
    fig.text(.055,.04,'Adafruit QT board only. Small-component boxes use Eagle pad/body bounds and a conservative 2 mm height.\nReliefs add 0.3 mm clearance; they are not extra printed parts. Verify the received board and light response on the pilot.',fontsize=9,color='#526568')
    fig.subplots_adjust(left=.07,right=.95,bottom=.17,top=.87,wspace=.25)
    fig.savefig(RENDERS/'light-sensor-fit.png',dpi=170)
    fig.savefig(CAD/'light-sensor-fit.pdf')
    plt.close(fig)


def battery_tie_drawing(scene):
    """True sections, oriented roof-down as held while threading the ties."""
    from battery_ties import feed_centerline, installed_centerline
    fig,axes=plt.subplots(1,2,figsize=(12,6.8))
    x=PARAMS['battery_saddles'][0]
    section_plot(axes[0],{'shell':scene['shell']},x,'1 · FEED THROUGH THE EMPTY SHELL',dimensions=False)
    section_plot(axes[1],{k:scene[k] for k in ['shell','battery']},x,'2 · FIT BATTERY, THEN CLOSE THE TIE',dimensions=False)
    for ax in axes:
        ax.set_xlim(30,67);ax.set_ylim(27,63);ax.invert_yaxis()
        ax.set_ylabel('Assembly Z (mm) · roof down')
    top=PARAMS['tie_tunnel_z']+PARAMS['tie_slot_height']/2
    route=feed_centerline(PARAMS)
    axes[0].plot(route[:,0],route[:,1],color='#287a77',lw=2.5)
    axes[0].annotate('',xy=(45,top),xytext=(32,top),arrowprops=dict(arrowstyle='->',color='#287a77',lw=2))
    axes[0].annotate('Front eyelet',xy=(40,top),xytext=(31,48),fontsize=9,arrowprops=dict(arrowstyle='->',lw=.8))
    axes[0].annotate('4 mm-radius\ncurved return',xy=(60.5,53.3),xytext=(47,60),fontsize=9,arrowprops=dict(arrowstyle='->',lw=.8))
    axes[0].annotate('Tail emerges toward\nthe open underside',xy=(61,43.5),xytext=(39,34),fontsize=9,color='#287a77',arrowprops=dict(arrowstyle='->',color='#287a77',lw=1.4))
    route=installed_centerline(PARAMS);route=np.vstack([route,route[0]])
    axes[1].plot(route[:,0],route[:,1],color='#394749',lw=2)
    axes[1].text(50,40,'Battery',ha='center',fontsize=10,color='white')
    axes[1].annotate('Second guide',xy=(61,49),xytext=(48,60),fontsize=9,arrowprops=dict(arrowstyle='->',lw=.8))
    axes[1].annotate('',xy=(50,46),xytext=(50,33),arrowprops=dict(arrowstyle='->',color='#a8583d',lw=2))
    axes[1].text(31,29,'Tie presses pack toward the cradle',fontsize=8,color='#a8583d')
    fig.suptitle('Battery ties: guided return and two anchoring points',x=.055,ha='left',fontsize=18)
    fig.text(.055,.035,'Roof-down sections at X = 23 mm. The guide bridges join the roof through side cheeks outside this cut.\nRoutes are nominal illustrations, not a friction or flexible-tie simulation. Test feeding before installing electronics.',fontsize=9,color='#526568')
    fig.subplots_adjust(left=.075,right=.97,top=.86,bottom=.17,wspace=.24)
    fig.savefig(RENDERS/'battery-tie-access.png',dpi=170)
    fig.savefig(CAD/'battery-tie-access.pdf')
    plt.close(fig)


def mounting_guide_drawing(scene):
    fig,axes=plt.subplots(1,2,figsize=(12,6.8))
    p=PARAMS;high=p['mount_band_z']+p['mount_groove_width']/2
    lip=high+p['mount_groove_bevel']+p['mount_guide_land']/2
    for z,color,label in [(p['mount_band_z'],'#287a77','Groove floor'),(lip,'#a8583d','Raised shoulder')]:
        section=scene['shell'].section(plane_origin=[0,0,z],plane_normal=[0,0,1])
        for i,points in enumerate(section.discrete):
            axes[0].plot(points[:,0],points[:,1],color=color,lw=2,label=label if i==0 else None)
    axes[0].set_xlim(-3,12);axes[0].set_ylim(-3,12);axes[0].set_aspect('equal')
    axes[0].set_title('FULL CORNER ARC + 2.5 mm RETURNS',loc='left',fontsize=12)
    axes[0].set_xlabel('X (mm)');axes[0].set_ylabel('Y (mm)');axes[0].legend(loc='upper right',fontsize=8)
    section=scene['shell'].section(plane_origin=[0,p['corner_radius'],0],plane_normal=[0,1,0])
    polys=[points[:,[0,2]] for points in section.discrete if len(points)>3]
    polys.sort(key=lambda poly:abs(np.sum(poly[:,0]*np.roll(poly[:,1],1)-poly[:,1]*np.roll(poly[:,0],1))),reverse=True)
    previous=[]
    for poly in polys:
        depth=sum(PlotPath(old).contains_point(poly[0]) for old in previous)
        axes[1].fill(poly[:,0],poly[:,1],color='white' if depth%2 else COLORS['shell'],edgecolor='#334c50',lw=.7)
        previous.append(poly)
    axes[1].set_xlim(-5,5);axes[1].set_ylim(23,39);axes[1].set_aspect('equal')
    axes[1].set_title('RAISED SHOULDERS · WALL KEPT INTACT',loc='left',fontsize=12)
    axes[1].set_xlabel('X (mm) · outside at left');axes[1].set_ylabel('Assembly Z (mm)')
    axes[1].annotate('',xy=(-3.3,high),xytext=(-3.3,high-p['mount_groove_width']),arrowprops=dict(arrowstyle='<->',lw=1))
    axes[1].text(-3.6,p['mount_band_z'],'6 mm',rotation=90,va='center',ha='right')
    axes[1].annotate('',xy=(-p['mount_groove_depth'],lip),xytext=(0,lip),arrowprops=dict(arrowstyle='<->',lw=1))
    axes[1].text(-2.6,lip+1.3,'1.6 mm',fontsize=9)
    for ax in axes:ax.grid(alpha=.12);ax.set_axisbelow(True)
    fig.suptitle('External tie: four identical corner guides',x=.055,ha='left',fontsize=18)
    fig.text(.055,.035,'Sections taken from the exported shell. Both shoulders follow the complete 90-degree corner and short straight returns.\nThe nominal 2.4 mm wall is not cut thinner. Guide flanks are 45 degrees; overall width/depth including shoulders is 95.2 × 69.2 mm.',fontsize=9,color='#526568')
    fig.subplots_adjust(left=.075,right=.97,top=.86,bottom=.17,wspace=.45)
    fig.savefig(RENDERS/'mounting-guide-details.png',dpi=170)
    fig.savefig(CAD/'mounting-guide-details.pdf')
    plt.close(fig)


if __name__ == "__main__":
    RENDERS.mkdir(exist_ok=True)
    scene=load_scene()
    variants=[("assembled",f"{PARAMS['light_sensor'].upper()} QT prototype · v{PARAMS['enclosure_version']}","95.2 × 69.2 × 60.8 mm including corner guides · three printed pieces"),
              ("underside","Downward-facing sensor","Open underside · shallow skirt · one removable carrier plate"),
              ("open","Component layout with shell hidden","Top-mounted boards and tied battery · SCD30 on the bottom plate"),
              ("exploded","Simplified assembly","Two case parts + removable Feather frame · eight M2 board screws and two M3 closure screws"),
              ("feather_install","Feather installs through the bottom","Attach two screws on the table, then slide the frame up; the carrier retains it"),
              ("section_front","Cutaway from the front","Material in front of Y = 33 mm removed; battery cradles remain visible"),
              ("section_side","Cutaway from the left","Material left of X = 43 mm removed; sensor body faces the open bottom")]
    for kind,title,subtitle in variants:
        eye=(-1,-1,-.85) if kind=="underside" else (-1,-1,.85)
        rasterize(variant(scene,kind),title,subtitle,RENDERS/(kind+".png"),eye=eye)
    drawings(scene)
    feather_mount_drawing(scene)
    light_sensor_drawing(scene)
    battery_tie_drawing(scene)
    mounting_guide_drawing(scene)
    from mounting import mounting_example
    mounting,_=mounting_example(PARAMS)
    rasterize({**scene,**mounting},'One tie around the body and support',
        'Four corner guides · clear controls and underside · Ø32 mm example pole and small non-slip pad',
        RENDERS/'pole-mount.png',eye=(-1,-1,.65))
    with PdfPages(CAD/"design-review.pdf") as pdf:
        for name in [x[0] for x in variants]+["sections","mounting-drawings"]:
            fig=plt.figure(figsize=(13.5,10.1))
            ax=fig.add_axes([0,0,1,1]);ax.imshow(Image.open(RENDERS/(name+".png")));ax.axis("off")
            pdf.savefig(fig,dpi=160);plt.close(fig)
    print("PDF design-review.pdf",flush=True)
