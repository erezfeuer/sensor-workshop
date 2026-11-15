"""Nominal tie routes through the two cradle guides; no flexible-body simulation."""
import numpy as np
import trimesh


def feed_centerline(p):
    front=p['battery_center'][1]-12.5
    top=p['tie_tunnel_z']+p['tie_slot_height']/2
    r=p['tie_turn_radius'];cy=p['tie_turn_start_y'];cz=top-r
    arc=np.array([[cy+r*np.cos(a),cz+r*np.sin(a)] for a in np.linspace(np.pi/2,0,25)])
    return np.vstack([[front-7,top],arc,[cy+r,p['tie_exit_z']-5]])


def installed_centerline(p):
    front=p['battery_center'][1]-12.5
    top=p['tie_tunnel_z']+p['tie_slot_height']/2
    cy,cz=p['battery_center'][1:]
    turn=feed_centerline(p)[1:-1]
    radius=p['tie_turn_start_y']+p['tie_turn_radius']-cy
    lower=np.array([[cy+radius*np.cos(a),cz+radius*np.sin(a)] for a in np.linspace(0,-5*np.pi/6,35)])
    # The front leg stays outside the first guide until below its solid foot.
    raw=np.vstack([[front-.5,top],turn,lower,[front-.5,cz-3]])
    # Round the feed-mouth and lower-front corners without hard ribbon kinks.
    points=[]
    for i,b in enumerate(raw):
        a=raw[(i-1)%len(raw)];c=raw[(i+1)%len(raw)]
        d=min(1.,np.linalg.norm(a-b)/3,np.linalg.norm(c-b)/3)
        start=b+(a-b)/np.linalg.norm(a-b)*d
        end=b+(c-b)/np.linalg.norm(c-b)*d
        for t in np.linspace(0,1,5):points.append((1-t)**2*start+2*(1-t)*t*b+t*t*end)
    return np.array(points)


def ribbon_mesh(x,points,closed=False,width=2.5,thickness=.8):
    points=np.asarray(points,float)
    tangent=np.roll(points,-1,axis=0)-np.roll(points,1,axis=0)
    if not closed:
        tangent[0]=points[1]-points[0];tangent[-1]=points[-1]-points[-2]
    tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    normals=np.c_[-tangent[:,1],tangent[:,0]]
    vertices=[]
    for point,normal in zip(points,normals):
        for dx,dn in [(-width/2,-thickness/2),(width/2,-thickness/2),(width/2,thickness/2),(-width/2,thickness/2)]:
            vertices.append([x+dx,*(point+normal*dn)])
    faces=[]
    for i in range(len(points) if closed else len(points)-1):
        for j in range(4):
            a=i*4+j;b=i*4+(j+1)%4;c=((i+1)%len(points))*4+(j+1)%4;d=((i+1)%len(points))*4+j
            faces.extend([[a,b,c],[a,c,d]])
    if not closed:
        k=(len(points)-1)*4
        faces.extend([[0,2,1],[0,3,2],[k,k+1,k+2],[k,k+2,k+3]])
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces)
    mesh.fix_normals()
    return mesh


def battery_tie_mesh(x,p):
    ribbon=ribbon_mesh(x,installed_centerline(p),closed=True)
    head=trimesh.creation.box(extents=[4.5,4,3])
    head.apply_translation([x,p['battery_center'][1],29.5])
    return trimesh.util.concatenate([ribbon,head])
