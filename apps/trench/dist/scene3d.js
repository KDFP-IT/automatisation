import {isPhysicalWell,worldPoint,nodeAngle,normalizeAngle,junctionAngles} from './node-geometry.js';
import {angleMetrics} from './angle-annotations.js';
import {wellGeometry,crossSection,atStation,lerp} from './network-model.js';
import {beddingColor} from './bedding-style.js';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const xyz=(x,y,z)=>[x,y,z];
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const norm=v=>{const m=Math.hypot(...v);return v.map(x=>x/(m||1))};
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const add=(a,b,k=1)=>a.map((v,i)=>v+b[i]*k);
export function cameraTransform(v,{yaw=-35,pitch=30}={}){
 const a=yaw*Math.PI/180,b=pitch*Math.PI/180,u=v[0]*Math.cos(a)-v[1]*Math.sin(a),d=v[0]*Math.sin(a)+v[1]*Math.cos(a);
 return [u,d*Math.sin(b)-v[2]*Math.cos(b),d*Math.cos(b)+v[2]*Math.sin(b)];
}
export const clampCameraZoom=value=>Number.isFinite(value)?Math.max(.5,Math.min(6,value)):1;
export function cameraFrame(bounds,camera={}){
 const low=[0,1,2].map(i=>Math.min(...bounds.map(v=>v[i]))),high=[0,1,2].map(i=>Math.max(...bounds.map(v=>v[i]))),centre=low.map((v,i)=>(v+high[i])/2);
 const horizontal=Math.max(.2,Math.hypot((high[0]-low[0])/2,(high[1]-low[1])/2)),radius=Math.max(.2,Math.hypot(horizontal,(high[2]-low[2])/2));
 const scale=Math.min(745/(2*horizontal),370/(2*radius))*clampCameraZoom(camera.zoom);
 return {scale,centre,project:v=>{const r=cameraTransform(sub(v,centre),camera);return [450+(Number.isFinite(camera.panX)?camera.panX:0)+r[0]*scale,250+(Number.isFinite(camera.panY)?camera.panY:0)+r[1]*scale,r[2]]}};
}
function face(mesh,vertices,fill,options={}){if(vertices.every(v=>v.every(Number.isFinite)))mesh.push({vertices,fill,...options})}
function tube(mesh,a,b,r,wall,color,options={}){
 if(r<=0)return;const axis=norm(sub(b,a)),u=norm(cross(axis,Math.abs(axis[2])>.95?[0,1,0]:[0,0,1])),v=cross(axis,u),n=24;
 const ring=(p,rr)=>Array.from({length:n},(_,i)=>add(add(p,u,rr*Math.cos(i*2*Math.PI/n)),v,rr*Math.sin(i*2*Math.PI/n)));
 const outerA=ring(a,r),outerB=ring(b,r),innerA=ring(a,Math.max(.001,r-wall)),innerB=ring(b,Math.max(.001,r-wall));
 for(let i=0;i<n;i++){const j=(i+1)%n;face(mesh,[outerA[i],outerA[j],outerB[j],outerB[i]],color,{stroke:'none',...options});face(mesh,[outerA[i],outerA[j],innerA[j],innerA[i]],color,{stroke:'none',...options});face(mesh,[outerB[i],outerB[j],innerB[j],innerB[i]],color,{stroke:'none',...options})}
 face(mesh,innerA,options.opacity&&options.opacity<1?'#aebac3':'#344c5c',{opacity:options.opacity??1,stroke:'none'});face(mesh,innerB,options.opacity&&options.opacity<1?'#aebac3':'#344c5c',{opacity:options.opacity??1,stroke:'none'});
}
function soilDefs(p){return p.soils.map((soil,i)=>`<pattern id="soil-${i}" width="${i%2?11:8}" height="${i%2?11:8}" patternUnits="userSpaceOnUse"><rect width="100%" height="100%" fill="${soil.color}"/>${i%3===0?'<path d="M-2 8L8 -2M2 12L12 2" stroke="#4f4438" opacity=".24" stroke-width=".8"/>':i%3===1?'<path d="M0 5H11" stroke="#635942" opacity=".3" stroke-width=".8"/>':'<circle cx="3" cy="3" r="1" fill="#756444" opacity=".35"/>'}</pattern>`).join('')}
function render(p,mesh,bounds,camera,labels=[],annotations=[]){
 if(!bounds.length)return '<text x="450" y="250" text-anchor="middle">Проверьте параметры модели</text>';
 const frame=cameraFrame(bounds,camera),project=frame.project;
 const objects=mesh.map(f=>({...f,points:f.vertices.map(project)})).map(f=>({...f,depth:f.points.reduce((a,b)=>a+b[2],0)/f.points.length})).sort((a,b)=>a.depth-b.depth);
 let html=`<defs><pattern id="orbit-grid" width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".65" fill="#d5dde3"/></pattern>${soilDefs(p)}</defs><rect width="900" height="520" fill="url(#orbit-grid)"/>`;
 html+=objects.map(f=>`<polygon points="${f.points.map(v=>v.slice(0,2).map(n=>n.toFixed(3)).join(',')).join(' ')}" fill="${f.fill}" fill-opacity="${f.opacity??1}" stroke="${f.stroke??'#8095a5'}" stroke-width="${f.strokeWidth??.65}" stroke-linejoin="round" ${f.soil?`data-soil="${esc(f.soil)}"`:''} ${f.action?`data-${f.action.kind}="${esc(f.action.id)}" class="clickable"`:''}/>`).join('');
 const axisEnds=new Map();
 html+=annotations.map(a=>{const points=a.points.map(project);if(a.axis&&a.axis!=='Z'){const first=points[0],last=points.at(-1),dx=last[0]-first[0],dy=last[1]-first[1],length=Math.hypot(dx,dy);if(length>1e-6&&length<85){last[0]=first[0]+dx/length*85;last[1]=first[1]+dy/length*85}}if(a.axis)axisEnds.set(a.axis,points.at(-1));const last=points.at(-1),prev=points.at(-2),angle=Math.atan2(last[1]-prev[1],last[0]-prev[0]),arrow=a.axis?`<path d="M${last[0]-12*Math.cos(angle-.45)} ${last[1]-12*Math.sin(angle-.45)}L${last[0]} ${last[1]}L${last[0]-12*Math.cos(angle+.45)} ${last[1]-12*Math.sin(angle+.45)}" fill="none" stroke="${a.color}" stroke-width="3"/>`:'';return `<g pointer-events="none"><polyline points="${points.map(v=>v.slice(0,2).join(',')).join(' ')}" fill="none" stroke="${a.color||'#c86b32'}" stroke-width="${a.axis?3:2}" ${a.axis?`data-axis="${esc(a.axis)}"`:""} ${a.dashed?'stroke-dasharray="6 4"':''}/>${arrow}</g>`}).join('');
 html+=labels.map(l=>{const q=l.axis&&axisEnds.has(l.axis)?axisEnds.get(l.axis):project(l.at);return `<text x="${q[0]}" y="${q[1]+(l.dy||0)}" text-anchor="middle" class="${l.class||'map-name'}" ${l.axis?`data-axis-label="${esc(l.axis)}"`:""} ${Number.isFinite(l.beta)?`data-beta="${l.beta}"`:""}>${esc(l.text)}</text>`}).join('');
 html+=`<text x="450" y="495" text-anchor="middle" class="axis-note">Камера: поворот ${Math.round(camera.yaw??-35)}° · наклон ${Math.round(camera.pitch??30)}°</text>`;
 return html;
}
export function drawEdgeMesh(p,e,res,camera={}){
 const mesh=[],bounds=[],length=Math.max(7,...e.sections.map(s=>s.width))*1.5,point=(x,z,s)=>xyz(x,s/res.length*length,z);
 for(const section of e.sections){
  const stations=[section.a*res.length,...res.points.filter(v=>v.s>section.a*res.length&&v.s<section.b*res.length).map(v=>v.s),section.b*res.length];
  for(let k=1;k<stations.length;k++){
   const a=crossSection(e,res,section,stations[k-1]),b=crossSection(e,res,section,stations[k]);
   for(const c of [a,b]){bounds.push(point(-section.width/2-c.left*c.depth,c.ground,c.s),point(section.width/2+c.right*c.depth,c.ground,c.s),point(-section.width/2,c.bottom,c.s),point(section.width/2,c.bottom,c.s))}
   if(section.method==='trench'){
    face(mesh,[point(-a.width/2,a.bottom,a.s),point(a.width/2,a.bottom,a.s),point(b.width/2,b.bottom,b.s),point(-b.width/2,b.bottom,b.s)],'#d3dce3',{opacity:.45});
    if(camera.showSoils!==false){
     let previousA=0,previousB=0;
     for(const layer of e.layers){
      const index=p.soils.findIndex(v=>v.id===layer.soil),bottomA=lerp(layer.start,layer.end,a.s/res.length),bottomB=lerp(layer.start,layer.end,b.s/res.length);
      const loA=Math.max(a.bottom,a.ground-bottomA),hiA=Math.min(a.ground,Math.max(a.bottom,a.ground-previousA)),loB=Math.max(b.bottom,b.ground-bottomB),hiB=Math.min(b.ground,Math.max(b.bottom,b.ground-previousB));
      if(hiA>loA||hiB>loB){
       const left=(c,z)=>-c.width/2-c.left*(z-c.bottom),right=(c,z)=>c.width/2+c.right*(z-c.bottom),style={opacity:.8,stroke:'none',soil:layer.soil};
       face(mesh,[point(left(a,loA),loA,a.s),point(left(b,loB),loB,b.s),point(left(b,hiB),hiB,b.s),point(left(a,hiA),hiA,a.s)],`url(#soil-${index})`,style);
       face(mesh,[point(right(a,loA),loA,a.s),point(right(b,loB),loB,b.s),point(right(b,hiB),hiB,b.s),point(right(a,hiA),hiA,a.s)],`url(#soil-${index})`,style);
       for(const [c,lo,hi]of [[a,loA,hiA],[b,loB,hiB]])if(hi>lo&&(c.s===0||c.s===res.length))face(mesh,[point(left(c,lo),lo,c.s),point(right(c,lo),lo,c.s),point(right(c,hi),hi,c.s),point(left(c,hi),hi,c.s)],`url(#soil-${index})`,{...style,opacity:.24});
      }
      previousA=bottomA;previousB=bottomB;
     }
    }else{
     for(const sign of [-1,1]){const mA=sign<0?a.left:a.right,mB=sign<0?b.left:b.right;face(mesh,[point(sign*a.width/2,a.bottom,a.s),point(sign*b.width/2,b.bottom,b.s),point(sign*(b.width/2+mB*b.depth),b.ground,b.s),point(sign*(a.width/2+mA*a.depth),a.ground,a.s)],'#b8c6d1',{opacity:.3})}
    }
    if(section.bedding>0){
     const ring=c=>[point(-c.width/2,c.bottom,c.s),point(c.width/2,c.bottom,c.s),point(c.width/2+c.right*section.bedding,c.bottom+section.bedding,c.s),point(-c.width/2-c.left*section.bedding,c.bottom+section.bedding,c.s)],A=ring(a),B=ring(b),color=beddingColor(section),style={stroke:'#a78650',strokeWidth:.5};
     for(const [i,j]of [[0,1],[1,2],[2,3],[3,0]])face(mesh,[A[i],A[j],B[j],B[i]],color,style);
     if(k===1)face(mesh,A,color,style);if(k===stations.length-1)face(mesh,B,color,style);
    }
   }
   const A=point(0,a.axis,a.s),B=point(0,b.axis,b.s);
   if(section.casing)tube(mesh,A,B,section.casing/2,section.casingWall,'#7e94a4',{opacity:.32});
   tube(mesh,A,B,e.diameter/2,e.pipeWall,section.method==='supports'?'#5a819b':'#fd6017',{action:{kind:'pipe',id:e.id}});
  }
 }
 const metrics=angleMetrics(e,res,camera.ratio),annotations=[],angleLabels=[];
 if(metrics&&metrics.section.method==='trench'){const c=metrics.c,r=Math.min(.5,c.depth*.25);for(const sign of [-1,1]){const alpha=sign<0?metrics.left:metrics.right;if(!Number.isFinite(alpha)||!(r>0))continue;const x=sign*c.width/2,vertices=Array.from({length:21},(_,i)=>{const a=alpha*Math.PI/180*i/20;return point(x+sign*r*Math.cos(a),c.bottom+r*Math.sin(a),metrics.s)});annotations.push({points:vertices},{points:[point(x,c.bottom,metrics.s),point(x+sign*r*1.3,c.bottom,metrics.s)],dashed:true});angleLabels.push({at:point(x+sign*(r+.15),c.bottom+r+.15,metrics.s),text:'α'+(sign<0?'л':'п')+' '+alpha.toLocaleString('ru-RU',{maximumFractionDigits:1})+'°',class:'angle-label'})}}
 if(metrics)angleLabels.push({at:point(0,metrics.c.axis,metrics.s),dy:-25,text:'β '+metrics.beta.toLocaleString('ru-RU',{minimumFractionDigits:2,maximumFractionDigits:2})+'°',class:'angle-label',beta:metrics.beta});
 const start=crossSection(e,res,e.sections[0],0),last=crossSection(e,res,e.sections.at(-1),res.length);
 return render(p,mesh,bounds,camera,[{at:point(0,start.bottom,0),text:res.from.name,dy:28},{at:point(0,last.bottom,res.length),text:res.to.name,dy:28},...angleLabels],annotations);
}
export function drawWellMesh(p,w,camera={},plan=false){
 const g=wellGeometry(w,p),mesh=[],bounds=[],parts=[{z:g.pitBottom,h:w.pad,width:g.baseW+2*w.padMargin,length:g.baseL+2*w.padMargin,shape:'rect',color:'#d9c69e'},{z:g.bottom,h:w.base,width:g.baseW,length:g.baseL,shape:w.shape,color:'#9eafba'},{z:g.floor,h:g.workingHeight,width:g.bodyW,length:g.bodyL,shape:w.shape,color:'#c3ced6'},{z:g.bodyTop-w.slab,h:w.slab,width:g.bodyW,length:g.bodyL,shape:w.shape,color:'#9cabb6'},{z:g.bodyTop,h:g.neckHeight,width:g.neckD,length:g.neckD,shape:'round',color:'#c6d1d9',x:w.neckX,y:w.neckY}];
 for(const part of parts){if(part.h<=0)continue;const ox=part.x||0,oy=part.y||0,n=part.shape==='round'?40:4;
  const footprint=z=>part.shape==='round'?Array.from({length:n},(_,i)=>[ox+part.width/2*Math.cos(i*2*Math.PI/n),oy+part.length/2*Math.sin(i*2*Math.PI/n),z]):[[ox-part.width/2,oy-part.length/2,z],[ox+part.width/2,oy-part.length/2,z],[ox+part.width/2,oy+part.length/2,z],[ox-part.width/2,oy+part.length/2,z]];
  const low=footprint(part.z),high=footprint(part.z+part.h);bounds.push(...low,...high);
  for(let i=0;i<n;i++)face(mesh,[low[i],low[(i+1)%n],high[(i+1)%n],high[i]],part.color,{stroke:part.shape==='round'?'none':'#9eafbb'});
  face(mesh,high,part.color);face(mesh,low,part.color);
 }
 if(camera.showSoils!==false&&!plan){
  let previous=0;for(const layer of w.layers){
   const low=Math.max(g.pitBottom,w.ground-layer.bottom),high=Math.min(w.ground,Math.max(g.pitBottom,w.ground-previous)),index=p.soils.findIndex(s=>s.id===layer.soil);
   if(high>low){
    const ring=z=>{const m=(z-g.pitBottom)*g.m;return [[-g.width/2-m,-g.length/2-m,z],[g.width/2+m,-g.length/2-m,z],[g.width/2+m,g.length/2+m,z],[-g.width/2-m,g.length/2+m,z]]},a=ring(low),b=ring(high);bounds.push(...a,...b);
    for(let i=0;i<4;i++)face(mesh,[a[i],a[(i+1)%4],b[(i+1)%4],b[i]],`url(#soil-${index})`,{opacity:.28,soil:layer.soil,stroke:'#ffffffaa',strokeWidth:1.1});
   }previous=layer.bottom;
  }
 }
 for(const e of p.edges){const end=e.from.well===w.id?e.from:e.to.well===w.id?e.to:null;if(!end)continue;const other=p.wells.find(v=>v.id===(end===e.from?e.to.well:e.from.well)),adjacent=end===e.from?e.waypoints[0]||other:e.waypoints.at(-1)||other,port=w.ports.find(v=>v.id===end.port);if(!adjacent||!port)continue;
  const az=Math.atan2(adjacent.y-w.y,adjacent.x-w.x)-g.rotation*Math.PI/180,r=w.shape==='rect'?Math.min(g.bodyW/2/Math.max(1e-12,Math.abs(Math.cos(az))),g.bodyL/2/Math.max(1e-12,Math.abs(Math.sin(az)))):g.bodyW/2,A=[Math.cos(az)*r,Math.sin(az)*r,port.invert+e.diameter/2],B=[Math.cos(az)*(r+.85),Math.sin(az)*(r+.85),port.invert+e.diameter/2];tube(mesh,A,B,e.diameter/2,e.pipeWall,'#fd6017',{action:{kind:'edge',id:e.id}});bounds.push(A,B);
 }
 const rotate=v=>{const q=worldPoint({x:0,y:0},v[0],v[1],g.rotation);return [q[0],q[1],v[2]]};for(const item of mesh)item.vertices=item.vertices.map(rotate);for(let i=0;i<bounds.length;i++)bounds[i]=rotate(bounds[i]);
 const angles=plan?{annotations:[],labels:[]}:wellPipeAngleAnnotations(p,w,g);bounds.push(...angles.annotations.flatMap(a=>a.points));return render(p,mesh,bounds,plan?{yaw:0,pitch:90,showSoils:false}:camera,[{at:[0,0,g.pitBottom],text:w.name,dy:26},...angles.labels],angles.annotations);
}

export function wellPipeAngleAnnotations(p,w,g){
 const pairs=w.shape==='round'?junctionAngles(p,w):[];if(pairs.length!==1)return {annotations:[],labels:[]};
 const pair=pairs[0],delta=normalizeAngle(pair.b.bearing-pair.a.bearing),r=Math.max(g.bodyW,g.bodyL)*.9,z=w.ground+.3,point=angle=>[r*Math.cos(angle*Math.PI/180),r*Math.sin(angle*Math.PI/180),z],points=Array.from({length:25},(_,i)=>point(pair.a.bearing+delta*i/24));
 return {annotations:[{points:[[0,0,z],points[0]],dashed:true},{points},{points:[[0,0,z],points.at(-1)],dashed:true}],labels:[{at:point(pair.a.bearing+delta/2),text:pair.angle.toFixed(1)+'°',dy:-12,class:'junction-angle-label'}]};
}
