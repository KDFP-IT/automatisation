import test from 'node:test';
import assert from 'node:assert/strict';
import {calculate,defaults} from '../dist/model.js';
test('default geometry and material balance',()=>{const r=calculate(defaults);assert.equal(r.errors.length,0);assert.ok(Math.abs(r.excavation-306)<1e-9);assert.ok(Math.abs(r.bed-8.5)<1e-9);assert.ok(Math.abs(r.pipe-7.793113276310) <1e-8);assert.ok(Math.abs(r.backfill+r.pipe+r.bed-r.excavation)<1e-9)});
test('rectangular trench without bedding',()=>{const r=calculate({...defaults,slope:0,bedding:0});assert.ok(Math.abs(r.excavation-144)<1e-9);assert.equal(r.bed,0);assert.equal(r.top,.8)});
test('width and slope modes give same results',()=>{assert.deepEqual(calculate({...defaults,mode:'width',top:2.6}),calculate(defaults))});
test('reject empty, inverted and vertical pipe overflow',()=>{for(const delta of [{length:NaN},{top:.2,mode:'width'},{diameter:1900},{count:1.5},{bedding:-.1}])assert.ok(calculate({...defaults,...delta}).errors.length)});
test('multiple pipes include wall clearance and gap',()=>{assert.ok(calculate({...defaults,count:3}).errors.length);assert.equal(calculate({...defaults,count:2,bottom:1.4}).errors.length,0)});
test('circle cannot cut a sloping wall even when its bounding width fits at centre',()=>{assert.ok(calculate({...defaults,bottom:.01,depth:3,diameter:1000,slope:1,bedding:0}).errors.length)});
