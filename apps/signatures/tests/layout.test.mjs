import test from 'node:test';
import assert from 'node:assert/strict';
import {pageLines,inkEvidence,repairCadEncoding} from '../dist/layout.mjs';
import {extractExpected,includeHandwriting,restoreHandwriting} from '../dist/core.mjs';
const rotatedView={width:1000,height:800,scale:1,transform:[0,1,1,0,0,0],convertToPdfPoint:(x,y)=>[y,x]};
const item=(str,x,y,width)=>({str,width,height:10,transform:[0,10,-10,0,y,x]});
test('legacy CAD character map restores entire surnames instead of matching prefixes',()=>{
 assert.equal(repairCadEncoding('ТруǪников ǔарина ǝуȀаджи ǌриǪкова'),'Трубников Ларина Фучаджи Грибкова');
 assert.equal(repairCadEncoding('Latin Ǫ test'),'Latin Ǫ test');
 const rows=pageLines([item('ГИП',463,782,16),item('ТруǪников',520,782,40)],rotatedView,249);
 const [p]=extractExpected(rows);assert.equal(p.surname,'Трубников');assert.equal(p.sources[0].rawText,'ГИП ТруǪников');
});
test('rotated drawing combines adjacent fragments and reads role/name/signature columns',()=>{
 const rows=pageLines([item('ГИП',463,782,16),item('Тру',520,782,12),item('бников',532,782,25)],rotatedView,241);
 const [drawing]=rows.filter(r=>r.drawing);assert.equal(drawing.stampName,'Трубников');assert.equal(drawing.stampRole,'ГИП');assert(drawing.signatureRect);assert(drawing.signatureScreenRect[0]>drawing.screenRect[0]);
 const people=extractExpected(rows);assert.deepEqual(people.map(p=>p.surname),['Трубников']);assert(people[0].sources[0].drawing);
});
test('surname continued on the next text line inside the name cell is reassembled',()=>{
 const rows=pageLines([item('ГИП',463,782,16),item('Тру',520,782,12),item('бников',520,790,25)],rotatedView,250);
 assert.equal(rows.find(r=>r.drawing).stampName,'Трубников');
});
test('Гл surname fragment is recovered across the neighboring cell, not discarded as a role',()=>{
 const rows=pageLines([item('ГИП',463,782,16),item('Гл',563,782,11),item('адков',574,782,24)],rotatedView,241);
 assert.equal(rows.find(r=>r.drawing).stampName,'Гладков');
 const partial=pageLines([item('ГИП',463,782,16),item('Гл',520,782,11)],rotatedView,241);
 const [person]=extractExpected(partial);assert.equal(person.surname,'Гл');assert.equal(includeHandwriting({...person,status:'missing'}).status,'review');
});
test('adjacent role cells do not become a person named Гл',()=>{
 const rows=pageLines([item('Гл.',463,760,12),item('инж.',478,760,20),item('Кокорев',520,760,35)],rotatedView,241);
 const people=extractExpected(rows);assert.deepEqual(people.map(p=>p.surname),['Кокорев']);
});
const image=(w,h)=>new Uint8ClampedArray(w*h*4).fill(255);
const ink=(a,w,x,y)=>{const i=(y*w+x)*4;a[i]=a[i+1]=a[i+2]=0;};
test('blank signature cells and table rules are not signatures',()=>{
 const w=120,h=40,a=image(w,h);assert.equal(inkEvidence(a,w,h).status,'empty');
 for(let x=0;x<w;x++)ink(a,w,x,4);for(let y=0;y<h;y++)ink(a,w,4,y);
 assert.equal(inkEvidence(a,w,h).status,'empty');
});
test('clear ink strokes count as image evidence, sparse strokes require review',()=>{
 const w=120,h=40,a=image(w,h);for(let x=20;x<80;x++)for(let d=0;d<2;d++)ink(a,w,x,15+Math.round(6*Math.sin(x/6))+d);
 assert.equal(inkEvidence(a,w,h).status,'detected');
 const sparse=image(w,h);for(let x=20;x<42;x++)ink(sparse,w,x,15+(x%7));assert.equal(inkEvidence(sparse,w,h).status,'candidate');
});
test('a handwritten signature on one sheet does not cover another sheet',()=>{
 const row={status:'missing',sources:[{page:1,drawing:true,handwriting:{status:'present'}},{page:2,drawing:true,handwriting:{status:'empty'}}]};
 assert.equal(includeHandwriting(row).status,'review');assert.equal(includeHandwriting(row).evidenceType,'partial');
 row.sources[1].handwriting.status='present';assert.equal(includeHandwriting(row).status,'found');
 const candidate={status:'missing',sources:[{page:1,drawing:true,handwriting:{status:'candidate'}}]};assert.equal(includeHandwriting(candidate).status,'review');
 const detected={status:'missing',sources:[{page:1,drawing:true,handwriting:{status:'detected',automatic:true}}]};assert.equal(includeHandwriting(detected).status,'found');
});
test('repeat analysis preserves manual handwriting only for the same source row',()=>{
 const source={page:249,text:'ГИП Трубников',signatureRect:[10,20,30,40],handwriting:{status:'present',manual:true}};
 const previous=[{sources:[source]}],expected=[{sources:[{...source,handwriting:{status:'candidate'}},{...source,text:'Проверил Кокорев',handwriting:{status:'empty'}}]}];
 restoreHandwriting(expected,previous);assert.equal(expected[0].sources[0].handwriting.status,'present');assert.equal(expected[0].sources[1].handwriting.status,'empty');
});
