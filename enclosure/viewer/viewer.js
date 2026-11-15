/* Offline, dependency-free WebGL mesh viewer. Geometry is embedded by build_viewer.py. */
(() => {
'use strict';
const $ = id => document.getElementById(id);
const data = JSON.parse($('model-data').textContent);
const canvas = $('model');
const gl = canvas.getContext('webgl', {antialias:true, alpha:false, preserveDrawingBuffer:true});
if (!gl) { $('error').hidden=false; $('error').textContent='WebGL is unavailable. Enable hardware acceleration in your browser, or open design-review.pdf for the static views.'; return; }
const vertex = `attribute vec3 aPosition; attribute vec3 aNormal;
uniform vec3 uOffset,uTarget,uRight,uUp,uEye; uniform vec2 uHalf;
varying vec3 vNormal,vPosition;
void main(){vec3 p=aPosition+uOffset;vec3 q=p-uTarget;vPosition=p;vNormal=aNormal;
gl_Position=vec4(dot(q,uRight)/uHalf.x,dot(q,uUp)/uHalf.y,-dot(q,uEye)/1000.0,1.0);}`;
const fragment = `precision mediump float; varying vec3 vNormal,vPosition;
uniform vec3 uColor; uniform int uCut; uniform float uCutPosition;
void main(){if(uCut==1 && vPosition.x<uCutPosition)discard;if(uCut==2 && vPosition.y<uCutPosition)discard;
vec3 n=normalize(vNormal);if(!gl_FrontFacing)n=-n;
float light=0.53+0.35*max(0.0,dot(n,normalize(vec3(-0.6,-0.8,1.5))))+0.12*max(0.0,dot(n,normalize(vec3(1.0,0.5,0.3))));
gl_FragColor=vec4(uColor*light,1.0);}`;
function shader(type, source){ const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s; }
let program;
try { program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vertex));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program)); }
catch(e){$('error').hidden=false;$('error').textContent='The 3D renderer could not start: '+e.message;return;}
gl.useProgram(program);gl.enable(gl.DEPTH_TEST);gl.clearColor(245/255,246/255,242/255,1);
const uniforms={};for(const name of ['Offset','Target','Right','Up','Eye','Half','Color','Cut','CutPosition'])uniforms[name]=gl.getUniformLocation(program,'u'+name);
const position=gl.getAttribLocation(program,'aPosition'),normal=gl.getAttribLocation(program,'aNormal');
gl.enableVertexAttribArray(position);gl.enableVertexAttribArray(normal);
const parts=data.parts.map(p=>{
 const raw=atob(p.data),bytes=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);
 p.buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,p.buffer);gl.bufferData(gl.ARRAY_BUFFER,bytes,gl.STATIC_DRAW);
 p.rgb=p.color.match(/\w\w/g).map(c=>parseInt(c,16)/255);p.visible=p.defaultVisible!==false;delete p.data;return p;
});
const selectable=parts.filter(p=>p.group!=='_attached'), byId=Object.fromEntries(parts.map(p=>[p.id,p]));
let motion='explode',explosion=0,yaw=-Math.PI*.73,pitch=.55,target=[46,33,30],halfHeight=72,cut='none',cutPosition=48,highlight=null,framePending=false;
const clamp=(x,lo,hi)=>Math.max(lo,Math.min(hi,x));
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
function axes(){const cp=Math.cos(pitch),sp=Math.sin(pitch),cy=Math.cos(yaw),sy=Math.sin(yaw);return {eye:[cp*cy,cp*sy,sp],right:[-sy,cy,0],up:[-sp*cy,-sp*sy,cp]};}
function offset(p){if(motion==='feather')return [0,0,featherPart(p)?-80*explosion:0];return p.delta.map(x=>x*explosion);}
function featherPart(p){return p.id==='feather'||p.id==='feather_frame'||p.id==='display'||p.id.startsWith('feather-screw');}
function removedForAccess(p){return motion==='feather'&&(p.cable||p.id==='carrier'||p.id.startsWith('scd30')||p.id.startsWith('case-screw'));}
function visible(p){if(p.parent)return visible(byId[p.parent]);return p.visible && !removedForAccess(p) && !(p.cable&&explosion>0);}
function schedule(){if(!framePending){framePending=true;requestAnimationFrame(render);}}
function render(){
 framePending=false;const dpr=Math.min(window.devicePixelRatio||1,2),w=Math.round(canvas.clientWidth*dpr),h=Math.round(canvas.clientHeight*dpr);if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
 gl.viewport(0,0,w,h);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);const a=axes();
 for(const k of ['eye','right','up'])gl.uniform3fv(uniforms[k[0].toUpperCase()+k.slice(1)],a[k]);
 gl.uniform3fv(uniforms.Target,target);gl.uniform2f(uniforms.Half,halfHeight*w/h,halfHeight);gl.uniform1i(uniforms.Cut,cut==='x'?1:cut==='y'?2:0);gl.uniform1f(uniforms.CutPosition,cutPosition);
 for(const p of parts){if(!visible(p))continue;gl.bindBuffer(gl.ARRAY_BUFFER,p.buffer);gl.vertexAttribPointer(position,3,gl.FLOAT,false,24,0);gl.vertexAttribPointer(normal,3,gl.FLOAT,false,24,12);gl.uniform3fv(uniforms.Offset,offset(p));gl.uniform3fv(uniforms.Color,p.id===highlight?p.rgb.map(v=>v*.65+.35):p.rgb);gl.drawArrays(gl.TRIANGLES,0,p.count);}
 $('scale-label').textContent=`View height ${(halfHeight*2).toFixed(0)} mm · ${Math.round(explosion*100)}% ${motion==='feather'?'withdrawn':'exploded'}`;
 canvas.dataset.rendered='true';canvas.dataset.explosion=String(explosion);canvas.dataset.visible=String(selectable.filter(visible).length);
}
function corners(p){const d=offset(p),out=[];for(let mask=0;mask<8;mask++)out.push([0,1,2].map(i=>p.bounds[(mask>>i)&1][i]+d[i]));return out;}
function fit(){const active=parts.filter(visible);if(!active.length){schedule();return;}const a=axes(),pts=active.flatMap(corners);const lo=[0,1,2].map(i=>Math.min(...pts.map(p=>p[i]))),hi=[0,1,2].map(i=>Math.max(...pts.map(p=>p[i])));target=lo.map((v,i)=>(v+hi[i])/2);let mx=0,my=0;for(const p of pts){const q=p.map((v,i)=>v-target[i]);mx=Math.max(mx,Math.abs(dot(q,a.right)));my=Math.max(my,Math.abs(dot(q,a.up)));}halfHeight=Math.max(20,my*1.25,mx*canvas.clientHeight/canvas.clientWidth*1.25);schedule();}
function showInfo(p){$('info').replaceChildren();const strong=document.createElement('strong');strong.textContent=p.label;$('info').append(strong,document.createTextNode(p.note));}
function sync(){for(const p of selectable){p.checkbox.checked=p.visible;p.checkbox.disabled=removedForAccess(p)||(p.cable&&explosion>0);p.row.style.opacity=p.checkbox.disabled?'.45':'1';}$('visible-count').textContent=selectable.filter(visible).length+'/'+selectable.length; schedule();}
const groupOrder=['Printed enclosure','Electronics','Wiring','Fasteners','Mounting example'];
for(const group of groupOrder){const section=document.createElement('details');section.open=group==='Printed enclosure'||group==='Electronics';const members=selectable.filter(p=>p.group===group);const summary=document.createElement('summary');summary.textContent=group;const count=document.createElement('span');count.className='count';count.textContent=String(members.length);summary.append(count);section.append(summary);
 for(const p of members){const label=document.createElement('label');label.className='part';label.title=p.note;const input=document.createElement('input');input.type='checkbox';input.checked=true;input.dataset.part=p.id;input.setAttribute('aria-label',p.label);const swatch=document.createElement('span');swatch.className='swatch';swatch.style.background=p.color;const name=document.createElement('span');name.textContent=p.label;label.append(input,swatch,name);section.append(label);p.checkbox=input;p.row=label;
 input.addEventListener('change',()=>{p.visible=input.checked;showInfo(p);sync();});label.addEventListener('pointerenter',()=>{highlight=p.id;showInfo(p);schedule();});label.addEventListener('pointerleave',()=>{highlight=null;schedule();});input.addEventListener('focus',()=>showInfo(p));
 }$('parts').append(section);
}
function setExplosion(value){const withdrawing=motion==='feather';$('motion-start').textContent=withdrawing?'Installed':'Assembled';$('motion-end').textContent=withdrawing?'Withdrawn':'Separated';$('assemble').textContent=withdrawing?'Install':'Assemble';$('explode-all').textContent=withdrawing?'Withdraw':'Fully explode';$('explode').setAttribute('aria-label',withdrawing?'Feather withdrawal amount':'Explosion amount');explosion=Number(value)/100;$('explode').value=value;$('explode-value').value=value+'%';$('explode-note').textContent=motion==='feather'?'0%: installed. 100%: withdrawn straight down. Carrier and attached SCD30 removed; unplug the battery and QT leads first.':(explosion>0?'Cable guides are hidden while parts are separated.':'');sync();fit();}
$('motion').onchange=()=>{motion=$('motion').value;$('motion-title').textContent=motion==='feather'?'Feather withdrawal':'Explode assembly';setExplosion(motion==='feather'?100:0);};
$('explode').addEventListener('input',e=>setExplosion(e.target.value));$('assemble').onclick=()=>setExplosion(0);$('explode-all').onclick=()=>setExplosion(100);
$('show-all').onclick=()=>{selectable.forEach(p=>p.visible=true);sync();};$('hide-all').onclick=()=>{selectable.forEach(p=>p.visible=false);sync();};
$('inside').onclick=()=>{selectable.forEach(p=>p.visible=p.defaultVisible!==false);byId.shell.visible=false;sync();};
function updateCut(){cut=$('cut').value;$('cut-position').style.display=cut==='none'?'none':'block';$('cut-position').max=cut==='y'?data.size[1]:data.size[0];cutPosition=Number($('cut-position').value);$('cut-note').textContent=cut==='none'?'Explore the complete housing or slice through it.':`${cut.toUpperCase()} = ${cutPosition} mm · uncapped cutaway; see sections.pdf for filled engineering sections.`;schedule();}
$('cut').onchange=()=>{$('cut-position').value=$('cut').value==='y'?33:43;updateCut();};$('cut-position').oninput=updateCut;
for(const btn of document.querySelectorAll('[data-view]'))btn.onclick=()=>{const v=btn.dataset.view;[yaw,pitch]=v==='front'?[-Math.PI/2,0]:v==='left'?[Math.PI,0]:v==='bottom'?[-Math.PI/2,-1.15]:v==='top'?[-Math.PI/2,Math.PI/2-.0001]:[-Math.PI*.73,.55];fit();};
$('fit').onclick=fit;$('reset').onclick=()=>{motion='explode';$('motion').value='explode';$('motion-title').textContent='Explode assembly';selectable.forEach(p=>p.visible=p.defaultVisible!==false);highlight=null;showInfo({label:'Ready to explore',note:'Untick the shell to inspect the electronics, or choose Underside to see the sensor.'});yaw=-Math.PI*.73;pitch=.55;$('cut').value='none';updateCut();setExplosion(0);};
$('tie-access').onclick=()=>{$('reset').click();selectable.forEach(p=>p.visible=p.id==='shell'||p.id.startsWith('tie-'));yaw=-Math.PI/2;pitch=-1.15;showInfo({label:'Thread ties before fitting the battery',note:'Feed each tie through its short front eyelet. The channel behind it is open from below, so the tail can be reached directly. Boards and battery are hidden for access.'});sync();fit();};
$('pole-mount').onclick=()=>{$('reset').click();selectable.forEach(p=>p.visible=true);yaw=-Math.PI*.78;pitch=.35;showInfo({label:'One tie around the body and support',note:'The band follows shallow side grooves below the controls. A small pad improves grip and leaves space behind the vents. Example: Ø32 mm pole; check the actual tie length and grip before hanging the device.'});sync();fit();};
function pan(dx,dy){const a=axes(),factor=2*halfHeight/canvas.clientHeight;target=target.map((v,i)=>v-a.right[i]*dx*factor+a.up[i]*dy*factor);}
let pointers=new Map(),gesture=null;
function snapshot(){const p=[...pointers.values()];return {x:p.reduce((s,v)=>s+v.x,0)/p.length,y:p.reduce((s,v)=>s+v.y,0)/p.length,d:p.length===2?Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y):0,n:p.length};}
canvas.addEventListener('pointerdown',e=>{canvas.setPointerCapture(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});gesture=snapshot();});
canvas.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});const next=snapshot();if(gesture&&next.n===gesture.n){const dx=next.x-gesture.x,dy=next.y-gesture.y;if(next.n>=2){pan(dx,dy);if(gesture.d&&next.d)halfHeight=clamp(halfHeight*gesture.d/next.d,8,700);}else if(e.shiftKey||e.buttons===2)pan(dx,dy);else{yaw-=dx*.008;pitch=clamp(pitch+dy*.008,-Math.PI/2+.01,Math.PI/2-.01);}schedule();}gesture=next;});
function release(e){pointers.delete(e.pointerId);gesture=pointers.size?snapshot():null;}
canvas.addEventListener('pointerup',release);canvas.addEventListener('pointercancel',release);canvas.addEventListener('contextmenu',e=>e.preventDefault());
canvas.addEventListener('wheel',e=>{e.preventDefault();halfHeight=clamp(halfHeight*Math.exp(e.deltaY*.001),8,700);schedule();},{passive:false});
canvas.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','-','0'].includes(e.key)){e.preventDefault();if(e.key==='ArrowLeft')yaw-=.1;if(e.key==='ArrowRight')yaw+=.1;if(e.key==='ArrowUp')pitch=clamp(pitch+.1,-1.56,1.56);if(e.key==='ArrowDown')pitch=clamp(pitch-.1,-1.56,1.56);if(e.key==='+')halfHeight/=1.1;if(e.key==='-')halfHeight*=1.1;if(e.key==='0')fit();schedule();}});
canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();$('error').hidden=false;$('error').textContent='The graphics context was lost. Reload this file to restore the model.';});
new ResizeObserver(()=>schedule()).observe(canvas);
sync();fit();
// Small read-only state surface for reproducible offline browser checks.
window.sensorWorkshop={state:()=>({motion,explosion,cut,cutPosition,target:[...target],yaw,pitch,halfHeight,components:selectable.map(p=>({id:p.id,visible:visible(p),defaultVisible:p.defaultVisible!==false,offset:offset(p),group:p.group,cable:!!p.cable})),version:data.version,glError:gl.getError()})};
})();
