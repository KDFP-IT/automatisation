import test from 'node:test';
import assert from 'node:assert/strict';
import {calculate,defaults} from '../dist/model.js';
const near=(a,b,e=1e-8)=>assert.ok(Math.abs(a-b)<e,`${a} ≠ ${b}`);
test('photo example: variable depth, rounding sections before volume',()=>{
 const p={...defaults,length:6.79,bottom:1.16,depth:2.45,depthEnd:2.66,depthMode:'variable',objectType:'none',bedding:0};
 const full=calculate(p),rounded=calculate({...p,sectionRounding:'3'});
 assert.deepEqual(full.errors,[]);assert.deepEqual(rounded.errors,[]);
 near(full.top,3.61);near(full.topEnd,3.82);near(full.excavation,42.2993235);near(rounded.excavation,42.29711675);near(rounded.backfill,rounded.excavation);
});
test('linear-depth volume matches independent numerical integration',()=>{
 const p={...defaults,length:19.4,depth:1.3,depthEnd:3.7,depthMode:'variable',slope:.8},r=calculate(p);
 let volume=0;const steps=20000;for(let i=0;i<steps;i++){const h=p.depth+(p.depthEnd-p.depth)*(i+.5)/steps;volume+=(p.bottom*h+p.slope*h*h)*p.length/steps}
 near(r.excavation,volume,1e-6);near(calculate({...p,depth:p.depthEnd,depthEnd:p.depth}).excavation,r.excavation);
});
test('Excel principle: subtract exterior construction volume and all replacement materials once',()=>{
 const r=calculate({...defaults,extraFill:25});assert.deepEqual(r.errors,[]);near(r.fill,r.bed+25);near(r.backfill,r.excavation-r.pipe-r.bed-25);near(r.excavation,r.backfill+r.displaced);
});
test('rectangular object and excavation-only modes',()=>{
 const box=calculate({...defaults,objectType:'box',boxWidth:.4,boxHeight:.5});assert.deepEqual(box.errors,[]);near(box.structure,20);near(box.backfill,box.excavation-20-box.bed);
 const none=calculate({...defaults,objectType:'none',bedding:0,diameter:NaN,count:NaN});assert.deepEqual(none.errors,[]);near(none.backfill,none.excavation);
});
test('shorter end controls clearance, invalid fill blocks result',()=>{
 for(const p of [{depthMode:'variable',depthEnd:.2},{extraFill:1000},{extraFill:-1},{extraFill:NaN},{objectType:'box',boxWidth:2}])assert.ok(calculate({...defaults,...p}).errors.length);
});
