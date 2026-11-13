import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeCms,extractExpected,matchPeople,parseName,checkDigest,correctExpected} from '../dist/core.mjs';
const dictionary=JSON.parse(fs.readFileSync(new URL('../dist/vendor/names.json',import.meta.url),'utf8'));
test('source lines and page coordinates survive merging and correction',()=>{
 const lines=[{page:2,text:'Директор А.Н. Соболев',rect:[10,20,200,40]},{page:22,text:'Соболев',rect:[30,40,120,60]}];
 const [p]=extractExpected(lines,dictionary);assert.deepEqual(p.pages,[2,22]);assert.equal(p.sources.length,2);
 const corrected=correctExpected(p,'Соболев Андрей Николаевич','Директор');assert.deepEqual(corrected.pages,[2,22]);assert.deepEqual(corrected.sources,p.sources);assert.equal(corrected.sources[0].text,lines[0].text);assert(corrected.corrected);
 assert.throws(()=>correctExpected(p,''));
});
test('job abbreviations cannot be surnames even if in the dictionary',()=>{
 const rows=extractExpected([{page:1,text:'Гл'},{page:1,text:'ГИП Гл. инженер А.Н. Соболев'},{page:1,text:'Гл А.Н.'}],{surname:['гл','соболев'],unambiguous:['гл','соболев'],given:[]});
 assert.deepEqual(rows.map(p=>p.surname),['Соболев']);
});
test('all four people from title and executor list, without headings or street names',()=>{
 const lines=[{page:1,text:'Изм. № Документа Подпись Дата'},{page:2,text:'Технический директор А.Н. Соболев'},{page:2,text:'Главный инженер проекта Д.С. Трубников'},{page:3,text:'Отдел Должность Ф.И.О. Подпись'},{page:3,text:'Организация строительства Инженер Ю.С. Закутаев'},{page:3,text:'Экспертизы и выдачи ПД Начальник отдела Ю.А. Ларина'},{page:3,text:'г. Кемерово, просп. Ленина'}];
 assert.deepEqual(extractExpected(lines,dictionary).map(x=>x.surname),['Соболев','Трубников','Закутаев','Ларина']);
});
test('surname-only outside roles, repeated mention, full name, ё and е',()=>{
 const e=extractExpected([{page:1,text:'Соколов'},{page:2,text:'Соколов'},{page:3,text:'Петров Иван Сергеевич'}],dictionary);
 assert.equal(e.length,2);assert.deepEqual(e[0].pages,[1,2]);assert.equal(e[1].surname,'Петров');
 const [m]=matchPeople([{display:'Семёнов А. Н.'}],[{name:'Семенов Андрей Николаевич'}]);assert.equal(m.status,'found');
});
test('missing signer and ambiguous people with same initials',()=>{
 const signers=[{name:'Иванов Иван Иванович'},{name:'Иванов Игорь Ильич'}];
 const r=matchPeople([{display:'Иванов И. И.'},{display:'Петров П. П.'},{display:'Иванов'}],signers);
 assert.deepEqual(r.map(x=>x.status),['review','missing','review']);
});
test('full names do not match only on initials',()=>{
 const [r]=matchPeople([{display:'Иванов Иван Иванович'}],[{name:'Иванов Игорь Ильич'}]);assert.equal(r.status,'missing');
});
test('malformed CMS fails rather than reporting an unsigned document',()=>{
 for(const bytes of [new Uint8Array(),new Uint8Array([48,130,255,255]),new TextEncoder().encode('not a signature')])assert.throws(()=>decodeCms(bytes));
});
test('SHA digest mismatch and GOST explicitly not verified',async()=>{
 const p=new TextEncoder().encode('document');
 assert.equal((await checkDigest({digestAlgorithm:'2.16.840.1.101.3.4.2.1',digest:'00'},p)).status,'mismatch');
 assert.equal((await checkDigest({digestAlgorithm:'1.2.643.7.1.1.2.2',digest:'00'},p)).status,'unchecked');
});
test('provided files integration (only when explicitly configured)',{skip:!process.env.KDFP_TEST_SIG},()=>{
 const c=decodeCms(fs.readFileSync(process.env.KDFP_TEST_SIG));assert.equal(c.signers.length,2);assert(c.detached);assert.deepEqual(c.signers.map(x=>x.surname),['Соболев','Трубников']);assert(c.signers.every(x=>x.identified));
});
