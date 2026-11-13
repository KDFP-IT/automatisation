import {diagnosticKey} from './issue-guidance.js';
import {isPhysicalWell,rectangleVertices,worldPoint,nodeAngle,junctionAngles,normalizeAngle} from './node-geometry.js';
import {sectionSoilLabels} from './section-soil-labels.js';
import {angleMetrics,sectionAngleMarks} from './angle-annotations.js';
import {drawEdgeMesh,drawWellMesh} from './scene3d.js';
import {beddingColor} from './bedding-style.js';
import {wellGeometry,resolveEdge,atStation,sectionAt,crossSection,lerp,degrees} from './network-model.js';
export const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const fmt=(n,d=2)=>Number.isFinite(n)?n.toLocaleString('ru-RU',{minimumFractionDigits:d,maximumFractionDigits:d}):'—';
const points=p=>p.map(a=>a.map(v=>Number.isFinite(v)?v.toFixed(2):0).join(',')).join(' ');
const poly=(p,fill,stroke='#9daab4',attrs='')=>`<polygon points="${points(p)}" fill="${fill}" stroke="${stroke}" stroke-width="1" ${attrs}/>`;
const line=(a,b,color='#a7b1b9',attrs='')=>`<line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}" stroke="${color}" ${attrs}/>`;
const text=(p,s,attrs='')=>`<text x="${p[0]}" y="${p[1]}" text-anchor="middle" ${attrs}>${esc(s)}</text>`;
let planSerial=0;
const defs=`<defs><pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".7" fill="#ced5da"/></pattern><marker id="flow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#fd6017"/></marker></defs><rect width="900" height="520" fill="url(#dots)" opacity=".65"/>`;
function fit(raw,width=900,height=520,padding=85){
 const xs=raw.map(p=>p[0]),ys=raw.map(p=>p[1]),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
 const scale=Math.min((width-2*padding)/Math.max(maxX-minX,1),(height-2*padding)/Math.max(maxY-minY,1));
 return {scale,map:v=>[width/2+(v[0]-(minX+maxX)/2)*scale,height/2+(v[1]-(minY+maxY)/2)*scale],unmap:v=>[(v[0]-width/2)/scale+(minX+maxX)/2,(v[1]-height/2)/scale+(minY+maxY)/2]};
}
export function planObjectFrame(p,selected){
 if(selected.kind==='well'){const w=p.wells.find(v=>v.id===selected.id);if(!w)throw Error('Выберите узел.');if(!isPhysicalWell(w))return fit([[w.x-1,-w.y-1],[w.x+1,-w.y+1]]);const g=wellGeometry(w,p);return fit(rectangleVertices(w,g.topW,g.topL,g.rotation).map(([x,y])=>[x,-y]))}
 const e=p.edges.find(v=>v.id===selected.id);if(!e)throw Error('Выберите участок.');const res=resolveEdge(p,e),margin=Math.max(.5,e.diameter);return fit(res.points.flatMap(v=>[[v.x-margin,-v.y-margin],[v.x+margin,-v.y+margin]]));
}
export function planRegionFrame(polygon){const xs=polygon.map(v=>v[0]),ys=polygon.map(v=>v[1]),pad=Math.max(2,(Math.max(...xs)-Math.min(...xs))/2,(Math.max(...ys)-Math.min(...ys))/2);return fit(polygon.flatMap(([x,y])=>[[x-pad,-y-pad],[x+pad,-y+pad]]))}
export function bearing(res,end){const a=end==='from'?res.points[0]:res.points.at(-1),b=end==='from'?res.points[1]:res.points.at(-2);return (Math.atan2(b.y-a.y,b.x-a.x)*180/Math.PI+360)%360}
export function drawPlan(p,result,selected,zoom=1,frame=null){
 if(!p.wells.length){const f=frame||fit([[-20,-12],[20,12]],900,520,60);return {html:defs+text([450,230],'Добавьте трубу или колодец','class="map-name"')+text([450,265],'Инструмент «Колодец» → щелчок по плану','class="axis-note"'),unmap:v=>{const q=f.unmap([450+(v[0]-450)/zoom,260+(v[1]-260)/zoom]);return[q[0],-q[1]]},frame:f,project:(x,y)=>{const q=f.map([x,-y]);return [450+(q[0]-450)*zoom,260+(q[1]-260)*zoom]}}}
 const raw=p.wells.flatMap(w=>{const g=wellGeometry(w,p);return isPhysicalWell(w)?rectangleVertices(w,g.topW,g.topL,g.rotation).map(([x,y])=>[x,-y]):[[w.x-.5,-w.y-.5],[w.x+.5,-w.y+.5]]});for(const e of p.edges)for(const v of e.waypoints)raw.push([v.x,-v.y]);
 const f=frame||fit(raw);const P=(x,y)=>[450+(f.map([x,-y])[0]-450)*zoom,260+(f.map([x,-y])[1]-260)*zoom];
 const unmap=v=>{const r=f.unmap([450+(v[0]-450)/zoom,260+(v[1]-260)/zoom]);return [r[0],-r[1]]};
 let html=defs;const maskId='joint-outside-pits-'+(++planSerial);const pitContours=p.wells.filter(isPhysicalWell).map(w=>{const g=wellGeometry(w,p);return {w,vertices:rectangleVertices(w,g.topW,g.topL,g.rotation).map(([x,y])=>P(x,y))}});html+='<defs><mask id="'+maskId+'" maskUnits="userSpaceOnUse" x="0" y="0" width="900" height="520"><rect width="900" height="520" fill="white"/>'+pitContours.map(v=>poly(v.vertices,'black','black')).join('')+'</mask></defs>';
 for(const w of p.wells.filter(isPhysicalWell)){const g=wellGeometry(w,p);html+=poly(rectangleVertices(w,g.topW,g.topL,g.rotation).map(([x,y])=>P(x,y)),'#7bb5dd17','#92b0c5','stroke-dasharray="4 4"')}
 for(const e of p.edges){let res;try{res=resolveEdge(p,e)}catch{continue}const r=result.edges[e.id],active=selected?.kind==='edge'&&selected.id===e.id;
  const pts=res.points.map(v=>P(v.x,v.y));html+=`<polyline points="${points(pts)}" fill="none" stroke="${active?'#fd601733':'#a8bac322'}" stroke-width="${active?21:15}" stroke-linejoin="round"/>`;
  for(const s of e.sections){const a=atStation(res,s.a*res.length),b=atStation(res,s.b*res.length),route=[a,...res.points.filter(v=>v.s>a.s&&v.s<b.s),b];html+=`<polyline points="${points(route.map(v=>P(v.x,v.y)))}" fill="none" stroke="${s.method==='supports'?'#7e8f9a':s.casing?'#596a77':'#fd6017'}" stroke-width="${s.casing?9:4}" stroke-linejoin="round" ${s.method==='supports'?'stroke-dasharray="6 4"':''}/>`}
  html+=`<polyline points="${points(pts)}" fill="none" stroke="transparent" stroke-width="23" data-edge="${esc(e.id)}" class="clickable"/>`;
  const mid=atStation(res,res.length*.5),midp=P(mid.x,mid.y),flow=atStation(res,res.length*.61);html+=line(P(mid.x,mid.y),P(flow.x,flow.y),'#fd6017','stroke-width="2" marker-end="url(#flow)" pointer-events="none"');
  html+=text([midp[0],midp[1]-20],`${fmt(res.length)} м · Ø ${fmt(e.diameter*1000,0)}`,'class="map-distance" pointer-events="none"');
  for(const v of e.waypoints){const q=P(v.x,v.y);if(v.autoPort){html+=`<circle cx="${q[0]}" cy="${q[1]}" r="3" class="auto-port-point" pointer-events="none"/>`;continue}html+=`<rect x="${q[0]-4}" y="${q[1]-4}" width="8" height="8" fill="#fff" stroke="#fd6017" transform="rotate(45 ${q[0]} ${q[1]})" data-waypoint="${esc(v.id)}" data-edge="${esc(e.id)}" class="point-drag"/>`}
 }
 for(const w of p.wells){const q=P(w.x,w.y),g=wellGeometry(w,p);if(!isPhysicalWell(w)){html+=`<g data-well="${esc(w.id)}" class="node-drag"><circle cx="${q[0]}" cy="${q[1]}" r="7" fill="#fff" stroke="#597b94" stroke-width="2"/>${text([q[0],q[1]+23],w.name,'class="map-name"')}</g>`;continue}const radius=Math.max(10,g.bodyW*f.scale*zoom/2),active=selected?.kind==='well'&&selected.id===w.id;html+=`<g data-well="${esc(w.id)}" class="node-drag"><circle cx="${q[0]}" cy="${q[1]}" r="${radius+7}" fill="${active?'#fd601722':'#ffffffcc'}"/>`;
  html+=w.shape==='round'?`<circle cx="${q[0]}" cy="${q[1]}" r="${radius}" fill="${active?'#fd6017':'#fff'}" stroke="${active?'#fd6017':'#566c7b'}" stroke-width="2.5"/>`:poly(rectangleVertices(w,Math.max(g.bodyW,20/f.scale/zoom),Math.max(g.bodyL,20/f.scale/zoom),g.rotation).map(([x,y])=>P(x,y)),active?'#fd6017':'#fff','#566c7b','stroke-width="2"');
  html+=`<circle cx="${q[0]}" cy="${q[1]}" r="${radius*.42}" fill="${active?'#fff':'#eef2f4'}" stroke="${active?'#fff':'#566c7b'}"/>`+text([q[0],q[1]+radius+22],w.name,'class="map-name"')+text([q[0],q[1]+radius+38],`Земля ${fmt(w.ground,3)}`,'class="map-elevation"')+'</g>';
 }
 if(selected?.kind==='well'){const w=p.wells.find(w=>w.id===selected.id);if(w&&isPhysicalWell(w)&&w.shape==='round'){const pairs=junctionAngles(p,w);if(pairs.length===1){const pair=pairs[0],centre=P(w.x,w.y),g=wellGeometry(w,p),r=Math.max(44,g.bodyW*f.scale*zoom/2+25),delta=normalizeAngle(pair.b.bearing-pair.a.bearing),start=pair.a.bearing,xy=angle=>[centre[0]+r*Math.cos(angle*Math.PI/180),centre[1]-r*Math.sin(angle*Math.PI/180)],a=xy(start),b=xy(start+delta),m=xy(start+delta/2);html+=`<g class="junction-angle" pointer-events="none"><path d="M${a[0]} ${a[1]} A${r} ${r} 0 0 ${delta>0?0:1} ${b[0]} ${b[1]}" fill="none" stroke="#cc671f" stroke-width="2"/>${text([m[0],m[1]-10],fmt(pair.angle,1)+'°','class="junction-angle-label"')}</g>`}}}
 for(const region of result.jointRegions||[]){if(selected?.kind!=='edge'||![region.objectId,...(region.related||[])].includes(selected.id))continue;if(region.polygon){html+=poly(region.polygon.map(([x,y])=>P(x,y)),'#5caa8d20','#43856d','stroke-width="1.5" mask="url(#'+maskId+')" pointer-events="none"')}}
 const focus=(result.issues||[]).find(v=>selected?.issueFocus===diagnosticKey(v));if(focus?.polygon){
 const ids=[focus.objectId,...(focus.related||[])];for(const e of p.edges.filter(e=>ids.includes(e.id))){const res=result.edges[e.id]?.res;if(!res)continue;for(const section of e.sections.filter(s=>s.method==='trench'))for(let i=1;i<res.points.length;i++){const lo=Math.max(section.a*res.length,res.points[i-1].s),hi=Math.min(section.b*res.length,res.points[i].s);if(hi<=lo)continue;const a=crossSection(e,res,section,lo),b=crossSection(e,res,section,hi),dx=b.x-a.x,dy=b.y-a.y,L=Math.hypot(dx,dy);if(!L)continue;const n=[-dy/L,dx/L],corners=[[a,1,a.width/2+a.left*a.depth],[b,1,b.width/2+b.left*b.depth],[b,-1,b.width/2+b.right*b.depth],[a,-1,a.width/2+a.right*a.depth]].map(([v,sign,r])=>P(v.x+sign*n[0]*r,v.y+sign*n[1]*r));html+=poly(corners,'#f6bc5720','#b68b51','stroke-dasharray="6 4" pointer-events="none"')}}
 html+=poly(focus.polygon.map(([x,y])=>P(x,y)),focus.code==='pit-overlap'?'#ecc46b40':'#ef444444',focus.code==='pit-overlap'?'#bf862d':'#c63c32','stroke-width="3" pointer-events="none"');const q=P(...focus.location);html+=text([q[0],q[1]-15],focus.code==='pit-overlap'?'Общий контур котлованов':'Пересечение траншей','class="conflict-label" pointer-events="none"')}
 const markerKeys=new Set();for(const issue of result.issues||[]){if(issue.severity!=='error'||!issue.location||!issue.location.slice(0,2).every(Number.isFinite))continue;const ids=[issue.objectId,...(issue.related||[])],key=diagnosticKey(issue);if(selected&&!ids.includes(selected.id)&&selected.issueFocus!==key||markerKeys.has(key))continue;markerKeys.add(key);const q=P(issue.location[0],issue.location[1]),markerColor=issue.code==='pit-overlap'?'#bf862d':'#d34f3d';html+=`<g class="error-location-marker" pointer-events="none"><circle cx="${q[0]}" cy="${q[1]}" r="16" fill="#fef2f255" stroke="${markerColor}" stroke-width="2"/><path d="M${q[0]-5} ${q[1]-5}L${q[0]+5} ${q[1]+5}M${q[0]-5} ${q[1]+5}L${q[0]+5} ${q[1]-5}" stroke="${markerColor}" stroke-width="2"/>${selected?.issueFocus===key?text([q[0],q[1]-24],issue.code==='pit-overlap'?'Общий котлован':'Место ошибки','class="conflict-label"'):''}</g>`}
 if(result.jointRegions?.length)html+=text([450,470],'Зелёный — пересечение контуров траншей вне котлованов','class="joint-plan-label" pointer-events="none"');
 html+=text([88,490],'X →  /  Y ↑','class="axis-note"')+text([725,490],'Голубой пунктир — котлованы','class="axis-note"');return {html,unmap,frame:f,project:P};
}
export function drawSection(p,e,res,ratio,showSoils=true){
 const s=res.length*ratio,section=sectionAt(e,res,s),c=crossSection(e,res,section,s);if(!Number.isFinite(c.depth)||c.depth<=0)return defs+text([450,250],'Проверьте параметры сечения');
 const f=fit([[-c.width/2-c.left*c.depth,-c.depth],[c.width/2+c.right*c.depth,0]],900,520,110),P=(x,z)=>f.map([x,-(z-c.bottom)]);
 let html=defs,prev=0;
 const band=(lo,hi,fill,stroke='none')=>{lo=Math.max(c.bottom,lo);hi=Math.min(c.ground,hi);if(hi<=lo)return '';const a=lo-c.bottom,b=hi-c.bottom;return poly([P(-c.width/2-c.left*a,lo),P(c.width/2+c.right*a,lo),P(c.width/2+c.right*b,hi),P(-c.width/2-c.left*b,hi)],fill,stroke)};
 if(showSoils)for(const layer of e.layers){const bottom=lerp(layer.start,layer.end,ratio),soil=p.soils.find(v=>v.id===layer.soil);html+=band(c.ground-bottom,c.ground-prev,(soil?.color||'#ccc')+'dd');prev=bottom}
 html+=band(c.bottom,c.bottom+section.bedding,beddingColor(section),'#9a763f');if(section.around)html+=band(c.bottom+section.bedding,c.axis+c.verticalR,'#ecdcbfbb')+band(c.axis+c.verticalR,c.fillTop,'#f1e4cbbb');
 html+=poly([P(-c.width/2,c.bottom),P(c.width/2,c.bottom),P(c.width/2+c.right*c.depth,c.ground),P(-c.width/2-c.left*c.depth,c.ground)],'none','#8195a3');
 const circle=(r,fill,stroke)=>{const verts=Array.from({length:65},(_,i)=>{const a=i*Math.PI/32;return P(r*Math.cos(a),c.axis+r*Math.sin(a)*Math.sqrt(1+c.grade*c.grade))});return poly(verts,fill,stroke)};
 if(section.casing)html+=circle(section.casing/2,'#a3b0ba99','#596d7c')+circle(section.casing/2-section.casingWall,'#e9e6da','#8597a4');
 html+=circle(e.diameter/2,'#fd6017','#d54e11')+circle(Math.max(.001,e.diameter/2-e.pipeWall),'#485964','#b94512');
 const bot=P(0,c.bottom),top=P(0,c.ground);html+=text([450,440],`b = ${fmt(c.width)} м   ·   B = ${fmt(c.top)} м   ·   H = ${fmt(c.depth)} м`,'class="section-dimension"');html+=text([450,470],section.method==='trench'?`Откосы от горизонтали · αл ${fmt(degrees(c.left),1)}° · αп ${fmt(degrees(c.right),1)}° · Ø ${fmt(e.diameter*1000,0)} мм`:`Труба на опорах · Ø ${fmt(e.diameter*1000,0)} мм`,'class="axis-note"');
 html+=text([125,55],`Сечение ${fmt(s)} м`,'class="map-name"')+text([765,55],`Земля ${fmt(c.ground,3)}`,'class="map-elevation"');
 if(section.method==='trench'&&section.bedding>0){const bed=P(c.width/2,c.bottom+section.bedding/2);html+=line(bed,[660,395],'#9a763f','stroke-width="1.5"')+text([680,382],`${section.beddingMaterial||'ЩПС'} · h ${fmt(section.bedding*1000,0)} мм`,'class="bed-label"');}
 if(showSoils&&section.method==='trench')html+=sectionSoilLabels(p,e,c,ratio,P);
 html+=sectionAngleMarks(angleMetrics(e,res,ratio),P);
 if(section.method==='supports')html+=`<rect x="220" y="200" width="460" height="60" fill="#fffffff0"/>`+text([450,237],'Прокладка на опорах — траншея не рассчитывается','class="map-name"');
 return html;
}
export function drawProfile(p,e,res,showSoils=true,ratio=null){
 const samples=[...new Set([...res.points.map(v=>v.s),...e.sections.flatMap(v=>[v.a*res.length,v.b*res.length]),...Array.from({length:65},(_,i)=>i*res.length/64)])].sort((a,b)=>a-b);
 const cs=samples.map(s=>crossSection(e,res,sectionAt(e,res,s),s)),max=Math.max(...cs.map(c=>c.ground))+ .5,min=Math.min(...cs.map(c=>c.bottom),wellGeometry(res.from).pitBottom,wellGeometry(res.to).pitBottom)-.4;
 const P=(s,z)=>[85+s/res.length*730,395-(z-min)/(max-min)*315];let html=defs;
 for(let z=Math.ceil(min);z<=max;z++){const y=P(0,z)[1];html+=line([70,y],[830,y],'#dce2e6','stroke-dasharray="4 5"')+text([45,y+4],fmt(z,0),'class="axis-note"')}
 let previous=cs.map(c=>c.ground);
 if(showSoils)for(const layer of e.layers){const soil=p.soils.find(v=>v.id===layer.soil),lower=cs.map(c=>Math.max(c.bottom,c.ground-lerp(layer.start,layer.end,c.s/res.length)));html+=poly([...cs.map((c,i)=>P(c.s,previous[i])),...cs.map((c,i)=>P(c.s,lower[i])).reverse()],(soil?.color||'#ccc')+'bb','none');previous=lower}
 for(let i=1;i<cs.length;i++){const a=cs[i-1],b=cs[i],section=sectionAt(e,res,(a.s+b.s)/2);if(section.method==='trench')html+=poly([P(a.s,a.bottom),P(b.s,b.bottom),P(b.s,b.fillTop),P(a.s,a.fillTop)],'#e7d4ad99','none');if(section.method==='trench'&&section.bedding>0)html+=poly([P(a.s,a.bottom),P(b.s,b.bottom),P(b.s,b.bottom+section.bedding),P(a.s,a.bottom+section.bedding)],beddingColor(section),'#aa8953');if(section.casing)html+=line(P(a.s,a.axis),P(b.s,b.axis),'#566d7d',`stroke-width="${Math.max(6,section.casing/(max-min)*315)}" opacity=".6"`)}
 html+=`<polyline points="${points(cs.map(c=>P(c.s,c.ground)))}" fill="none" stroke="#7e9080" stroke-width="2.5"/>`+`<polyline points="${points(cs.map(c=>P(c.s,c.bottom)))}" fill="none" stroke="#879aa8" stroke-dasharray="6 3" stroke-width="1.5"/>`+`<polyline points="${points(cs.map(c=>P(c.s,c.invert+e.diameter/2)))}" fill="none" stroke="#fd6017" stroke-width="${Math.max(3,e.diameter/(max-min)*315)}"/>`;
 for(const [w,s]of [[res.from,0],[res.to,res.length]]){if(!isPhysicalWell(w)){const port=s===0?res.portA:res.portB;html+=`<circle cx="${P(s,port.invert)[0]}" cy="${P(s,port.invert)[1]}" r="5" fill="#fff" stroke="#597b94"/>`+text([P(s,0)[0],430],w.name,'class="map-name"');continue}const g=wellGeometry(w,p),x=P(s,0)[0],yt=P(s,w.ground)[1],yb=P(s,g.bottom)[1];html+=`<rect x="${x-12}" y="${yt}" width="24" height="${yb-yt}" fill="#edf1f3" stroke="#708695" stroke-width="2"/>`+text([x,430],w.name,'class="map-name"');}
 for(const point of res.points.slice(1,-1)){const v=P(point.s,point.ground);html+=line([v[0],v[1]],[v[0],410],'#a1aeb8','stroke-dasharray="3 4"')+text([v[0],445],fmt(point.s)+' м','class="axis-note"')}
 if(Number.isFinite(ratio)){const c=crossSection(e,res,sectionAt(e,res,res.length*ratio),res.length*ratio),q=P(c.s,c.axis);html+=line([q[0],65],[q[0],410],'#bd4b16','stroke-width="2" stroke-dasharray="6 4" pointer-events="none"')+`<circle cx="${q[0]}" cy="${q[1]}" r="7" fill="#fd6017" stroke="#fff" stroke-width="2" pointer-events="none"/>`+text([q[0],45],`${fmt(c.s)} м`,'class="station-marker-label" pointer-events="none"');}
 const inclination=angleMetrics(e,res,ratio);if(inclination){const q=P(inclination.s,inclination.c.axis);html+=text([Math.max(215,Math.min(685,q[0])),q[1]-24],`β ${fmt(inclination.beta)}° · i ${fmt(inclination.perMille)} ‰`,`class="profile-angle-label" data-beta="${inclination.beta}" pointer-events="none"`)}
 html+=text([450,480],`Плановая длина ${fmt(res.length)} м · труба ${fmt(res.actualLength,3)} м · вертикальный масштаб условный`,'class="axis-note"');return html;
}
export function drawEdge3d(p,e,res,camera={}){return drawEdgeMesh(p,e,res,camera)}
export function drawWell(p,w,camera={},plan=false){return drawWellMesh(p,w,camera,plan)}
