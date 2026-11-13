import test from 'node:test';
import assert from 'node:assert/strict';
import {seedProject,makeWell,makeEdge,wellGeometry,resolveEdge,atStation,crossSection,integrateEdge,calculateNetwork,validateProject} from '../dist/network-model.js';
const near=(a,b,eps=1e-7)=>assert.ok(Math.abs(a-b)<eps,`${a} != ${b}`);
test('pilot has shared junction, exact profile lengths and a balanced volume',()=>{
 const p=seedProject(),r=calculateNetwork(p);assert.deepEqual(r.errors,[]);assert.equal(p.wells.length,3);assert.equal(p.edges.length,2);assert.equal(p.edges[0].to.well,p.edges[1].to.well);
 near(resolveEdge(p,p.edges[0]).length,21.02);near(resolveEdge(p,p.edges[1]).length,8.75);
 near(r.total.excavation,r.total.pipe+r.total.fill+r.total.backfill);near(Object.values(r.total.soils).reduce((a,b)=>a+b,0),r.total.excavation,.0001);
 for(const e of p.edges)assert.ok(r.edges[e.id].excluded>0,'well pits must be excluded from trench volumes');
 near(r.total.excavation,Object.values(r.wells).reduce((a,b)=>a+b.excavation,0)+Object.values(r.edges).reduce((a,b)=>a+b.excavation,0));
});
test('numerical trench agrees with an independent exact prismatic calculation',()=>{
 const p=seedProject(),e=p.edges[1];e.waypoints=[];const res=resolveEdge(p,e);res.portA.invert=res.portB.invert=97.65;res.from.ground=res.to.ground=100;
 const adjusted=resolveEdge(p,e);const s={...e.sections[0],a:0,b:1,casing:0,width:.9,bedding:.15,left:45,right:45,around:true,protection:.3};e.sections=[s];e.layers=[{soil:'ige1',start:1,end:1},{soil:'ige3',start:10,end:10}];
 const isolated={...p,wells:[]},r=integrateEdge(isolated,e,adjusted,{step:.1,crossSamples:400}),L=adjusted.length;
 near(r.excavation,(.9*2.5+2.5**2)*L,.002);near(r.pipe,Math.PI*.2**2*L,.002);
 near(r.backfill,((.9*2.5+2.5**2)-(.9*.85+.85**2))*L,.005);near(r.excavation,r.pipe+r.fill+r.backfill);
});
test('casing replaces outer pipe envelope once and supports do not excavate',()=>{
 const p=seedProject(),e=p.edges[0],res=resolveEdge(p,e);for(const s of e.sections)s.method='supports';
 const r=integrateEdge(p,e,res);near(r.excavation,0);near(r.pipe,0);near(r.fill,0);
 const q=seedProject(),f=q.edges[1],isolated={...q,wells:[]},config={step:.1,crossSamples:400},r1=integrateEdge(isolated,f,resolveEdge(q,f),config).pipe;f.diameter=.35;const r2=integrateEdge(isolated,f,resolveEdge(q,f),config).pipe;
 assert.ok(r2<r1,'only uncased portions should change, cased envelope stays outer casing');
 for(const s of f.sections)s.casing=.71;
 const a=integrateEdge(isolated,f,resolveEdge(q,f),config).pipe;f.diameter=.3;const b=integrateEdge(isolated,f,resolveEdge(q,f),config).pipe;near(a,b,.005);
});
test('angles and upper-base modes produce the same geometry',()=>{
 const p=seedProject(),e=p.edges[0],res=resolveEdge(p,e),s=e.sections[0],start=crossSection(e,res,s,0);const byWidth={...s,slopeMode:'top',topWidth:start.top};
 for(const station of [0,.1*res.length,s.b*res.length]){const a=crossSection(e,res,s,station),b=crossSection(e,res,byWidth,station);near(a.left,b.left);near(a.top,b.top)}
 const asym={...s,left:60,right:35};const c=crossSection(e,res,asym,0);assert.ok(c.left<c.right);near(c.top,c.width+(c.left+c.right)*c.depth);
});
test('changed endpoint updates slope, interpolation and connected edge without duplicating well',()=>{
 const p=seedProject(),e=p.edges[1],res=resolveEdge(p,e),before=res.portB.invert;res.portB.invert-=.2;const after=resolveEdge(p,e);near(atStation(after,after.length).invert,before-.2);assert.ok(after.actualLength>after.length);assert.equal(p.wells.length,3);
});
test('invalid layer coverage, dimensions, casing and port heights cannot yield valid totals',()=>{
 for(const mutate of [p=>p.edges[0].layers=[{soil:'ige1',start:.1,end:.1}],p=>p.edges[0].sections[0].left=0,p=>p.edges[0].sections[0].casing=.2,p=>p.wells[0].ports[0].invert=100,p=>p.wells[0].neckX=20,p=>p.edges[0].sections[1].a=.99]){
  const p=seedProject();mutate(p);assert.ok(calculateNetwork(p).errors.length);
 }
});
test('overlapping well pits and actual pipe collisions remain blocked',()=>{
 const p=seedProject();p.wells[1].x=p.wells[0].x;p.wells[1].y=p.wells[0].y;assert.ok(calculateNetwork(p).errors.some(s=>s.includes('Пересекаются котлованы')));
 const q=seedProject();q.wells=[makeWell('A',-20,0),makeWell('B',20,0),makeWell('C',0,-20),makeWell('D',0,20)];q.edges=[makeEdge(q,q.wells[0].id,q.wells[1].id),makeEdge(q,q.wells[2].id,q.wells[3].id)];assert.ok(calculateNetwork(q).errors.some(s=>s.includes('наружные габариты')));
});
test('well volume is composed of outer parts; soil splitting matches exact pit volume',()=>{
 const p=seedProject(),w=p.wells[0],g=wellGeometry(w);assert.ok(g.occupied>Math.PI*w.diameter**2/4*w.workingHeight);near(g.excavation,g.occupied+g.pad+g.backfill);
 const r=calculateNetwork(p).wells[w.id];near(Object.values(r.soils).reduce((a,b)=>a+b,0),g.excavation);
});
test('JSON roundtrip preserves geometry, shared IDs and volumes; malformed structures rejected',()=>{
 const p=seedProject(),clone=validateProject(JSON.parse(JSON.stringify(p)));near(calculateNetwork(p).total.excavation,calculateNetwork(clone).total.excavation);
 for(const mutate of [p=>p.version=2,p=>p.wells[0].x=null,p=>p.edges[0].sections[0].a='bad',p=>p.wells[1].id=p.wells[0].id,p=>p.soils[0].color='url(bad)']){const p=seedProject();mutate(p);assert.throws(()=>validateProject(p))}
});
