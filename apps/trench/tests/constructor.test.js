import test from 'node:test';
import assert from 'node:assert/strict';
import {ProjectHistory,addWellAt,connectWells,transformEdge,copyEdgeSoilsToWells,clone} from '../dist/constructor-core.js';
import {seedProject,resolveEdge,validateProject,calculateNetwork} from '../dist/network-model.js';
import {kulkoD13} from '../dist/kulko-example.js';
test('a new well in a custom catalogue has explicit missing geology, never dangling default IDs',()=>{
 const p=kulkoD13(),w=addWellAt(p,40,0);assert.deepEqual(w.layers,[]);assert.equal(w.dataStatus,'preliminary');
 const e=connectWells(p,p.wells[1].id,w.id);assert.deepEqual(e.layers,[]);assert.equal(p.edges.length,2);
 validateProject(p);assert.equal(calculateNetwork(p).valid,false);
 const empty={...p,wells:[],edges:[],soils:[]};const a=addWellAt(empty,0,0),b=addWellAt(empty,20,0);connectWells(empty,a.id,b.id);validateProject(empty);
});
test('history restores a whole graph and results, and invalidates redo after a new command',()=>{
 const p=seedProject(),original=clone(p),h=new ProjectHistory();transformEdge(p,p.edges[0].id,{length:35,bearing:25});
 h.record(original,p,'Геометрия');const changed=clone(p),undo=h.undo();assert.deepEqual(undo,original);assert.deepEqual(calculateNetwork(undo).total,calculateNetwork(original).total);assert.deepEqual(h.redo(),changed);
 const previous=clone(changed);changed.name='Другой';h.record(previous,changed,'Имя');h.undo();h.record(previous,{...previous,name:'Новый'});assert.equal(h.redo(),null);
});
test('geometry preview works on a copy, identifies affected neighbours and preserves fixed profile unless explicitly replaced',()=>{
 const p=seedProject(),before=clone(p),copy=clone(p),e=copy.edges[0],res=resolveEdge(copy,e),fixed=e.waypoints[0].invert;
 const affected=transformEdge(copy,e.id,{length:30,bearing:45});assert.ok(affected.includes(copy.edges[1].name));assert.equal(e.waypoints[0].invert,fixed);assert.deepEqual(p,before);assert.ok(Math.abs(resolveEdge(copy,e).length-30)<1e-8);assert.equal(res.from.x,p.wells[0].x);
 assert.throws(()=>transformEdge(clone(p),p.edges[0].id,{grade:10}),/фиксированные/);
 const adjusted=clone(p);transformEdge(adjusted,adjusted.edges[0].id,{grade:10,replaceFixed:true});assert.equal(adjusted.edges[0].waypoints[0].invert,null);
});
test('zone distances are either explicitly proportional or fixed, with no silent truncation',()=>{
 const p=seedProject(),e=p.edges[0],old=resolveEdge(p,e).length,station=e.sections[0].b*old;
 transformEdge(p,e.id,{length:40,zoneMode:'fixed'});assert.ok(Math.abs(e.sections[0].b*40-station)<1e-9);assert.equal(e.sections.at(-1).b,1);
 const short=seedProject();assert.throws(()=>transformEdge(short,short.edges[0].id,{length:1,zoneMode:'fixed'}),/обрежет/);
});
test('existing free ports are reused, occupied ports rejected, and ground transfer is explicit and reversible',()=>{
 const p=kulkoD13(),w=addWellAt(p,40,0),a=p.wells[1];a.ports.push({id:'free',name:'Свободный',invert:117,bearing:null});const e=connectWells(p,a.id,w.id,{fromPort:'free'});assert.equal(e.from.port,'free');assert.equal(a.ports.filter(v=>v.id==='free').length,1);assert.throws(()=>connectWells(p,a.id,p.wells[0].id,{fromPort:'free'}));
 e.layers=[{soil:p.soils[0].id,start:20,end:20}];copyEdgeSoilsToWells(p,e.id);assert.equal(w.layers[0].soil,p.soils[0].id);assert.equal(w.layers[0].bottom,20);validateProject(p);
});
