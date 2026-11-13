import test from 'node:test';
import assert from 'node:assert/strict';
import {matchPeople,includeHandwriting,extractExpected} from '../dist/core.mjs';
const signer={name:'Трубников Денис Сергеевич',surname:'Трубников',given:'Денис',patronymic:'Сергеевич'};
const text=page=>({page,drawing:false,text:'ГИП Д.С. Трубников'});
const drawing=(page,status)=>({page,drawing:true,text:'ГИП Трубников',handwriting:{status}});
function check(sources,signed=true){const [person]=matchPeople([{display:'Д.С. Трубников',pages:sources.map(s=>s.page),sources}],signed?[signer]:[]);return includeHandwriting(person);}
test('SIG covers every text occurrence, handwriting does not',()=>{
 const row=check([text(2),text(14)]);assert.equal(row.status,'found');assert.deepEqual(row.sigAppliedPages,[2,14]);assert(row.occurrences.every(o=>o.method==='sig'&&o.status==='found'));
 const handOnText={...text(2),handwriting:{status:'present'}};const absent=check([handOnText],false);assert.equal(absent.status,'missing');assert.equal(absent.handwriting.present.length,0);
});
test('a SIG never covers empty, unreadable or uncertain signature cells on drawings',()=>{
 for(const [hand,status] of [['empty','missing'],['absent','missing'],['unchecked','review'],['candidate','review']]){
  const row=check([drawing(249,hand)]);assert.equal(row.status,status,hand);assert.deepEqual(row.sigAppliedPages,[]);assert(row.sigExcludedFromDrawings);assert.equal(row.occurrences[0].method,'handwritten');
 }
});
test('mixed document is partial when text is signed but drawing is blank',()=>{
 const row=check([text(2),text(14),drawing(231,'empty')]);assert.equal(row.status,'review');assert.equal(row.evidenceType,'partial');assert.deepEqual(row.sigAppliedPages,[2,14]);assert.deepEqual(row.occurrences.map(o=>o.status),['found','found','missing']);
});
test('SIG in text and handwritten signature on drawing satisfy both independent requirements',()=>{
 const row=check([text(2),drawing(249,'detected')]);assert.equal(row.status,'found');assert.equal(row.evidenceType,'combined');assert.deepEqual(row.sigAppliedPages,[2]);assert.equal(row.handwriting.present[0].page,249);
});
test('handwriting on a drawing cannot satisfy an unsigned text page',()=>{
 const row=check([text(2),drawing(249,'present')],false);assert.equal(row.status,'review');assert.equal(row.evidenceType,'partial');assert.deepEqual(row.occurrences.map(o=>o.status),['missing','found']);
});
test('drawing-only person can be fully signed without any SIG',()=>{
 const row=check([drawing(249,'present')],false);assert.equal(row.status,'found');assert.equal(row.evidenceType,'handwritten');assert.deepEqual(row.sigAppliedPages,[]);
});
test('other surname mentions on a drawing page also require handwriting',()=>{
 const [person]=extractExpected([{page:249,text:'Главный инженер проекта Д.С. Трубников',drawingPage:true}]);assert(person.sources[0].drawing);
 const [matched]=matchPeople([person],[signer]);assert.equal(includeHandwriting(matched).status,'review');
});
