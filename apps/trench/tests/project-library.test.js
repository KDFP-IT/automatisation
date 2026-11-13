import test from 'node:test';
import assert from 'node:assert/strict';
import {SchemeSaver,legacyModels} from '../dist/project-library.js';
import {uid,seedProject} from '../dist/network-model.js';
const model=()=>seedProject();
test('saves serialize concurrent edits with the acknowledged revision',async()=>{
 const sent=[];let release;const saver=new SchemeSaver({send:async(path,method,body)=>{sent.push(structuredClone(body));if(sent.length===1)await new Promise(r=>release=r);return {revision:body.revision+1}}});
 const p=model();saver.bind({id:'scheme',revision:1,model:p});saver.queue(p);assert.equal(saver.dirty,false);
 p.name='Edit 1';saver.queue(p);const saving=saver.flush();p.name='Edit 2';saver.queue(p);p.name='Edit 3';saver.queue(p);release();assert.equal(await saving,true);clearTimeout(saver.timer);
 assert.deepEqual(sent.map(v=>[v.revision,v.model.name]),[[1,'Edit 1'],[2,'Edit 3']]);assert.equal(saver.dirty,false);assert.equal(saver.active.revision,3);
});
test('conflict retains local changes and never retries over newer server version',async()=>{
 let calls=0;const saver=new SchemeSaver({send:async()=>{calls++;throw Object.assign(Error('conflict'),{status:409})}});const p=model();saver.bind({id:'s',revision:1,model:p});p.name='Local';saver.queue(p);assert.equal(await saver.flush(),false);assert.equal(saver.dirty,true);assert.throws(()=>saver.bind({id:'other'}));assert.equal(await saver.flush(),false);assert.equal(calls,1);assert.equal(saver.pending.name,'Local');saver.abandon();
});
test('network error can be retried without losing latest edit',async()=>{
 let fail=true;const saver=new SchemeSaver({send:async(_p,_m,b)=>{if(fail)throw Error('offline');return {revision:b.revision+1}}});const p=model();saver.bind({id:'s',revision:1,model:p});p.name='Keep';saver.queue(p);assert.equal(await saver.flush(),false);fail=false;assert.equal(await saver.flush(),true);assert.equal(saver.active.revision,2);assert.equal(saver.dirty,false);
});
test('migration prefers the constructor copy and never modifies browser storage',()=>{
 const old=model(),current=model();current.name='Latest';const map=new Map([['kdfp-network-v3',JSON.stringify(old)],['kdfp-network-v3-constructor-v4',JSON.stringify(current)]]);const before=[...map];const found=legacyModels({getItem:k=>map.get(k)});assert.equal(found.length,1);assert.equal(found[0].model.name,'Latest');assert.deepEqual([...map],before);
});

test('UUID creation works on an HTTP server without crypto.randomUUID',()=>{
 const original=Object.getOwnPropertyDescriptor(globalThis.crypto,'randomUUID');Object.defineProperty(globalThis.crypto,'randomUUID',{value:undefined,configurable:true});
 try{const a=uid(),b=uid();assert.match(a,/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);assert.notEqual(a,b)}finally{if(original)Object.defineProperty(globalThis.crypto,'randomUUID',original);else delete globalThis.crypto.randomUUID}
});
