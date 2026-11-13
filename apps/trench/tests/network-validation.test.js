import test from 'node:test';
import assert from 'node:assert/strict';
import {uid,seedProject,makeWell,makeEdge,makeSection,resolveEdge,crossSection,calculateNetwork,setSlopeMode,validateProject} from '../dist/network-model.js';
import {inspectNetwork,closestSegments} from '../dist/network-checks.js';
import * as geometry from '../dist/network-model.js';
const project=()=>({...seedProject(),wells:[],edges:[]});
function well(p,name,x,y){const w=makeWell(name,x,y,p);Object.assign(w,{ground:10,workingHeight:4,neckHeight:.5,slab:.2});w.layers=[{soil:p.soils[0].id,bottom:20}];p.wells.push(w);return w}
function edge(p,a,b,level=6){const e=makeEdge(p,a.id,b.id);a.ports.at(-1).invert=b.ports.at(-1).invert=level;e.layers=[{soil:p.soils[0].id,start:20,end:20}];p.edges.push(e);return e}
const codes=p=>inspectNetwork(p,geometry).map(v=>v.code);

test('switching slope input preserves section geometry and computed volume; asymmetric conversion is explicit',()=>{
 const p=seedProject(),e=p.edges[0],s=e.sections[0],res=resolveEdge(p,e),before=crossSection(e,res,s,1),volume=calculateNetwork(p).total.excavation;
 setSlopeMode(e,res,s,'top');assert.ok(Math.abs(crossSection(e,res,s,1).top-before.top)<1e-9);assert.ok(Math.abs(calculateNetwork(p).total.excavation-volume)<1e-6);setSlopeMode(e,res,s,'angles');assert.ok(Math.abs(s.left-45)<1e-9);
 s.right=60;const copy=structuredClone(s);assert.throws(()=>setSlopeMode(e,res,s,'top'),/симметричные/);assert.deepEqual(s,copy);
});
test('editing a connected well invalidates its pipe and suppresses row quantities until fixed',()=>{
 const p=seedProject(),w=p.wells[0],e=p.edges[0];w.workingHeight=.1;const r=calculateNetwork(p);assert.equal(r.valid,false);assert.ok(r.wells[w.id].errors.length);assert.ok(r.edges[e.id].errors.length);assert.equal(r.edges[e.id].excavation,undefined);assert.ok(r.issues.some(v=>v.code==='port-height'&&v.kind==='well'&&v.paths.length));
 w.workingHeight=1.8;assert.equal(calculateNetwork(p).valid,true);
});
test('one physical port cannot belong to multiple pipes and dangling references cannot be saved',()=>{
 const p=seedProject(),a=p.edges[0],b=p.edges[1];b.to=structuredClone(a.to);assert.throws(()=>validateProject(p),/подключение/);assert.ok(codes(p).includes('port-reused'));
 b.to.port='missing';assert.throws(()=>validateProject(p),/подключение/);
});
test('two distinct ports still cannot overlap physically at the same well wall',()=>{
 const p=project(),a=well(p,'A',0,0),b=well(p,'B',20,0),c=well(p,'C',20,1);edge(p,a,b);edge(p,a,c);assert.ok(codes(p).includes('port-openings'));
 a.ports[1].invert+=1;assert.ok(!codes(p).includes('port-openings'));
});
test('3D pipe clashes include collinear overlap but not a grade-separated crossing',()=>{
 const p=project(),a=well(p,'A',-10,0),b=well(p,'B',10,0),c=well(p,'C',0,-10),d=well(p,'D',0,10),e=edge(p,a,b),f=edge(p,c,d);assert.ok(codes(p).includes('pipe-clash'));
 for(const w of [c,d])w.ports[0].invert=8;assert.ok(!codes(p).includes('pipe-clash'));
 c.x=-5;c.y=0;d.x=15;d.y=0;for(const w of [c,d])w.ports[0].invert=6;assert.ok(codes(p).includes('pipe-clash'));
});
test('self intersections, reversal and unrelated well penetration are identified',()=>{
 const p=project(),a=well(p,'A',0,0),b=well(p,'B',10,0),e=edge(p,a,b);e.waypoints=[{id:uid(),x:10,y:10,ground:null,invert:null},{id:uid(),x:0,y:10,ground:null,invert:null}];assert.ok(codes(p).includes('pipe-self-clash'));
 e.waypoints=[{id:uid(),x:15,y:0,ground:null,invert:null}];assert.ok(codes(p).includes('route-reversal'));
 e.waypoints=[];well(p,'C',5,0);assert.ok(codes(p).includes('pipe-well-clash'));
});
test('geology must cover a deep middle zone even when both endpoints are covered',()=>{
 const p=project(),a=well(p,'A',0,0),b=well(p,'B',30,0),e=edge(p,a,b);e.sections=[makeSection(0,.4),makeSection(.4,.6),makeSection(.6,1)];e.sections[1].bedding=1;e.layers=[{soil:p.soils[0].id,start:4.5,end:4.5}];const r=calculateNetwork(p);assert.ok(r.issues.some(v=>v.code==='soil-zone-coverage'));assert.equal(r.edges[e.id].excavation,undefined);
});
test('parallel trenches with intersecting soil volumes are blocked outside pits; separate corridors are accepted',()=>{
 const p=project(),a=well(p,'A',0,0),b=well(p,'B',30,0),c=well(p,'C',0,3),d=well(p,'D',30,3);edge(p,a,b);edge(p,c,d);assert.ok(codes(p).includes('trench-overlap'));
 c.y=d.y=20;assert.ok(!codes(p).includes('trench-overlap'));assert.equal(calculateNetwork(p).valid,true);
});
test('reverse/flat grades and geology differences are warnings; no gravity-network assumptions',()=>{
 const p=project(),a=well(p,'A',0,0),b=well(p,'B',30,0),e=edge(p,a,b);b.ports[0].invert+=.1;e.layers[0].end=19;const r=calculateNetwork(p);assert.equal(r.valid,true);assert.ok(r.issues.some(v=>v.code==='rising-pipe'&&v.severity==='warning'));assert.ok(r.issues.some(v=>v.code==='geology-junction'&&v.severity==='warning'));
});
test('closest segment distance handles zero-length, parallel and perpendicular segments',()=>{
 assert.equal(closestSegments([0,0,0],[10,0,0],[2,1,0],[8,1,0]).distance,1);
 assert.equal(closestSegments([0,0,0],[0,0,0],[2,0,0],[2,0,0]).distance,2);
 assert.equal(closestSegments([0,0,0],[10,0,0],[5,1,0],[5,1,0]).distance,1);
 assert.equal(closestSegments([-1,0,0],[1,0,0],[0,-1,3],[0,1,3]).distance,3);
});

test('grade-separated pipes on supports do not trigger an excavation crossing error',()=>{
 const p=project(),a=well(p,'A',-20,0),b=well(p,'B',20,0),c=well(p,'C',0,-20),d=well(p,'D',0,20);edge(p,a,b,6);edge(p,c,d,8);for(const e of p.edges)for(const s of e.sections)s.method='supports';assert.equal(calculateNetwork(p).valid,true);
});

test('rectangular well aperture depends on approach direction rather than the shortest body side',()=>{
 const p=project(),a=well(p,'A',0,0),b=well(p,'B',0,30),e=edge(p,a,b);
 for(const w of [a,b])Object.assign(w,{shape:'rect',width:3,length:1});e.diameter=1.2;
 assert.ok(!codes(p).includes('port-width'));b.x=30;b.y=0;assert.ok(codes(p).includes('port-width'));
});
